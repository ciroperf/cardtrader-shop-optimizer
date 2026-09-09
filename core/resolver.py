"""Risolve i nomi carta della decklist nei Blueprint di CardTrader.

Match esatto prima, poi rapidfuzz.process.extract con score_cutoff=60.
"""

from dataclasses import dataclass

from rapidfuzz import process


@dataclass
class BlueprintInfo:
    """Blueprint CardTrader (o varianti/edizioni) corrispondenti a un nome carta."""

    name: str
    blueprints: list[dict]


def resolve(card_name: str, blueprint_index: dict) -> BlueprintInfo | None:
    """Risolve un nome carta parsato nel Blueprint CardTrader corrispondente.

    Cerca prima un match esatto case-insensitive tra le chiavi dell'indice,
    poi ricorre al fuzzy matching (rapidfuzz, score_cutoff=60) per gestire
    piccole differenze di formattazione (es. 'Fire // Ice' vs 'Fire/Ice').
    Restituisce None se non trova nessun match sopra soglia.
    """
    lookup = card_name.lower()

    blueprints = blueprint_index.get(lookup)
    if blueprints is not None:
        return BlueprintInfo(name=lookup, blueprints=blueprints)

    match = process.extractOne(lookup, blueprint_index.keys(), score_cutoff=60)
    if match is None:
        return None

    matched_name = match[0]
    return BlueprintInfo(name=matched_name, blueprints=blueprint_index[matched_name])
