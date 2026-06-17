#!/usr/bin/env bash
# Push sicuro anti-race tra bot auto-update e aggiornamenti manuali.
# Invariante: sui file generati vince SEMPRE chi ha PIÙ risultati nello state.
# Così un aggiornamento più vecchio non può mai sovrascrivere uno più fresco,
# a prescindere da chi pusha per primo.
set -e
cd "$(dirname "$0")"
MSG="${1:-auto-update modello $(date -u +'%Y-%m-%d %H:%M UTC')}"

# conta i risultati in un revision-file (0 se assente)
count_results () {  # $1 = git ref ("" = working tree locale)
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
  echo "Push rifiutato: confronto freschezza…"
  git fetch -q origin main
  LOCAL=$(count_results "")
  REMOTE=$(count_results "origin/main")
  echo "  risultati locali=$LOCAL  remoti=$REMOTE"
  if [ "$REMOTE" -gt "$LOCAL" ]; then
    # il remoto è PIÙ fresco: abbandono i miei dati, niente sovrascrittura
    echo "  → il remoto ha più risultati: tengo il remoto, abbandono il mio commit."
    git reset --hard origin/main; exit 0
  else
    # i miei dati sono uguali o più freschi: vincono i MIEI file generati
    echo "  → i miei dati sono ≥ freschi: rebase tenendo i miei file."
    git rebase -X theirs origin/main || { git rebase --abort; git reset --hard origin/main; exit 1; }
  fi
done
echo "✗ push non riuscito dopo i tentativi"; exit 1
