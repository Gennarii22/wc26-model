"""
═══════════════════════════════════════════════════════════════════════════
  MONDIALE 2026 — Simulatore Monte Carlo (regole FIFA ufficiali)
═══════════════════════════════════════════════════════════════════════════

- 72 partite dei gironi con sede reale → vantaggio casa solo nel proprio paese
- Tiebreaker Art.13: head-to-head per coppie a pari punti (esatto), poi
  diff.reti/gol totali; ranking FIFA finale ≈ ELO (deterministico, no sorteggio)
- Migliori 8 terze: punti, DR, GF, ELO
- Assegnazione terze nel tabellone: TABELLA UFFICIALE FIFA Annexe C (495 righe)
- Tabellone R32→finale ufficiale con sedi (Azteca/Monterrey/Toronto/Vancouver)
- KO: 90' Poisson → supplementari λ/3 → rigori (lieve tilt ELO)
"""
import warnings; warnings.filterwarnings("ignore")
import os
import json
import numpy as np
import pandas as pd
import joblib
from scipy.stats import poisson

OUT = os.environ.get("WC_OUT") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
BASE = os.environ.get("WC_BASE") or os.path.dirname(os.path.abspath(__file__))
N_SIMS = 20000
RNG = np.random.default_rng(42)

M = joblib.load(f"{BASE}/match_model.pkl")
a, b, w = M["a"], M["b"], M["w"]
HADV = b * 1.0          # +100 ELO equivalenti, solo nel proprio paese (letteratura)

# ── Stato live (risultati giocati + ELO aggiornati da update_tournament.py) ─
import os
STATE = None
if os.path.exists(f"{BASE}/state_2026.json"):
    STATE = json.load(open(f"{BASE}/state_2026.json"))
    print(f"▶ Stato live caricato ({STATE['updated']}): {len(STATE['results'])} risultati reali, ELO aggiornati")
KNOWN = {}   # frozenset({home,away}) → (home, away, hs, as, pen_home, pen_away) — indip. da casa/trasferta
if STATE:
    for r in STATE["results"]:
        KNOWN[frozenset((r["home"], r["away"]))] = (
            r["home"], r["away"], int(r["home_score"]), int(r["away_score"]),
            r.get("pen_home"), r.get("pen_away"))

# ── 1. Squadre e forza ─────────────────────────────────────────────────────
teams = pd.read_csv(f"{OUT}/worldcup_teams.csv")
t26 = teams[teams.year == 2026].copy()
panel = pd.read_csv(f"{OUT}/countries_panel.csv")
pan = panel[panel.year == 2024][["iso3", "log_gdppc_ppp_best", "log_population"]]
t26 = t26.merge(pan, left_on="country_iso3", right_on="iso3", how="left")
for c in ["log_gdppc_ppp_best", "log_population"]:
    t26[c] = t26[c].fillna(t26[c].median())

# ELO correnti: aggiornati se c'è lo stato live, altrimenti pre-torneo
if STATE:
    t26["elo_cur"] = t26.team_name.map(STATE["elo"]).fillna(t26.elo_pre_tournament)
else:
    t26["elo_cur"] = t26.elo_pre_tournament
S = (b * t26.elo_cur / 100
     + M["c_mv"] * t26.log_market_value + M["c_gdp"] * t26.log_gdppc_ppp_best
     + M["c_pop"] * t26.log_population + M["c_age"] * t26.avg_age
     + M["c_t5"] * t26.pct_top5_leagues)
t26["S"] = S - S.mean()
STR = dict(zip(t26.team_name, t26.S))
ELO = dict(zip(t26.team_name, t26.elo_pre_tournament))   # spareggio FIFA (deterministico, pre-torneo)
ELO_CUR = dict(zip(t26.team_name, t26.elo_cur))           # ELO live (aggiornato dai risultati) → display
TEAMS = list(t26.team_name); IDX = {t: i for i, t in enumerate(TEAMS)}; nt = len(TEAMS)
HOSTS = {"Mexico", "Canada", "United States"}

# Incertezza sulla forza (forma/infortuni): deriva ELO storica nei tornei
# std=59 ELO → uso 70% (il resto è fortuna già nel Poisson) = 41 punti ELO.
# Errore CORRELATO per squadra entro la stessa simulazione → code più larghe,
# calibrazione torneo allineata a Zeileis/bookmaker.
SIGMA_S = b * 0.41
S_vec = np.array([STR[t] for t in TEAMS])

