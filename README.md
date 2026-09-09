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
`CARDTRADER_API_TOKEN` e lo usa per validare l'account (`get_info()`)
e recuperare le espansioni Magic (`get_expansions()`).

## Test

```bash
pip install -r requirements.txt
pytest
```

## Screenshot

_(da aggiungere)_
