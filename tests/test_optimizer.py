from core.optimizer import optimize


def _listing(seller_id, price_cents):
    return {
        "price": {"cents": price_cents, "currency": "EUR"},
        "user": {"id": seller_id, "username": f"seller-{seller_id}"},
    }


def test_optimize_groups_sellers_within_threshold_and_splits_beyond_it():
    card_listings = {
        # S1 e' il minimo assoluto -> primo venditore scelto.
        "Card A": [_listing("S1", 100), _listing("S2", 120)],
        # S2 sarebbe il minimo, ma S1 (gia' scelto) e' entro il 5% -> resta su S1.
        "Card B": [_listing("S1", 206), _listing("S2", 200)],
        # S1 sfora ampiamente la soglia rispetto al minimo di S3 -> nuovo venditore.
        "Card C": [_listing("S1", 500), _listing("S3", 300)],
        # S2 sarebbe il minimo, ma S3 (gia' scelto) e' entro il 5% -> resta su S3.
        "Card D": [_listing("S2", 305), _listing("S3", 310)],
    }

    result = optimize(card_listings)

    sellers = result["sellers"]
    assert set(sellers) == {"S1", "S3"}

    s1_cards = {card_name: listing["price"]["cents"] for card_name, listing in sellers["S1"]}
    s3_cards = {card_name: listing["price"]["cents"] for card_name, listing in sellers["S3"]}

    assert s1_cards == {"Card A": 100, "Card B": 206}
    assert s3_cards == {"Card C": 300, "Card D": 310}
    assert result["total_cents"] == 100 + 206 + 300 + 310


def test_optimize_uses_cheapest_listing_per_seller():
    card_listings = {
        "Card A": [_listing("S1", 150), _listing("S1", 100), _listing("S2", 90)],
    }

    result = optimize(card_listings)

    assert result["sellers"] == {"S2": [("Card A", _listing("S2", 90))]}
    assert result["total_cents"] == 90


def test_optimize_empty_input():
    assert optimize({}) == {"sellers": {}, "total_cents": 0}
