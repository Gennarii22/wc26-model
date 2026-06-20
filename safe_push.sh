#!/usr/bin/env bash
# Push sicuro anti-race tra bot auto-update e modifiche manuali.
# Due principi separati:
#  1) le MODIFICHE DI CODICE/CONFIG vincono sempre (non vengono mai abbandonate);
#  2) sui FILE-DATI GENERATI vince chi ha PIÙ risultati nello state (dati più freschi).
# Così un refresh più vecchio non sovrascrive uno più fresco, MA una modifica al
# workflow/script non viene mai persa solo perché il bot ha pushato dei dati.
set -e
cd "$(dirname "$0")"
MSG="${1:-auto-update modello $(date -u +'%Y-%m-%d %H:%M UTC')}"

# file-dati rigenerati dalla pipeline (su questi conta la freschezza, non il codice)
DATA_FILES="model/state_2026.json model/team_probs.csv model/match_predictions.csv \
model/data/golden_boot_v2.csv model/data/live_goals.json \
model/dashboard_data.js model/betting_data.js site/dashboard_data.js site/betting_data.js"

count_results () {  # $1 = git ref ("" = working tree)
  if [ -z "$1" ]; then
    python3 -c "import json;print(len(json.load(open('model/state_2026.json'))['results']))" 2>/dev/null || echo 0
  else
    git show "$1:model/state_2026.json" 2>/dev/null | python3 -c "import json,sys;print(len(json.load(sys.stdin)['results']))" 2>/dev/null || echo 0
  fi
}

git add -A
git diff --cached --quiet && { echo "Niente da committare."; exit 0; }
git commit -q -m "$MSG"

for attempt in 1 2 3 4 5; do
  if git push origin main 2>/dev/null; then
    echo "✓ push riuscito (tentativo $attempt)"; exit 0
  fi
  echo "Push rifiutato: riallineo preservando le mie modifiche…"
  git fetch -q origin main
  LOCAL=$(count_results "")
  REMOTE=$(count_results "origin/main")
  echo "  risultati locali=$LOCAL  remoti=$REMOTE"
  # rebase tenendo SEMPRE le mie modifiche sui conflitti (codice e dati locali)
  if ! git rebase -X theirs origin/main; then
    git rebase --abort
    echo "  rebase fallito, riprovo dal remoto preservando le mie modifiche non-dati…"
    git reset --soft origin/main; git commit -q -m "$MSG (re-applied)"
    continue
  fi
  # se il remoto ha dati PIÙ freschi, riprendo SOLO i file-dati dal remoto
  if [ "$REMOTE" -gt "$LOCAL" ]; then
    echo "  → dati remoti più freschi: tengo le mie modifiche di codice, riprendo i dati dal remoto."
    git checkout origin/main -- $DATA_FILES 2>/dev/null || true
    git diff --cached --quiet && git diff --quiet || git commit -aqm "merge dati remoti più freschi (mantengo le modifiche di codice)"
  fi
done
echo "✗ push non riuscito dopo i tentativi"; exit 1
