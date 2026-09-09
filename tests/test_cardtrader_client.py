from unittest.mock import Mock, patch

import pytest
import requests

from api.cardtrader import CardTraderAuthError, CardTraderClient, CardTraderError


def test_init_reads_token_from_env(monkeypatch):
    monkeypatch.setenv("CARDTRADER_API_TOKEN", "il-mio-token")
    client = CardTraderClient()
    assert client._headers["Authorization"] == "Bearer il-mio-token"


def test_init_without_token_raises(monkeypatch):
    monkeypatch.delenv("CARDTRADER_API_TOKEN", raising=False)
    with pytest.raises(CardTraderAuthError):
        CardTraderClient()


@patch("api.cardtrader.requests.get")
def test_get_info_returns_json(mock_get, monkeypatch):
    monkeypatch.setenv("CARDTRADER_API_TOKEN", "il-mio-token")
    mock_get.return_value = Mock(status_code=200, json=lambda: {"username": "foo"})

    client = CardTraderClient()
    info = client.get_info()

    assert info == {"username": "foo"}
    called_url = mock_get.call_args.args[0]
    assert called_url.endswith("/info")
    assert mock_get.call_args.kwargs["headers"]["Authorization"] == "Bearer il-mio-token"


@patch("api.cardtrader.requests.get")
def test_get_info_raises_on_401(mock_get, monkeypatch):
    monkeypatch.setenv("CARDTRADER_API_TOKEN", "token-non-valido")
    mock_get.return_value = Mock(status_code=401, json=lambda: {})

    client = CardTraderClient()
    with pytest.raises(CardTraderAuthError):
        client.get_info()


@patch("api.cardtrader.requests.get")
def test_get_info_raises_on_timeout(mock_get, monkeypatch):
    monkeypatch.setenv("CARDTRADER_API_TOKEN", "il-mio-token")
    mock_get.side_effect = requests.Timeout()

    client = CardTraderClient()
    with pytest.raises(CardTraderError):
        client.get_info()


@patch("api.cardtrader.requests.get")
def test_get_expansions_filters_magic(mock_get, monkeypatch):
    monkeypatch.setenv("CARDTRADER_API_TOKEN", "il-mio-token")
    payload = [
        {"id": 1, "game_id": 1, "name": "Alpha"},
        {"id": 2, "game_id": 4, "name": "Non-Magic Set"},
        {"id": 3, "game_id": 1, "name": "Beta"},
    ]
    mock_get.return_value = Mock(status_code=200, json=lambda: payload)

    client = CardTraderClient()
    expansions = client.get_expansions()

    assert expansions == [
        {"id": 1, "game_id": 1, "name": "Alpha"},
        {"id": 3, "game_id": 1, "name": "Beta"},
    ]


@patch("api.cardtrader.requests.get")
def test_get_expansions_raises_on_server_error(mock_get, monkeypatch):
    monkeypatch.setenv("CARDTRADER_API_TOKEN", "il-mio-token")
    mock_get.return_value = Mock(status_code=500, json=lambda: {})

    client = CardTraderClient()
    with pytest.raises(CardTraderError):
        client.get_expansions()
