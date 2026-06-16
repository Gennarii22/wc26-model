#!/bin/bash
# ── Mondiale 2026 — aggiornamento completo in locale ──────────────────────
# Lancialo dopo le partite: scarica i risultati (ESPN), aggiorna gli ELO,
# ri-simula il torneo condizionato ai risultati reali, rigenera capocannoniere
# e le due dashboard, copia i dati nel sito. Poi `git push` per pubblicare
# (Netlify ripubblica da solo). Nota: il cloud lo fa già ogni giorno da solo —
# questo serve solo per forzare un aggiornamento o lavorare offline.
set -e
BASE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${PY:-python3}"
cd "$BASE/model"

echo "═══ Aggiornamento Mondiale $(date '+%Y-%m-%d %H:%M') ═══"
"$PY" update_tournament.py
"$PY" simulate.py
"$PY" espn_goals.py        # gol live dei marcatori (ESPN)
"$PY" top_scorer_v2.py     # capocannoniere v2 (rate xG × cammino + rigori + gol live)
"$PY" gen_dashboard.py
"$PY" gen_betting.py
cp dashboard_data.js betting_data.js "$BASE/site/"
# NB: i TASSI (player_rates.csv) si rigenerano a parte con `python3 model/sb_rates.py`
#     (serve la cartella Football BoxScore, solo in locale) — non a ogni aggiornamento.

echo ""
echo "✓ Tutto aggiornato. Lancia 'git push' per pubblicare online."
