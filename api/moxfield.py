"""Parser di decklist testuali in stile Moxfield.

Verra' implementato compito per compito: split righe, pulizia tag
markdown, tolleranza a commenti e quantita' omesse.
"""

import re

# Cattura "[Nome Carta](url)" per tenere solo "Nome Carta".
_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]*\)")
# Cattura una quantita' iniziale, con "x" opzionale: "1 Nome" / "1x Nome".
_QUANTITY_RE = re.compile(r"^(\d+)\s*[xX]?\s+(.+)$")


def parse_decklist(text: str) -> list[tuple[str, int]]:
    """Converte una decklist testuale in coppie (nome carta, quantita').

    Righe vuote o che iniziano con "//" o "#" vengono ignorate. Link in
    stile markdown ("[Nome](url)") vengono ridotti al solo nome. Se la
    quantita' e' omessa si assume 1.
    """
    cards: list[tuple[str, int]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("//") or line.startswith("#"):
            continue

        line = _LINK_RE.sub(r"\1", line).strip()
        if not line:
            continue

        match = _QUANTITY_RE.match(line)
        if match:
            quantity = int(match.group(1))
            name = match.group(2).strip()
        else:
            quantity = 1
            name = line

        if name:
            cards.append((name, quantity))

    return cards
