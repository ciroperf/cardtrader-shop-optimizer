"""ShopOptimizer: raggruppa gli acquisti per venditore per minimizzare
il numero di spedizioni a parita' di prezzo.
"""

# Sovrapprezzo massimo tollerato pur di riusare un venditore gia' scelto.
DEFAULT_OVERPRICE_THRESHOLD = 0.05


def optimize(card_listings: dict[str, list[dict]], overprice_threshold: float = DEFAULT_OVERPRICE_THRESHOLD) -> dict:
    """Calcola il piano di acquisto che minimizza il numero di venditori.

    Per ogni carta considera solo il listing piu' economico di ciascun
    venditore. Elabora le carte in ordine di prezzo minimo crescente e,
    per ognuna, preferisce il venditore piu' economico gia' presente nel
    piano se il suo prezzo supera il minimo assoluto di non piu' di
    ``overprice_threshold`` (es. 0.05 = 5%); altrimenti sceglie il
    venditore col prezzo minimo assoluto, anche se nuovo.

    Restituisce ``{"sellers": {seller_id: [(card_name, listing), ...]},
    "total_cents": int}``.
    """
    best_by_seller_per_card: dict[str, dict[int, dict]] = {}
    global_best_per_card: dict[str, dict] = {}

    for card_name, listings in card_listings.items():
        best_by_seller: dict[int, dict] = {}
        for listing in listings:
            seller_id = listing["user"]["id"]
            price = listing["price"]["cents"]
            current = best_by_seller.get(seller_id)
            if current is None or price < current["price"]["cents"]:
                best_by_seller[seller_id] = listing

        best_by_seller_per_card[card_name] = best_by_seller
        global_best_per_card[card_name] = min(
            best_by_seller.values(), key=lambda listing: listing["price"]["cents"]
        )

    processing_order = sorted(
        card_listings, key=lambda name: global_best_per_card[name]["price"]["cents"]
    )

    plan: dict[int, list[tuple[str, dict]]] = {}
    total_cents = 0

    for card_name in processing_order:
        best_by_seller = best_by_seller_per_card[card_name]
        global_best = global_best_per_card[card_name]
        max_acceptable = global_best["price"]["cents"] * (1 + overprice_threshold)

        qualifying = [
            listing
            for seller_id, listing in best_by_seller.items()
            if seller_id in plan and listing["price"]["cents"] <= max_acceptable
        ]

        chosen_listing = (
            min(qualifying, key=lambda listing: listing["price"]["cents"])
            if qualifying
            else global_best
        )

        seller_id = chosen_listing["user"]["id"]
        plan.setdefault(seller_id, []).append((card_name, chosen_listing))
        total_cents += chosen_listing["price"]["cents"]

    return {"sellers": plan, "total_cents": total_cents}
