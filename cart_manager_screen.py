"""Step carrello: aggiunge al carrello CardTrader le carte del piano
d'acquisto ottimizzato, sostituendo automaticamente i listing rifiutati
dall'API (422) con un'alternativa compatibile.
"""

import logging

from api.cardtrader import CardTraderClient, CardTraderRejectedError

MAX_ATTEMPTS_PER_CARD = 10

logger = logging.getLogger(__name__)


def _properties(listing: dict) -> dict:
    return listing.get("properties_hash", {})


def _find_alternative(
    card_name: str, failed_listing: dict, all_listings: dict, excluded_ids: set
) -> dict | None:
    """Cerca un listing alternativo per ``card_name``, escludendo gli id in
    ``excluded_ids``.

    Prova prima gli alternativi con stessa lingua/condizione/foil del
    listing rifiutato, poi degrada progressivamente il vincolo (foil,
    condizione, infine lingua) finche' non trova un candidato o esaurisce
    i listing disponibili. Tra i candidati di ciascun livello sceglie il
    piu' economico.
    """
    pool = [
        listing
        for listing in all_listings.get(card_name, [])
        if listing.get("id") not in excluded_ids and listing.get("can_sell_via_hub")
    ]
    if not pool:
        return None

    wanted = _properties(failed_listing)
    tiers = [
        lambda listing: _properties(listing) == wanted,
        lambda listing: _properties(listing).get("mtg_language") == wanted.get("mtg_language")
        and _properties(listing).get("mtg_foil") == wanted.get("mtg_foil"),
        lambda listing: _properties(listing).get("mtg_language") == wanted.get("mtg_language"),
        lambda listing: True,
    ]

    for matches in tiers:
        candidates = [listing for listing in pool if matches(listing)]
        if candidates:
            return min(candidates, key=lambda listing: listing["price"]["cents"])
    return None


def checkout(plan: dict, blueprint_index: dict, all_listings: dict) -> dict:
    """Aggiunge al carrello tutte le carte del ``plan`` prodotto da
    ``core.optimizer.optimize``.

    Per ogni carta chiama ``add_to_cart``; se l'API rifiuta il listing
    (422) cerca un'alternativa in ``all_listings`` (stessa lingua,
    condizione e foil del listing rifiutato, poi degradando) escludendo i
    product_id gia' falliti, e riprova fino a ``MAX_ATTEMPTS_PER_CARD``
    volte per carta. ``blueprint_index`` non e' usato per la ricerca (le
    carte del piano sono gia' risolte) ma e' accettato per coerenza con
    gli altri step e per eventuali arricchimenti futuri dei log.

    Restituisce ``{"added": [(card_name, listing), ...], "failed":
    [card_name, ...]}``.
    """
    client = CardTraderClient()
    added: list[tuple[str, dict]] = []
    failed: list[str] = []

    for purchases in plan["sellers"].values():
        for card_name, listing in purchases:
            current_listing = listing
            excluded_ids: set = set()
            succeeded = False

            for attempt in range(1, MAX_ATTEMPTS_PER_CARD + 1):
                logger.info(
                    "Tentativo %d/%d: aggiungo '%s' al carrello (product_id=%s).",
                    attempt,
                    MAX_ATTEMPTS_PER_CARD,
                    card_name,
                    current_listing["id"],
                )
                try:
                    client.add_to_cart(current_listing["id"], 1)
                except CardTraderRejectedError:
                    excluded_ids.add(current_listing["id"])
                    alternative = _find_alternative(
                        card_name, current_listing, all_listings, excluded_ids
                    )
                    if alternative is None:
                        logger.error(
                            "Nessuna alternativa disponibile per '%s' dopo il "
                            "rifiuto del listing %s.",
                            card_name,
                            current_listing["id"],
                        )
                        break
                    logger.warning(
                        "Listing %s rifiutato per '%s': sostituito con %s.",
                        current_listing["id"],
                        card_name,
                        alternative["id"],
                    )
                    current_listing = alternative
                    continue
                else:
                    succeeded = True
                    added.append((card_name, current_listing))
                    break

            if not succeeded:
                logger.error(
                    "Impossibile aggiungere '%s' al carrello dopo %d tentativi.",
                    card_name,
                    MAX_ATTEMPTS_PER_CARD,
                )
                failed.append(card_name)

    return {"added": added, "failed": failed}
