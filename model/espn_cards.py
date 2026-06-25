"""
espn_cards.py (cloud) — scarica i cartellini per squadra da OGNI partita WC giocata
(ESPN summary: boxscore.teams.statistics yellowCards/redCards/foulsCommitted) e
ne ricava i tassi-squadra + la statistica di dispersione per il modello over/under
cartellini di partita. Output: data/team_cards.csv + data/cards_meta.json.
Gira nel workflow PRIMA di gen_betting.
"""
import json, os, urllib.request, datetime as dt
BASE = os.path.dirname(os.path.abspath(__file__))
START = dt.date(2026, 6, 11)
UA = {"User-Agent": "Mozilla/5.0"}
ALIAS = {"Czechia":"Czech Republic","USA":"United States","Türkiye":"Turkey","Cabo Verde":"Cape Verde",
         "Congo DR":"DR Congo","Côte d'Ivoire":"Ivory Coast","Curacao":"Curaçao",
         "Bosnia-Herzegovina":"Bosnia and Herzegovina","Korea Republic":"South Korea"}
def canon(n): return ALIAS.get(n, n)

def get(url):
    try: return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20))
    except Exception: return None

def run():
    today = dt.date.today()
    teams = {}            # team -> [matches, yellows, reds]
    match_totals = []     # cartellini totali per partita (per la dispersione)
    d = START
    while d <= today:
        sb = get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates={d.strftime('%Y%m%d')}")
        for e in (sb or {}).get("events", []):
            c = e["competitions"][0]
            if c["status"]["type"]["name"] not in ("STATUS_FULL_TIME", "STATUS_POST"): continue
            s = get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/summary?event={e['id']}")
            tot = 0; ok = False
            for tm in (s or {}).get("boxscore", {}).get("teams", []):
                nm = canon(tm.get("team", {}).get("displayName", ""))
                st = {x.get("name"): x.get("displayValue") for x in tm.get("statistics", [])}
                if "yellowCards" not in st: continue
                y = int(st.get("yellowCards", 0) or 0); r = int(st.get("redCards", 0) or 0)
                rec = teams.setdefault(nm, [0, 0, 0]); rec[0] += 1; rec[1] += y; rec[2] += r
                tot += y + r; ok = True
            if ok: match_totals.append(tot)
        d += dt.timedelta(days=1)

    import csv
    with open(f"{BASE}/data/team_cards.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["team", "matches", "yellows", "reds", "cards"])
        for t, (m, y, r) in sorted(teams.items()):
            w.writerow([t, m, y, r, y + r])
    # statistica di dispersione (cartellini totali per partita)
    n = len(match_totals)
    mean = sum(match_totals) / n if n else 4.5
    var = sum((x - mean) ** 2 for x in match_totals) / n if n > 1 else mean * 1.4
    meta = {"n_matches": n, "mean_total": round(mean, 3), "var_total": round(var, 3),
            "team_mean": round(mean / 2, 3) if n else 2.25}
    json.dump(meta, open(f"{BASE}/data/cards_meta.json", "w"), indent=2)
    print(f"✓ team_cards.csv ({len(teams)} squadre, {n} partite) | media {mean:.2f} cartellini/partita, var {var:.2f}")

if __name__ == "__main__":
    run()
