"""
═══════════════════════════════════════════════════════════════════════════
  BETTING DATA — probabilità complete per ogni partita non ancora giocata
═══════════════════════════════════════════════════════════════════════════

Per ogni partita: λ casa/trasferta (con ELO aggiornati dallo stato live),
matrice dei risultati esatti (0-7 × 0-7) e probabilità dei mercati:
1X2, doppia chance, gol/no-gol (BTTS), over/under 0.5→4.5, parziali squadra.

Copre: 72 partite dei gironi (quelle non giocate) + partite KO future
(quando gli accoppiamenti saranno noti, da ESPN). Output: betting_data.js
"""
import os
import warnings; warnings.filterwarnings("ignore")
import json, os, datetime
import urllib.request
import numpy as np
import pandas as pd
import joblib
from scipy.stats import poisson

OUT = os.environ.get("WC_OUT") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
BASE = os.environ.get("WC_BASE") or os.path.dirname(os.path.abspath(__file__))
M = joblib.load(f"{BASE}/match_model.pkl")
a, b, w = M["a"], M["b"], M["w"]
HADV = b * 1.0
MAXG = 8

# squadre + forza con ELO aggiornati (stessa logica del simulatore)
teams = pd.read_csv(f"{OUT}/worldcup_teams.csv"); t26 = teams[teams.year == 2026].copy()
panel = pd.read_csv(f"{OUT}/countries_panel.csv")
pan = panel[panel.year == 2024][["iso3", "log_gdppc_ppp_best", "log_population"]]
t26 = t26.merge(pan, left_on="country_iso3", right_on="iso3", how="left")
for c in ["log_gdppc_ppp_best", "log_population"]: t26[c] = t26[c].fillna(t26[c].median())

STATE = json.load(open(f"{BASE}/state_2026.json")) if os.path.exists(f"{BASE}/state_2026.json") else None
t26["elo_cur"] = t26.team_name.map(STATE["elo"]).fillna(t26.elo_pre_tournament) if STATE else t26.elo_pre_tournament
KNOWN = {(r["home"], r["away"]) for r in (STATE["results"] if STATE else [])}

S = (b*t26.elo_cur/100 + M["c_mv"]*t26.log_market_value + M["c_gdp"]*t26.log_gdppc_ppp_best
     + M["c_pop"]*t26.log_population + M["c_age"]*t26.avg_age + M["c_t5"]*t26.pct_top5_leagues)
t26["S"] = S - S.mean()
STR = dict(zip(t26.team_name, t26.S))
ELO = dict(zip(t26.team_name, t26.elo_cur.round(0)))
MV = dict(zip(t26.team_name, (t26.market_value_eur/1e6).round(0)))
GROUPS = json.load(open(f"{BASE}/groups_resolved.json"))
GROUP_OF = {t: g for g, ts in GROUPS.items() for t in ts}

# calendario gironi
mm = pd.read_csv(f"{OUT}/worldcup_matches.csv"); m26 = mm[mm.year == 2026].copy()
MX = {"Mexico City","Zapopan","Guadalajara","Monterrey"}; CA = {"Toronto","Vancouver"}
m26["venue_country"] = m26.city_name.map(lambda c: "Mexico" if c in MX else ("Canada" if c in CA else "United States"))
fixtures = [(r.home_team_name, r.away_team_name, r.venue_country, r.city_name, r.match_date, "Gironi")
            for _, r in m26.iterrows()]

# partite future da ESPN (aggiunge i KO quando saranno definiti)
def espn_upcoming(days=7):
    out = []
    today = datetime.date.today()
    for k in range(days):
        d = today + datetime.timedelta(days=k)
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates={d.strftime('%Y%m%d')}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            data = json.load(urllib.request.urlopen(req, timeout=15))
            for e in data.get("events", []):
                comp = e["competitions"][0]
                if comp["status"]["type"]["name"] != "STATUS_SCHEDULED": continue
                cm = {c["homeAway"]: c["team"]["displayName"] for c in comp["competitors"]}
                city = comp.get("venue", {}).get("address", {}).get("city", "")
                out.append((cm["home"], cm["away"], str(d), city))
        except Exception:
            pass
    return out

ALIAS = {"Czechia":"Czech Republic","USA":"United States","Türkiye":"Turkey","Cabo Verde":"Cape Verde",
         "Congo DR":"DR Congo","Côte d'Ivoire":"Ivory Coast","Curacao":"Curaçao",
         "Bosnia-Herzegovina":"Bosnia and Herzegovina","Korea Republic":"South Korea"}
def canon(x):
    x = ALIAS.get(x, x)
    return x if x in STR else None

sched_pairs = {(h, aw) for h, aw, *_ in fixtures}
for h, aw, d, city in espn_upcoming():
    ch, ca_ = canon(h), canon(aw)
    if ch and ca_ and (ch, ca_) not in sched_pairs:
        ven = "Mexico" if city in MX else ("Canada" if city in CA else "United States")
        fixtures.append((ch, ca_, ven, city or "USA", d, "Eliminazione"))

