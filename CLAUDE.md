# <NOME PROGETTO>

<Una riga: cosa fa e per chi.>

Questo file viene letto a ogni run dell'agente. Tienilo sotto le 40 righe.

## Stack

- <linguaggio / framework>
- <database o storage, se c'e'>
- Test: <comando>
- Avvio locale: <comando>

## Regole

1. Mai push su `main`. Branch, PR, stop.
2. Un compito, una PR. Niente refactor non richiesti.
3. Se il compito e' ambiguo: commenta la domanda sull'issue e fermati.
4. Leggi in modo mirato con Grep e Glob. Non aprire `node_modules`, `dist`,
   `build`, `.next`, `bin`, `obj`, `*.lock`.
5. Nessun segreto nel codice, nemmeno negli esempi.
6. Nessuna dipendenza nuova senza scriverne il motivo nella PR.

## Convenzioni

- Codice e identificatori in inglese, commenti in italiano.
- Commit in forma imperativa, una riga.
- <convenzione specifica del progetto: struttura cartelle, naming, ecc.>

## Fatto quando

Una PR e' pronta se: i test passano, il README riflette le novita', e
un'immagine o un output di esempio mostra il risultato.