# ── 2. Gironi ufficiali (sorteggio dic 2025) ──────────────────────────────
GROUPS = {
 "A": ["Mexico","South Africa","South Korea","Czech Republic"],
 "B": ["Canada","Switzerland","Qatar","Bosnia and Herzegovina"],
 "C": ["Brazil","Morocco","Scotland","Haiti"],
 "D": ["United States","Paraguay","Australia","Turkey"],
 "E": ["Germany","Ecuador","Ivory Coast","Curaçao"],
 "F": ["Netherlands","Japan","Sweden","Tunisia"],
 "G": ["Belgium","Egypt","Iran","New Zealand"],
 "H": ["Spain","Uruguay","Saudi Arabia","Cape Verde"],
 "I": ["France","Senegal","Norway","Iraq"],
 "J": ["Argentina","Austria","Algeria","Jordan"],
 "K": ["Portugal","Colombia","Uzbekistan","DR Congo"],
 "L": ["England","Croatia","Panama","Ghana"],
}
GROUP_OF = {t: g for g, ts in GROUPS.items() for t in ts}
assert set(GROUP_OF) == set(TEAMS), f"mismatch: {set(GROUP_OF)^set(TEAMS)}"

# ── 3. Calendario gironi con sede ──────────────────────────────────────────
mm = pd.read_csv(f"{OUT}/worldcup_matches.csv")
m26 = mm[mm.year == 2026].copy()
MX = {"Mexico City","Zapopan","Guadalajara","Monterrey"}; CA = {"Toronto","Vancouver"}
m26["venue_country"] = m26.city_name.map(lambda c: "Mexico" if c in MX else ("Canada" if c in CA else "United States"))
group_fixtures = [(r.home_team_name, r.away_team_name, r.venue_country, r.city_name, r.match_date)
                  for _, r in m26.iterrows()]

# ── 4. Tabella FIFA Annexe C (terze) ───────────────────────────────────────
annexc = pd.read_csv(f"{OUT}/annexC_third_place_allocation.csv")
annexc["key"] = annexc.qualified_groups.map(lambda s: "".join(sorted(s)))
THIRD_COLS = {"A":"vs_1A_M79","B":"vs_1B_M85","D":"vs_1D_M81","E":"vs_1E_M74",
              "G":"vs_1G_M82","I":"vs_1I_M77","K":"vs_1K_M87","L":"vs_1L_M80"}
ALLOC = {r.key: {g: r[c] for g, c in THIRD_COLS.items()} for _, r in annexc.iterrows()}

# ── 5. Motore match ────────────────────────────────────────────────────────
def lambdas(th, ta, venue):
    d = STR[th] - STR[ta]
    hh = HADV if (th in HOSTS and th == {"Mexico":"Mexico","Canada":"Canada","United States":"United States"}.get(venue, venue)) else 0.0
    ha = HADV if (ta in HOSTS and ta == venue) else 0.0
    # nota: venue è il paese; vantaggio se squadra == paese sede
    hh = HADV if th == venue else 0.0
    ha = HADV if ta == venue else 0.0
    return np.exp(a + w + d + hh), np.exp(a + w - d + ha)

# risultati noti dei KO (esclude le partite dei gironi già consumate)
GROUP_PAIRS = set()
def _register_group_pairs(fixtures):
    for h, aw, *_ in fixtures:
        GROUP_PAIRS.add(frozenset((h, aw)))
KNOWN_KO = {}   # frozenset({i1,i2}) → indice vincitore
def _build_known_ko():
    for h, aw, hs_, as2, ph, pa in KNOWN.values():
        if frozenset((h, aw)) in GROUP_PAIRS: continue
        if h not in IDX or aw not in IDX: continue
        if hs_ > as2: wnr = IDX[h]
        elif as2 > hs_: wnr = IDX[aw]
        else:
            if ph is not None and pa is not None and not (pd.isna(ph) or pd.isna(pa)):
                wnr = IDX[h] if float(ph) > float(pa) else IDX[aw]
            else: continue
        KNOWN_KO[frozenset((IDX[h], IDX[aw]))] = wnr

