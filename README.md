# CardTrader Deck Optimizer

Applicazione desktop che, data una decklist (es. copiata da Moxfield),
trova sul marketplace di [CardTrader](https://www.cardtrader.com) la
combinazione di venditori piu' economica per comprare tutte le carte,
raggruppando gli acquisti per abbattere le spese di spedizione.

Per chi gioca a Magic: The Gathering e compra le carte mancanti di un
mazzo su CardTrader invece di prenderle una per una a occhio.

## Stack

- Python 3.10+
- GUI: `tkinter` + `ttkbootstrap` (tema `darkly`)
- HTTP: `requests` verso le API v2 di CardTrader
- Fuzzy matching: `rapidfuzz`
- Test: `pytest`

## Avvio in locale

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export CARDTRADER_API_TOKEN=il-tuo-personal-access-token
python main.py
```

Il token si genera dalla sezione sviluppatori del proprio account
CardTrader e non va mai committato nel repo.

`api/cardtrader.py` espone `CardTraderClient`, che legge il token da
`CARDTRADER_API_TOKEN` e lo usa per validare l'account (`get_info()`),
recuperare le espansioni Magic (`get_expansions()`) ed esportarne i
blueprint (`export_blueprints(expansion_id)`). `build_blueprint_index()`
itera tutte le espansioni Magic e salva un indice locale
`blueprints_index.json` (`{"nome carta minuscolo": [{id, name,
expansion_id}, ...]}`) usato in seguito per il fuzzy matching.

`api/moxfield.py` espone `parse_decklist(text)`, che converte una
decklist testuale incollata dall'utente (es. da Moxfield) in una lista
di coppie `(nome carta, quantita')`, ignorando righe vuote o di
commento (`//`, `#`) e ripulendo i link in stile markdown
(`[Nome](url)` -> `Nome`).

`core/resolver.py` espone `resolve(card_name, blueprint_index)`, che
cerca il nome carta nell'indice locale dei blueprint: prima un match
esatto case-insensitive, poi un fuzzy match (`rapidfuzz`,
`score_cutoff=60`) per gestire differenze di formattazione (es.
`Fire // Ice` vs `Fire/Ice`). Restituisce un `BlueprintInfo` o `None`
se non trova nessun match sopra soglia.

## Test

```bash
pip install -r requirements.txt
pytest
```

## Screenshot

_(da aggiungere)_
