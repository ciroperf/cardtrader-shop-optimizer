"""Client per le API v2 di CardTrader (https://api.cardtrader.com/api/v2).

Verra' implementato compito per compito: validazione token (/info),
espansioni, export blueprint, marketplace/products con rate limit.
"""

import json
import os

import requests

BASE_URL = "https://api.cardtrader.com/api/v2"
MAGIC_GAME_ID = 1


class CardTraderError(Exception):
    """Errore generico nella comunicazione con le API di CardTrader."""


class CardTraderAuthError(CardTraderError):
    """Token API mancante o non valido (401)."""


class CardTraderClient:
    """Client per le API v2 di CardTrader."""

    def __init__(self, token: str | None = None, timeout: float = 10.0) -> None:
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