def sim_ko_pairs(hi, ai, venue, n):
    """hi/ai array di indici squadra per sim (vettorizzato, usa S con rumore).
    Se il risultato reale del KO è noto, viene imposto."""
    Sh = Snoise[np.arange(n), hi]; Sa = Snoise[np.arange(n), ai]
    hostv = np.array([1.0 if TEAMS[i] == venue else 0.0 for i in range(nt)])
    hh = hostv[hi] * HADV; ha = hostv[ai] * HADV
    d = Sh - Sa
    lh = np.exp(a + w + d + hh); la = np.exp(a + w - d + ha)
    gh, ga = RNG.poisson(lh), RNG.poisson(la)
    eh, ea = RNG.poisson(lh/3), RNG.poisson(la/3)
    elo_eq = d / b * 100
    p_pen = 1 / (1 + 10 ** (-elo_eq * 0.5 / 400))
    pen = RNG.random(n) < p_pen
    wh = np.where(gh != ga, gh > ga, np.where(eh != ea, eh > ea, pen))
    out = np.where(wh, hi, ai)
    for pair, wnr in KNOWN_KO.items():
        i1, i2 = tuple(pair)
        mask = ((hi == i1) & (ai == i2)) | ((hi == i2) & (ai == i1))
        out[mask] = wnr
    return out

# ── 6. Simula i gironi ─────────────────────────────────────────────────────
print(f"Simulo {N_SIMS:,} tornei (tiebreaker FIFA Art.13, rumore forza σ=41 ELO)…")
n = N_SIMS
_register_group_pairs(group_fixtures)
_build_known_ko()
if KNOWN_KO:
    print(f"  → {len(KNOWN_KO)} partite KO fissate al risultato reale")
Snoise = S_vec[None, :] + RNG.normal(0, SIGMA_S, (n, nt))   # forza per-sim correlata
fix = {}
n_fixed = 0
for h, aw, ven, city, date in group_fixtures:
    rec = KNOWN.get(frozenset((h, aw)))        # risultato REALE → fissato in tutte le sim
    if rec:
        rh, _, rhs, ras, _, _ = rec
        hs_, as2 = (rhs, ras) if rh == h else (ras, rhs)   # orienta sul calendario
        fix[(h, aw)] = (np.full(n, hs_, np.int64), np.full(n, as2, np.int64))
        n_fixed += 1
        continue
    ih, ia = IDX[h], IDX[aw]
    d = Snoise[:, ih] - Snoise[:, ia]
    hh = HADV if h == ven else 0.0; ha = HADV if aw == ven else 0.0
    lh = np.exp(a + w + d + hh); la = np.exp(a + w - d + ha)
    fix[(h, aw)] = (RNG.poisson(lh), RNG.poisson(la))
if n_fixed:
    print(f"  → {n_fixed} partite dei gironi fissate al risultato reale")

pts = np.zeros((n, nt), np.int32); gd = np.zeros((n, nt), np.int32); gf = np.zeros((n, nt), np.int32)
team_goals = np.zeros((n, nt), np.int32)
for (h, aw), (gh, ga) in fix.items():
    ih, ia = IDX[h], IDX[aw]
    pts[:, ih] += np.where(gh > ga, 3, np.where(gh == ga, 1, 0))
    pts[:, ia] += np.where(ga > gh, 3, np.where(gh == ga, 1, 0))
    gd[:, ih] += gh - ga; gd[:, ia] += ga - gh
    gf[:, ih] += gh; gf[:, ia] += ga
    team_goals[:, ih] += gh; team_goals[:, ia] += ga

# chiave base: pts ▸ DR ▸ GF ▸ ELO (ranking FIFA come ultimo criterio, deterministico)
elo_arr = np.array([ELO[t] for t in TEAMS])
base_key = pts*1e10 + (gd+500)*1e6 + gf*1e3 + elo_arr/3000
rank_in_group = np.zeros((n, nt), np.int8)
for g, ts in GROUPS.items():
    ii = [IDX[t] for t in ts]
    order = (-base_key[:, ii]).argsort(1).argsort(1)
    for j, ti in enumerate(ii):
        rank_in_group[:, ti] = order[:, j]

