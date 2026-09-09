import logging
from unittest.mock import patch

from api.cardtrader import CardTraderRejectedError
from cart_manager_screen import checkout


def _listing(product_id, price_cents, language="en", foil=False, condition="Near Mint"):
    return {
        "id": product_id,
        "price": {"cents": price_cents, "currency": "EUR"},
        "user": {"id": "S1", "username": "seller-1"},
        "can_sell_via_hub": True,
        "properties_hash": {
            "mtg_language": language,
            "mtg_foil": foil,
            "condition": condition,
        },
    }


@patch("cart_manager_screen.CardTraderClient.add_to_cart")
def test_checkout_replaces_rejected_listing_with_alternative(
    mock_add_to_cart, monkeypatch, caplog
):
    monkeypatch.setenv("CARDTRADER_API_TOKEN", "il-mio-token")

    failed_listing = _listing(1, 100)
    alternative_listing = _listing(2, 120)

    plan = {
        "sellers": {"S1": [("Lightning Bolt", failed_listing)]},
        "total_cents": 100,
    }
    all_listings = {"Lightning Bolt": [failed_listing, alternative_listing]}

    mock_add_to_cart.side_effect = [CardTraderRejectedError("422"), {"ok": True}]

    with caplog.at_level(logging.INFO):
        result = checkout(plan, {}, all_listings)

    assert result == {"added": [("Lightning Bolt", alternative_listing)], "failed": []}
    assert mock_add_to_cart.call_count == 2
    mock_add_to_cart.assert_any_call(1, 1)
    mock_add_to_cart.assert_any_call(2, 1)
    assert any("sostituito" in record.message for record in caplog.records)


@patch("cart_manager_screen.CardTraderClient.add_to_cart")
def test_checkout_succeeds_without_errors(mock_add_to_cart, monkeypatch):
    monkeypatch.setenv("CARDTRADER_API_TOKEN", "il-mio-token")

    listing = _listing(1, 100)
    plan = {"sellers": {"S1": [("Lightning Bolt", listing)]}, "total_cents": 100}
    all_listings = {"Lightning Bolt": [listing]}

    mock_add_to_cart.return_value = {"ok": True}

    result = checkout(plan, {}, all_listings)

    assert result == {"added": [("Lightning Bolt", listing)], "failed": []}
    mock_add_to_cart.assert_called_once_with(1, 1)


@patch("cart_manager_screen.CardTraderClient.add_to_cart")
def test_checkout_reports_failure_when_no_alternative_exists(
    mock_add_to_cart, monkeypatch, caplog
):
    monkeypatch.setenv("CARDTRADER_API_TOKEN", "il-mio-token")

    listing = _listing(1, 100)
    plan = {"sellers": {"S1": [("Lightning Bolt", listing)]}, "total_cents": 100}
    all_listings = {"Lightning Bolt": [listing]}

    mock_add_to_cart.side_effect = CardTraderRejectedError("422")

    with caplog.at_level(logging.ERROR):
        result = checkout(plan, {}, all_listings)

    assert result == {"added": [], "failed": ["Lightning Bolt"]}
    mock_add_to_cart.assert_called_once_with(1, 1)
    assert any("Nessuna alternativa" in record.message for record in caplog.records)
