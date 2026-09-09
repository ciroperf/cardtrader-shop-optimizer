import json
from unittest.mock import Mock, patch

import pytest
import requests

from api.cardtrader import (
    CardTraderAuthError,
    CardTraderClient,
    CardTraderError,
    build_blueprint_index,
)


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


@patch("api.cardtrader.requests.get")
def test_export_blueprints_returns_json(mock_get, monkeypatch):
    monkeypatch.setenv("CARDTRADER_API_TOKEN", "il-mio-token")
    payload = [{"id": 10, "name": "Lightning Bolt", "expansion_id": 1}]
    mock_get.return_value = Mock(status_code=200, json=lambda: payload)

    client = CardTraderClient()
    blueprints = client.export_blueprints(1)

    assert blueprints == payload
    called_url = mock_get.call_args.args[0]
    assert called_url.endswith("/blueprints/export?expansion_id=1")


def test_build_blueprint_index_groups_by_lowercase_name(tmp_path, monkeypatch):
    monkeypatch.setenv("CARDTRADER_API_TOKEN", "il-mio-token")
    client = CardTraderClient()
    client.get_expansions = Mock(
        return_value=[{"id": 1, "game_id": 1, "name": "Alpha"}]
    )
    client.export_blueprints = Mock(
        return_value=[
            {"id": 100, "name": "Lightning Bolt", "expansion_id": 1},
            {"id": 101, "name": "lightning bolt", "expansion_id": 1},
        ]
    )

    index_path = tmp_path / "blueprints_index.json"
    index = build_blueprint_index(client, path=str(index_path))

    expected = {
        "lightning bolt": [
            {"id": 100, "name": "Lightning Bolt", "expansion_id": 1},
            {"id": 101, "name": "lightning bolt", "expansion_id": 1},
        ]
    }
    assert index == expected
    client.export_blueprints.assert_called_once_with(1)
    assert json.loads(index_path.read_text(encoding="utf-8")) == expected
