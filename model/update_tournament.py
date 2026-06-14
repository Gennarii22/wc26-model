"""
═══════════════════════════════════════════════════════════════════════════
  AGGIORNAMENTO LIVE — scarica i risultati giocati e aggiorna gli ELO
═══════════════════════════════════════════════════════════════════════════

1. Scarica da ESPN tutti i risultati del Mondiale (11 giu → oggi)
2. Li mappa sulle squadre del modello, salva results_2026.csv
3. Aggiorna gli ELO partita per partita (formula ufficiale, K=60, margine gol)
4. Salva state_2026.json (ELO aggiornati + risultati noti)
   → simulate.py li usa per CONDIZIONARE le simulazioni ai risultati reali

Fallback manuale: se ESPN non risponde, scrivi i risultati in
results_manual.csv (home,away,home_score,away_score) e rilancia.

Uso:  python update_tournament.py
"""
import os
import warnings; warnings.filterwarnings("ignore")
import json, os, datetime
import urllib.request
import pandas as pd
import numpy as np

BASE = os.environ.get("WC_BASE") or os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("WC_OUT") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
START = datetime.date(2026, 6, 11)

# nomi ESPN → nomi modello
ALIAS = {"Czechia": "Czech Republic", "USA": "United States", "Türkiye": "Turkey",
         "Cabo Verde": "Cape Verde", "Congo DR": "DR Congo", "Côte d'Ivoire": "Ivory Coast",
         "Curacao": "Curaçao", "Bosnia-Herzegovina": "Bosnia and Herzegovina",
         "Republic of Ireland": "Ireland", "Korea Republic": "South Korea"}

teams = pd.read_csv(f"{OUT}/worldcup_teams.csv")
t26 = teams[teams.year == 2026]
VALID = set(t26.team_name)
ELO0 = dict(zip(t26.team_name, t26.elo_pre_tournament))

def canon(n):
    n = ALIAS.get(n, n)
    if n in VALID: return n
    # fuzzy leggero
    import difflib
    m = difflib.get_close_matches(n, list(VALID), n=1, cutoff=0.8)
    return m[0] if m else None

def fetch_espn():
    rows = []
    today = datetime.date.today()
    d = START
    while d <= today:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates={d.strftime('%Y%m%d')}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            data = json.load(urllib.request.urlopen(req, timeout=20))
            for e in data.get("events", []):
                comp = e["competitions"][0]
                status = comp["status"]["type"]["name"]
                if status not in ("STATUS_FULL_TIME", "STATUS_FINAL", "STATUS_FINAL_PEN", "STATUS_FINAL_AET"):
                    continue
                cmap = {c["homeAway"]: c for c in comp["competitors"]}
                h = canon(cmap["home"]["team"]["displayName"])
                a = canon(cmap["away"]["team"]["displayName"])
                if not h or not a:
                    print(f"  ⚠ nomi non mappati: {cmap['home']['team']['displayName']} / {cmap['away']['team']['displayName']}")
                    continue
                hs, as_ = int(cmap["home"]["score"]), int(cmap["away"]["score"])
                # rigori (per i KO)
                pen_h = cmap["home"].get("shootoutScore"); pen_a = cmap["away"].get("shootoutScore")
                rows.append({"date": str(d), "home": h, "away": a,
                             "home_score": hs, "away_score": as_,
                             "pen_home": pen_h, "pen_away": pen_a,
                             "status": status})
        except Exception as ex:
            print(f"  ⚠ ESPN {d}: {ex}")
        d += datetime.timedelta(days=1)
    return pd.DataFrame(rows)

print("Scarico i risultati da ESPN…")
res = fetch_espn()

# fallback/integrazione manuale
man_path = f"{BASE}/results_manual.csv"
if os.path.exists(man_path):
    man = pd.read_csv(man_path)
    man["home"] = man.home.map(lambda x: canon(x) or x)
    man["away"] = man.away.map(lambda x: canon(x) or x)
    if "status" not in man: man["status"] = "MANUAL"
    res = pd.concat([res, man], ignore_index=True).drop_duplicates(subset=["home","away"], keep="last")

if res.empty:
    res = pd.DataFrame(columns=["date","home","away","home_score","away_score","pen_home","pen_away","status"])
print(f"Risultati acquisiti: {len(res)}")
if len(res):
    for _, r in res.iterrows():
        pen = f" (rig. {r.pen_home}-{r.pen_away})" if pd.notna(r.get("pen_home")) and r.get("pen_home") is not None else ""
        print(f"  {r.date}  {r.home} {r.home_score}-{r.away_score} {r.away}{pen}")
res.to_csv(f"{BASE}/results_2026.csv", index=False)

# ── aggiorna ELO (formula ufficiale, K=60) ─────────────────────────────────
def gmult(gd):
    if gd <= 1: return 1.0
    if gd == 2: return 1.5
    return 1.75 + (gd - 3) / 8 if gd >= 3 else 1.0

elo = dict(ELO0)
for _, r in res.sort_values("date").iterrows():
    rh, ra = elo[r.home], elo[r.away]
    we = 1 / (1 + 10 ** (-(rh - ra) / 400))      # campo neutro (anche per host: l'ELO ufficiale dà +100 solo se in casa — i padroni di casa lo sono)
    we_h = 1 / (1 + 10 ** (-(rh - ra + (100 if r.home in {"Mexico","Canada","United States"} else 0)) / 400))
    wres = 1.0 if r.home_score > r.away_score else (0.0 if r.home_score < r.away_score else 0.5)
    g = gmult(abs(int(r.home_score) - int(r.away_score)))
    delta = 60 * g * (wres - we_h)
    elo[r.home] = rh + delta; elo[r.away] = ra - delta

changed = {t: round(elo[t] - ELO0[t], 1) for t in VALID if abs(elo[t] - ELO0[t]) > 0.1}
if changed:
    print("\nVariazioni ELO:", changed)

state = {"updated": str(datetime.datetime.now())[:16],
         "elo": {t: round(v, 2) for t, v in elo.items()},
         "results": res.to_dict("records")}
json.dump(state, open(f"{BASE}/state_2026.json", "w"), ensure_ascii=False)
print(f"\n✓ state_2026.json — {len(res)} risultati, ELO aggiornati")
