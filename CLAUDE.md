# CardTrader Deck Optimizer

Trova la combinazione di venditori piu' economica su CardTrader per
comprare una decklist Magic, raggruppando gli acquisti per venditore.

Questo file viene letto a ogni run dell'agente. Tienilo sotto le 40 righe.

## Stack

- Python 3.10+, GUI tkinter + ttkbootstrap (tema darkly)
- requests per le API v2 di CardTrader, rapidfuzz per il fuzzy matching
- Test: `pytest`
- Avvio locale: `python main.py` (richiede `CARDTRADER_API_TOKEN`
  nell'ambiente o in un file `.env` locale, mai committato)

## Regole

1. Mai push su `main`. Branch, PR, stop.
2. Un compito, una PR. Niente refactor non richiesti.
3. Se il compito e' ambiguo: commenta la domanda sull'issue e fermati.
4. Leggi in modo mirato con Grep e Glob. Non aprire `node_modules`, `dist`,
   `build`, `.next`, `bin`, `obj`, `*.lock`, `.venv`.
5. Nessun segreto nel codice, nemmeno negli esempi: il token API si legge
   solo da `CARDTRADER_API_TOKEN`.
6. Nessuna dipendenza nuova senza scriverne il motivo nella PR.
7. Mai chiamare `/marketplace/products` senza rispettare il rate limit di
   10 richieste/secondo (vedi `api/cardtrader.py`).

## Convenzioni

- Codice e identificatori in inglese, commenti in italiano.
- Commit in forma imperativa, una riga.
- Client API in `api/`, logica di dominio (resolver, analyzer, optimizer)
  in `core/`, GUI nei file `*_screen.py` in radice.

## Fatto quando

Una PR e' pronta se: `pytest` passa, il README riflette le novita', e
la PR descrive manualmente il comportamento osservato (screenshot o log).
