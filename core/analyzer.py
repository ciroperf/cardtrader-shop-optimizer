"""Filtra i listing di marketplace/products per lingua, condizione e foil.

Considera solo i listing con can_sell_via_hub e produce la best_listing.
"""

# Scala delle condizioni CardTrader: valori piu' bassi = condizione migliore.
CONDITION_RANK = {
    "Mint": -1,
    "Near Mint": 0,
    "Slightly Played": 1,
    "Moderately Played": 2,
    "Played": 3,
    "Heavily Played": 4,
    "Poor": 5,
}


def filter_listings(
    listings: list[dict], language: str, min_condition: str, foil: bool
) -> tuple[list[dict], dict | None]:
    """Filtra i listing secondo le preferenze utente.

    Scarta i listing senza ``can_sell_via_hub``, quelli con lingua o foil
    diversi da quelli richiesti e quelli con condizione peggiore di
    ``min_condition`` (scala ``CONDITION_RANK``). Restituisce la tupla
    ``(listing_filtrati, best_listing)`` dove ``best_listing`` e' il
    listing con prezzo minore, o ``None`` se nessun listing e' valido.
    """
    max_rank = CONDITION_RANK[min_condition]

    filtered = []
    for listing in listings:
        if not listing.get("can_sell_via_hub"):
            continue

        properties = listing.get("properties_hash", {})
        if properties.get("mtg_language") != language:
            continue
        if bool(properties.get("mtg_foil")) != bool(foil):
            continue
        if CONDITION_RANK.get(properties.get("condition"), max_rank + 1) > max_rank:
            continue

        filtered.append(listing)

    best_listing = min(
        filtered, key=lambda listing: listing["price"]["cents"], default=None
    )
    return filtered, best_listing