# ── mercati da matrice Poisson ─────────────────────────────────────────────
def markets(lh, la):
    g = np.arange(MAXG+1)
    P = np.outer(poisson.pmf(g, lh), poisson.pmf(g, la))
    P = P / P.sum()
    p1 = float(np.tril(P,-1).sum()); px = float(np.trace(P)); p2 = float(np.triu(P,1).sum())
    tot = np.add.outer(g, g)
    ou = {f"{x+0.5}": float(P[tot > x+0.5].sum()) for x in range(5)}    # over 0.5..4.5
    btts = float(P[1:,1:].sum())
    out = {
        "1": p1, "X": px, "2": p2,
        "1X": p1+px, "12": p1+p2, "X2": px+p2,
        "GOL": btts, "NOGOL": 1-btts,
        **{f"OVER {k}": v for k, v in ou.items()},
        **{f"UNDER {k}": 1-v for k, v in ou.items()},
    }
    return out, P

# ── marcatori per partita: P(segna) / P(doppietta) / P(tripletta) ──────────
import re as _re, math
PR = pd.read_csv(f"{BASE}/data/player_rates.csv")
PR["w"] = PR.op_rate90.fillna(0.1)*(PR.exp_min.fillna(60)/90) + PR.pen_rate90.fillna(0)
def match_scorers(team, lam, n=5):
    sub = PR[PR.team == team]; W = sub.w.sum()
    if W <= 0 or lam <= 0: return []
    rows = []
    for _, p in sub.iterrows():
        li = lam * p.w / W
        if li < 0.04: continue
        e = math.exp(-li)
        rows.append({"player": _re.sub(r'\s*\(captain\)', '', str(p.player)).strip(),
                     "li": li, "p1": round((1-e)*100,1),
                     "p2": round((1-e*(1+li))*100,1),
                     "p3": round((1-e*(1+li+li*li/2))*100,1)})
    rows.sort(key=lambda x: -x["li"])
    return [{k:v for k,v in r.items() if k!="li"} for r in rows[:n]]

# ── tiri per partita: P(over 0.5 / 1.5 / 2.5 tiri) per giocatore ────────────
PR["esh"] = PR.exp_shots_match.fillna(PR.pos.map({'FW':2.0,'MF':1.0,'DF':0.5,'GK':0.0})).fillna(0.7) if "exp_shots_match" in PR.columns else 0.7
SH_LAM_AVG = 1.3   # lambda-gol medio di una squadra: scala la dominanza nei tiri
def match_shots(team, lh, n=6):
    sub = PR[PR.team == team]
    if not len(sub): return []
    ctx = float(np.clip(lh / SH_LAM_AVG, 0.7, 1.4))   # squadra dominante = piu' tiri
    rows = []
    for _, p in sub.iterrows():
        li = float(p.esh) * ctx
        if li < 0.3: continue
        e = math.exp(-li)
        rows.append({"player": _re.sub(r'\s*\(captain\)', '', str(p.player)).strip(),
                     "li": li, "s1": round((1-e)*100,1),
                     "s2": round((1-e*(1+li))*100,1),
                     "s3": round((1-e*(1+li+li*li/2))*100,1)})
    rows.sort(key=lambda x: -x["li"])
    return [{k:v for k,v in r.items() if k!="li"} for r in rows[:n]]

out = {"updated": (STATE["updated"] if STATE else "pre-torneo"), "matches": []}
for h, aw, ven, city, date, stage in sorted(fixtures, key=lambda x: x[4]):
    played = (h, aw) in KNOWN
    d = STR[h] - STR[aw]
    hh = HADV if h == ven else 0.0; ha = HADV if aw == ven else 0.0
    lh = float(np.exp(a + w + d + hh)); la = float(np.exp(a + w - d + ha))
    mk, P = markets(lh, la)
    top_scores = sorted([(f"{i}-{j}", float(P[i,j])) for i in range(6) for j in range(6)],
                        key=lambda x: -x[1])[:8]
    out["matches"].append({
        "home": h, "away": aw, "date": date, "city": city, "venue": ven,
        "stage": stage, "group": GROUP_OF.get(h, ""), "played": played,
        "elo_h": ELO[h], "elo_a": ELO[aw], "mv_h": MV.get(h), "mv_a": MV.get(aw),
        "lh": round(lh, 2), "la": round(la, 2),
        "markets": {k: round(v, 4) for k, v in mk.items()},
        "matrix": [[round(float(P[i, j]), 4) for j in range(7)] for i in range(7)],
        "top_scores": [{"s": s, "p": round(p*100, 1)} for s, p in top_scores],
        "gh_dist": [round(float(poisson.pmf(i, lh)), 4) for i in range(7)],
        "ga_dist": [round(float(poisson.pmf(i, la)), 4) for i in range(7)],
        "scorers_h": match_scorers(h, lh), "scorers_a": match_scorers(aw, la),
        "shots_h": match_shots(h, lh), "shots_a": match_shots(aw, la),
    })

with open(f"{BASE}/betting_data.js", "w") as f:
    f.write("window.BET = " + json.dumps(out, ensure_ascii=False) + ";")
n_up = sum(1 for m in out["matches"] if not m["played"])
print(f"✓ betting_data.js — {len(out['matches'])} partite ({n_up} da giocare)")
