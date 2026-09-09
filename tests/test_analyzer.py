from core.analyzer import filter_listings


def _listing(price_cents, condition="Near Mint", language="en", foil=False, can_sell=True):
    return {
        "price": {"cents": price_cents, "currency": "EUR"},
        "can_sell_via_hub": can_sell,
        "properties_hash": {
            "condition": condition,
            "mtg_language": language,
            "mtg_foil": foil,
        },
    }


def test_filter_listings_discards_non_hub_listings():
    listings = [_listing(100, can_sell=False), _listing(200)]

    filtered, best = filter_listings(
        listings, language="en", min_condition="Near Mint", foil=False
    )

    assert filtered == [listings[1]]
    assert best == listings[1]


def test_filter_listings_discards_worse_condition():
    listings = [
        _listing(100, condition="Played"),
        _listing(150, condition="Near Mint"),
        _listing(90, condition="Poor"),
    ]

    filtered, best = filter_listings(
        listings, language="en", min_condition="Slightly Played", foil=False
    )

    assert filtered == [listings[1]]
    assert best == listings[1]


def test_filter_listings_discards_wrong_language_and_foil():
    listings = [
        _listing(100, language="it"),
        _listing(120, foil=True),
        _listing(150),
    ]

    filtered, best = filter_listings(
        listings, language="en", min_condition="Near Mint", foil=False
    )

    assert filtered == [listings[2]]
    assert best == listings[2]


def test_filter_listings_picks_cheapest_as_best():
    listings = [_listing(300), _listing(150), _listing(200)]

    filtered, best = filter_listings(
        listings, language="en", min_condition="Near Mint", foil=False
    )

    assert len(filtered) == 3
    assert best == listings[1]


def test_filter_listings_returns_none_when_nothing_matches():
    listings = [_listing(100, can_sell=False)]

    filtered, best = filter_listings(
        listings, language="en", min_condition="Near Mint", foil=False
    )

    assert filtered == []
    assert best is None