# correzione head-to-head ESATTA per coppie a pari punti adiacenti nel ranking
for g, ts in GROUPS.items():
    ii = [IDX[t] for t in ts]
    for x in range(4):
        for y in range(x+1, 4):
            t1, t2 = ts[x], ts[y]; i1, i2 = IDX[t1], IDX[t2]
            if (t1, t2) in fix: gh, ga = fix[(t1, t2)]; d12 = gh - ga
            else: gh, ga = fix[(t2, t1)]; d12 = ga - gh
            same_pts = pts[:, i1] == pts[:, i2]
            # nessun'altra squadra del girone con gli stessi punti (tie a 2)
            others = [IDX[t] for t in ts if t not in (t1, t2)]
            only2 = same_pts & (pts[:, others[0]] != pts[:, i1]) & (pts[:, others[1]] != pts[:, i1])
            # H2H decide: se d12>0 t1 sopra, d12<0 t2 sopra (se H2H pari resta base key)
            r1, r2 = rank_in_group[:, i1], rank_in_group[:, i2]
            swap_to_t1 = only2 & (d12 > 0) & (r1 > r2)
            swap_to_t2 = only2 & (d12 < 0) & (r2 > r1)
            for mask, lo, hi_ in [(swap_to_t1, i1, i2), (swap_to_t2, i2, i1)]:
                if mask.any():
                    tmp = rank_in_group[mask, lo].copy()
                    rank_in_group[mask, lo] = rank_in_group[mask, hi_]
                    rank_in_group[mask, hi_] = tmp

# vincitori/seconde/terze
winners_g, runners_g, thirds_g = {}, {}, {}
for g, ts in GROUPS.items():
    ii = np.array([IDX[t] for t in ts])
    winners_g[g] = ii[rank_in_group[:, ii].argmin(1)]
    runners_g[g] = ii[np.abs(rank_in_group[:, ii]-1).argmin(1)]
    thirds_g[g]  = ii[np.abs(rank_in_group[:, ii]-2).argmin(1)]

# migliori 8 terze (pts ▸ DR ▸ GF ▸ ELO)
third_key = np.full((n, nt), -np.inf)
for g in GROUPS:
    ti = thirds_g[g]
    third_key[np.arange(n), ti] = base_key[np.arange(n), ti]
order_third = (-third_key).argsort(1)
qual_third = np.zeros((n, nt), bool)
qual_third[np.arange(n)[:, None], order_third[:, :8]] = True

# ── 7. Tabellone (ufficiale FIFA) ──────────────────────────────────────────
group_letters = sorted(GROUPS)
# per sim: stringa gironi con terza qualificata → riga Annexe C
tq = np.zeros((n, 12), bool)
for j, g in enumerate(group_letters):
    tq[:, j] = qual_third[np.arange(n), thirds_g[g]]
# patterns → allocazione (cache sui pattern unici: al più 495)
pat_codes = tq.dot(1 << np.arange(12))
third_for = {g: np.zeros(n, np.int32) for g in THIRD_COLS}   # 1X → indice squadra terza
uniq = np.unique(pat_codes)
for code in uniq:
    mask = pat_codes == code
    qg = "".join(group_letters[j] for j in range(12) if (code >> j) & 1)
    alloc = ALLOC.get("".join(sorted(qg)))
    if alloc is None:                                  # non dovrebbe accadere
        gl = [g for g in qg]; alloc = {k: gl[i % len(gl)] for i, k in enumerate(THIRD_COLS)}
    for gk in THIRD_COLS:
        src_group = alloc[gk].replace("3", "")         # es. "3E" → "E"
        third_for[gk][mask] = thirds_g[src_group][mask]

US, MXC, CAN = "United States", "Mexico", "Canada"
R32 = [
    ("M73", "2A", "2B", US), ("M74", "1E", "T_E", US), ("M75", "1F", "2C", MXC),
    ("M76", "1C", "2F", US), ("M77", "1I", "T_I", US), ("M78", "2E", "2I", US),
    ("M79", "1A", "T_A", MXC), ("M80", "1L", "T_L", US), ("M81", "1D", "T_D", US),
    ("M82", "1G", "T_G", US), ("M83", "2K", "2L", CAN), ("M84", "1H", "2J", US),
    ("M85", "1B", "T_B", CAN), ("M86", "1J", "2H", US), ("M87", "1K", "T_K", US),
    ("M88", "2D", "2G", US),
]
def slot(s):
    if s.startswith("T_"): return third_for[s[2]]
    pos, g = s[0], s[1]
    return winners_g[g] if pos == "1" else runners_g[g]

reach = {st: np.zeros(nt) for st in ["R32","R16","QF","SF","F","W"]}
for g in GROUPS:
    np.add.at(reach["R32"], winners_g[g], 1); np.add.at(reach["R32"], runners_g[g], 1)
for gk in THIRD_COLS:
    np.add.at(reach["R32"], third_for[gk], 1)

