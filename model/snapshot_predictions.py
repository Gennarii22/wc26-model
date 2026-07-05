"""
snapshot_predictions.py — archivio GENUINO delle previsioni pre-partita.

Idea: la previsione "vera" di una partita e' l'ULTIMA in cui era ancora da giocare
(played=False), cioe' subito prima del fischio. Una volta giocata, la si CONGELA e
non la si tocca piu' (mai ricreata coi dati aggiornati). Poi si aggancia il risultato.

Due modi:
  python snapshot_predictions.py            # forward: aggiorna dal betting_data corrente (ogni ciclo)
  python snapshot_predictions.py --backfill # ricostruisce lo storico dalla git history (una tantum)

Scrive predictions_history.json.
"""
import os, json, sys, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))
HIST = os.path.join(BASE, "predictions_history.json")

def load_bd(text):
    return json.loads(text.split("= ", 1)[1].rstrip(";\n"))

def snap(m):
    """estrae la previsione compatta da un match del betting_data."""
    mk = m.get("markets", {}) or {}
    ts = m.get("top_scores") or []
    return {
        "home": m["home"], "away": m["away"], "date": m.get("date"),
        "stage": m.get("stage"), "group": m.get("group"),
        "p1": mk.get("1"), "pX": mk.get("X"), "p2": mk.get("2"),
        "ml": ts[0]["s"] if ts else None, "ml_p": ts[0]["p"] if ts else None,
        "over25": mk.get("OVER 2.5"), "gol": mk.get("GOL"),
        "real": None,
    }

def key(m): return f"{m['home']}|{m['away']}|{m.get('date')}"

def emit(hist):
    """scrive il json canonico + il .js (lista ordinata per data) per il sito."""
    json.dump(hist, open(HIST, "w"), ensure_ascii=False, indent=0)
    lst = sorted(hist.values(), key=lambda v: (v.get("date") or "", v.get("home") or ""), reverse=True)
    with open(os.path.join(BASE, "predictions_history.js"), "w") as f:
        f.write("window.WCH = " + json.dumps(lst, ensure_ascii=False) + ";")
    known = sum(1 for v in hist.values() if v.get("real"))
    print(f"✓ predictions_history — {len(hist)} previsioni pre-partita ({known} con risultato)")

def update_from_bd(hist, bd):
    """regola: pre-partita -> sovrascrivi (e' ancora previsione); giocata -> congela + aggancia risultato."""
    for m in bd.get("matches", []):
        k = key(m)
        if not m.get("played"):
            s = snap(m)
            if k in hist:              # mantieni eventuale real gia' agganciato? no: e' ancora pre-partita
                s["real"] = None
            hist[k] = s
        else:
            if k in hist and hist[k].get("real") is None:
                hist[k]["real"] = m.get("real")     # aggancia risultato, previsione INTATTA
    return hist

def forward():
    bd = load_bd(open(os.path.join(BASE, "betting_data.js")).read())
    hist = json.load(open(HIST)) if os.path.exists(HIST) else {}
    hist = update_from_bd(hist, bd)
    emit(hist)

def backfill():
    os.chdir(BASE)
    hashes = subprocess.run(["git", "log", "--format=%H", "--reverse", "--", "betting_data.js"],
                            capture_output=True, text=True).stdout.split()
    print(f"commit da scorrere: {len(hashes)}")
    hist = {}
    for i, h in enumerate(hashes):
        blob = subprocess.run(["git", "show", f"{h}:model/betting_data.js"],
                              capture_output=True, text=True).stdout
        if not blob.strip():
            blob = subprocess.run(["git", "show", f"{h}:betting_data.js"],
                                  capture_output=True, text=True).stdout
        if not blob.strip():
            continue
        try:
            bd = load_bd(blob)
        except Exception:
            continue
        for m in bd.get("matches", []):
            if not m.get("played"):
                hist[key(m)] = snap(m)          # ultima pre-partita vince (ordine cronologico)
        if (i + 1) % 40 == 0:
            print(f"  ...{i+1}/{len(hashes)}")
    # aggancia i risultati reali dal betting_data corrente
    bd_now = load_bd(open(os.path.join(BASE, "betting_data.js")).read())
    for m in bd_now.get("matches", []):
        k = key(m)
        if k in hist and m.get("played"):
            hist[k]["real"] = m.get("real")
    emit(hist)

if __name__ == "__main__":
    backfill() if "--backfill" in sys.argv else forward()
