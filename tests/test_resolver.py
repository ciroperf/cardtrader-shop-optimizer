from core.resolver import BlueprintInfo, resolve


def _index():
    return {
        "lightning bolt": [
            {"id": 1, "name": "Lightning Bolt", "expansion_id": 10},
        ],
        "fire // ice": [
            {"id": 2, "name": "Fire // Ice", "expansion_id": 11},
        ],
    }


def test_resolve_exact_match_case_insensitive():
    index = _index()

    result = resolve("lightning bolt", index)

    assert result == BlueprintInfo(name="lightning bolt", blueprints=index["lightning bolt"])


def test_resolve_fuzzy_match():
    index = _index()

    result = resolve("Fire/Ice", index)

    assert result == BlueprintInfo(name="fire // ice", blueprints=index["fire // ice"])


def test_resolve_no_match_returns_none():
    index = _index()

    result = resolve("Totally Unrelated Card Name Xyz", index)

    assert result is None