r32w = []
for mid, sh, sa, ven in R32:
    wnr = sim_ko_pairs(slot(sh), slot(sa), ven, n)
    r32w.append(wnr); np.add.at(reach["R16"], wnr, 1)

# R16 (ufficiale): M89 W74-W77 | M90 W73-W75 | M91 W76-W78 | M92 W79-W80 (Azteca)
#                  M93 W83-W84 | M94 W81-W82 | M95 W86-W88 | M96 W85-W87 (Vancouver)
W = {f"M{73+i}": r32w[i] for i in range(16)}
R16 = [("M89","M74","M77",US),("M90","M73","M75",US),("M91","M76","M78",US),
       ("M92","M79","M80",MXC),("M93","M83","M84",US),("M94","M81","M82",US),
       ("M95","M86","M88",US),("M96","M85","M87",CAN)]
r16w = []
for mid, x, y, ven in R16:
    wnr = sim_ko_pairs(W[x], W[y], ven, n); r16w.append(wnr); np.add.at(reach["QF"], wnr, 1)
W16 = {R16[i][0]: r16w[i] for i in range(8)}
QF = [("M97","M89","M90",US),("M98","M93","M94",US),("M99","M91","M92",US),("M100","M95","M96",US)]
qfw = []
for mid, x, y, ven in QF:
    wnr = sim_ko_pairs(W16[x], W16[y], ven, n); qfw.append(wnr); np.add.at(reach["SF"], wnr, 1)
WQF = {QF[i][0]: qfw[i] for i in range(4)}
SF = [("M101","M97","M98",US),("M102","M99","M100",US)]
sfw = []
for mid, x, y, ven in SF:
    wnr = sim_ko_pairs(WQF[x], WQF[y], ven, n); sfw.append(wnr); np.add.at(reach["F"], wnr, 1)
champ = sim_ko_pairs(sfw[0], sfw[1], US, n)
np.add.at(reach["W"], champ, 1)

# ── 8. Output ──────────────────────────────────────────────────────────────
res = pd.DataFrame({"team": TEAMS})
res["group"] = res.team.map(GROUP_OF)
res["elo"] = res.team.map(ELO_CUR).round(0)              # ELO live aggiornato
res["elo_pre"] = res.team.map(ELO).round(0)              # ELO pre-torneo (giorno 0)
res["elo_delta"] = (res["elo"] - res["elo_pre"]).round(0)
res["mv_meur"] = (res.team.map(dict(zip(t26.team_name, t26.market_value_eur)))/1e6).round(0)
wg = np.zeros(nt)
for g in GROUPS: np.add.at(wg, winners_g[g], 1)
res["p_win_group"] = wg/n*100
for st, col in [("R32","p_r32"),("R16","p_r16"),("QF","p_qf"),("SF","p_sf"),("F","p_final"),("W","p_win")]:
    res[col] = reach[st]/n*100
res["exp_goals_group"] = team_goals.mean(0).round(2)
res = res.sort_values("p_win", ascending=False)
res.to_csv(f"{BASE}/team_probs.csv", index=False)

mp = []
for h, aw, ven, city, date in group_fixtures:
    lh, la = lambdas(h, aw, ven)
    P = np.outer(poisson.pmf(np.arange(11), lh), poisson.pmf(np.arange(11), la))
    p1, px, p2 = np.tril(P,-1).sum(), np.trace(P), np.triu(P,1).sum()
    ml = np.unravel_index(P.argmax(), P.shape)
    mp.append({"date": date, "group": GROUP_OF[h], "home": h, "away": aw, "venue": ven,
               "city": city, "p1": round(p1*100,1), "px": round(px*100,1), "p2": round(p2*100,1),
               "lh": round(lh,2), "la": round(la,2), "score_ml": f"{ml[0]}-{ml[1]}"})
pd.DataFrame(mp).sort_values("date").to_csv(f"{BASE}/match_predictions.csv", index=False)
np.save(f"{BASE}/team_goals_group.npy", team_goals)
json.dump(TEAMS, open(f"{BASE}/teams_order.json", "w"))
json.dump(GROUPS, open(f"{BASE}/groups_resolved.json", "w"))

print("\nTOP 12 — probabilità Mondiale 2026:")
print(res.head(12)[["team","group","elo","p_win_group","p_r16","p_qf","p_sf","p_final","p_win"]].to_string(index=False))
print("\n✓ Salvati: team_probs.csv, match_predictions.csv")
