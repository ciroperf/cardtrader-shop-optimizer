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
`get_marketplace_products(blueprint_id)` recupera i listing di mercato
di un blueprint, rispettando un rate limit di 10 richieste/secondo
(`RateLimiter`, sliding window condivisa tra tutte le istanze del
client).

`core/analyzer.py` espone `filter_listings(listings, language,
min_condition, foil)`, che scarta i listing senza `can_sell_via_hub`,
con lingua/foil diversi da quelli richiesti o con condizione peggiore
di `min_condition` (scala `CONDITION_RANK`, da `Mint` a `Poor`), e
restituisce `(listing_filtrati, best_listing)` col listing piu'
economico tra quelli rimasti.

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

`core/optimizer.py` espone `optimize(card_listings, overprice_threshold=0.05)`,
che calcola il piano di acquisto (greedy): elabora le carte in ordine di
prezzo minimo crescente e per ognuna preferisce il venditore piu'
economico gia' scelto nel piano se il suo prezzo supera il minimo
assoluto di non piu' di `overprice_threshold`, altrimenti sceglie il
venditore col prezzo minimo assoluto. Restituisce `{"sellers":
{seller_id: [(nome_carta, listing), ...]}, "total_cents": int}`.

`main.py` mette in fila i moduli sopra in una GUI a step (tema
`darkly`): (1) incolla la decklist in una textbox, (2) il pulsante
"Risolvi" chiama `parse_decklist` + `resolve` su ogni riga e mostra le
carte non trovate in una lista, (3) un form imposta lingua, condizione
minima e foil, (4) il pulsante "Analizza" recupera i listing di
mercato per le carte risolte, li filtra con `filter_listings` e calcola
il piano con `optimize` in un thread separato (per non bloccare la
UI), mostrando il risultato raggruppato per venditore in una tabella
con il totale. Se `CARDTRADER_API_TOKEN` manca o non e' valido
(verificato con `get_info()` all'avvio), viene mostrato un messaggio
d'errore e la risoluzione resta disabilitata. La gestione del
carrello non e' ancora inclusa.

## Test

```bash
pip install -r requirements.txt
pytest
```

I test di `main.py` istanziano la finestra in modalita' headless
(`Tk().withdraw()`) e vengono saltati automaticamente se non c'e' un
display disponibile (es. CI senza Xvfb). Per eseguirli con un display
virtuale su Linux: `xvfb-run -a pytest`.

## Screenshot

_(da aggiungere)_
