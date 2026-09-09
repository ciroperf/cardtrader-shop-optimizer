"""Client per le API v2 di CardTrader (https://api.cardtrader.com/api/v2).

Verra' implementato compito per compito: validazione token (/info),
espansioni, export blueprint, marketplace/products con rate limit.
"""

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
