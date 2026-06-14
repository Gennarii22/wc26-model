# Mondiale 2026 — Il Modello

Modello probabilistico del Mondiale 2026: 20.000 simulazioni Monte Carlo, tutte
le partite, value bet vs i bookmaker, capocannoniere. Pubblicato gratis, si
aggiorna da solo dopo ogni giornata.

## Struttura
- **`site/`** — sito statico pubblicato da Netlify (`index.html` gate email +
  `dashboard.html` / `betting.html` + dati `*_data.js`).
- **`model/`** — pipeline Python. Input statici in `model/data/`.
- **`.github/workflows/update.yml`** — auto-update schedulato (06:00 UTC).

## Come gira l'auto-update
1. La Action scarica i risultati (ESPN), ri-simula, rigenera i `*_data.js`.
2. Committa i dati nuovi nel repo.
3. Netlify (connesso al repo) ripubblica automaticamente a ogni push.

## Esecuzione manuale (locale)
```bash
cd model
WC_BASE=$(pwd) python update_tournament.py && python simulate.py \
  && python top_scorer.py && python gen_dashboard.py && python gen_betting.py
cp dashboard_data.js betting_data.js ../site/
```
I path sono portabili (env `WC_BASE`/`WC_OUT`/`WC_RAW`, default = cartella script).

## Setup email (gate)
Vedi `site/email_apps_script.gs`: crea un Google Sheet, pubblica lo script come
Web App, incolla l'URL `/exec` in `site/index.html`.

## Deploy
Repo connesso a Netlify · publish dir = `site/` · dominio `mondiale.gpancia.com`.
*Solo a scopo informativo · 18+ · scommettere comporta rischi.*
