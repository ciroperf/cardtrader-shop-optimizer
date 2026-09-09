"""Client per le API v2 di CardTrader (https://api.cardtrader.com/api/v2).

Verra' implementato compito per compito: validazione token (/info),
espansioni, export blueprint, marketplace/products con rate limit.
"""

import json
import os
import threading
import time
from collections import deque
from pathlib import Path

import requests

BASE_URL = "https://api.cardtrader.com/api/v2"
MAGIC_GAME_ID = 1
MARKETPLACE_PRODUCTS_RATE_LIMIT = 10  # richieste/secondo, imposto da CardTrader
ENV_FILE_PATH = Path(__file__).resolve().parent.parent / ".env"


def _load_dotenv() -> None:
    """Carica le variabili da un file ``.env`` locale (se presente).

    Non sovrascrive variabili gia' impostate nell'ambiente: l'ambiente
    reale ha sempre priorita' sul file.
    """
    try:
        lines = Path(ENV_FILE_PATH).read_text(encoding="utf-8").splitlines()
    except OSError:
        return

    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = value


class RateLimiter:
    """Limita a ``max_calls`` le chiamate concesse in una finestra di ``period`` secondi.

    Sliding window: tiene i timestamp delle chiamate recenti e, se la
    finestra e' piena, dorme il tempo necessario prima di procedere.
    Condivisibile tra thread tramite un ``threading.Lock``.
    """

    def __init__(self, max_calls: int, period: float = 1.0) -> None:
        self._max_calls = max_calls
        self._period = period
        self._lock = threading.Lock()
        self._timestamps: deque[float] = deque()

    def acquire(self) -> None:
        with self._lock:
            self._drop_expired()
            if len(self._timestamps) >= self._max_calls:
                sleep_time = self._period - (time.monotonic() - self._timestamps[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
                self._drop_expired()
            self._timestamps.append(time.monotonic())

    def _drop_expired(self) -> None:
        now = time.monotonic()
        while self._timestamps and now - self._timestamps[0] >= self._period:
            self._timestamps.popleft()


# Condiviso da tutte le istanze di CardTraderClient: il limite e' imposto
# dall'API, non dal singolo client.
_marketplace_rate_limiter = RateLimiter(max_calls=MARKETPLACE_PRODUCTS_RATE_LIMIT)


class CardTraderError(Exception):
    """Errore generico nella comunicazione con le API di CardTrader."""


class CardTraderAuthError(CardTraderError):
    """Token API mancante o non valido (401)."""


class CardTraderRejectedError(CardTraderError):
    """Il listing richiesto non e' piu' disponibile (422)."""


class CardTraderClient:
    """Client per le API v2 di CardTrader."""

    def __init__(self, token: str | None = None, timeout: float = 10.0) -> None:
        _load_dotenv()
        token = token or os.environ.get("CARDTRADER_API_TOKEN")
        if not token:
            raise CardTraderAuthError(
                "CARDTRADER_API_TOKEN non impostato nell'ambiente."
            )
        self._headers = {"Authorization": f"Bearer {token}"}
        self._timeout = timeout

    def _get(self, path: str):
        url = f"{BASE_URL}{path}"
        try:
            response = requests.get(url, headers=self._headers, timeout=self._timeout)
        except requests.Timeout as exc:
            raise CardTraderError(f"Timeout durante la richiesta a {path}.") from exc
        except requests.RequestException as exc:
            raise CardTraderError(
                f"Errore di rete durante la richiesta a {path}."
            ) from exc

        if response.status_code == 401:
            raise CardTraderAuthError("Token API non valido o scaduto (401).")
        if response.status_code >= 400:
            raise CardTraderError(
                f"Richiesta a {path} fallita con status {response.status_code}."
            )
        return response.json()

    def _post(self, path: str, payload: dict):
        url = f"{BASE_URL}{path}"
        try:
            response = requests.post(
                url, headers=self._headers, json=payload, timeout=self._timeout
            )
        except requests.Timeout as exc:
            raise CardTraderError(f"Timeout durante la richiesta a {path}.") from exc
        except requests.RequestException as exc:
            raise CardTraderError(
                f"Errore di rete durante la richiesta a {path}."
            ) from exc

        if response.status_code == 401:
            raise CardTraderAuthError("Token API non valido o scaduto (401).")
        if response.status_code == 422:
            raise CardTraderRejectedError(
                f"Listing non piu' disponibile per la richiesta a {path} (422)."
            )
        if response.status_code >= 400:
            raise CardTraderError(
                f"Richiesta a {path} fallita con status {response.status_code}."
            )
        return response.json()

    def get_info(self) -> dict:
        """Valida il token recuperando le info dell'account (GET /info)."""
        return self._get("/info")

    def get_expansions(self) -> list:
        """Recupera le espansioni Magic (game_id == 1) da GET /expansions."""
        expansions = self._get("/expansions")
        return [e for e in expansions if e.get("game_id") == MAGIC_GAME_ID]

    def export_blueprints(self, expansion_id: int) -> list:
        """Recupera i blueprint di un'espansione (GET /blueprints/export)."""
        return self._get(f"/blueprints/export?expansion_id={expansion_id}")

    def get_marketplace_products(self, blueprint_id: int) -> list:
        """Recupera i listing di mercato di un blueprint (GET /marketplace/products).

        Rispetta il rate limit di CardTrader (10 richieste/secondo) tramite
        ``_marketplace_rate_limiter``, condiviso tra tutte le istanze del
        client. La API risponde con un dizionario ``{blueprint_id: [...]}``:
        qui viene gia' spacchettato nella lista di listing.
        """
        _marketplace_rate_limiter.acquire()
        data = self._get(f"/marketplace/products?blueprint_id={blueprint_id}")
        if isinstance(data, dict):
            return data.get(str(blueprint_id), [])
        return data

    def add_to_cart(self, product_id: int, quantity: int) -> dict:
        """Aggiunge un listing al carrello (POST /cart/add).

        Solleva ``CardTraderRejectedError`` se il listing non e' piu'
        disponibile (422), cosi' il chiamante puo' cercarne un'alternativa.
        """
        return self._post(
            "/cart/add",
            {
                "product_id": product_id,
                "quantity": quantity,
                "via_cardtrader_zero": True,
            },
        )


def build_blueprint_index(
    client: CardTraderClient, path: str = "blueprints_index.json"
) -> dict:
    """Costruisce l'indice locale dei blueprint Magic e lo salva su file.

    Itera le espansioni Magic, recupera i blueprint di ciascuna con
    ``export_blueprints`` e produce un dizionario
    ``{"nome carta minuscolo": [{id, name, expansion_id}, ...]}``.
    """
    index: dict[str, list[dict]] = {}
    for expansion in client.get_expansions():
        expansion_id = expansion["id"]
        for blueprint in client.export_blueprints(expansion_id):
            entry = {
                "id": blueprint["id"],
                "name": blueprint["name"],
                "expansion_id": expansion_id,
            }
            index.setdefault(blueprint["name"].lower(), []).append(entry)

    with open(path, "w", encoding="utf-8") as index_file:
        json.dump(index, index_file, ensure_ascii=False, indent=2)

    return index
