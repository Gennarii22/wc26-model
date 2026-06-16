"""
═══════════════════════════════════════════════════════════════════════════
  MONDIALE 2026 — Modello partita (Poisson sui gol, ELO-driven)
═══════════════════════════════════════════════════════════════════════════

Allena su ~30k partite internazionali (era moderna) un modello di Poisson:
    log λ(gol squadra) = α + β·(ELO_proprio − ELO_avv)/100 + γ·casa + δ·Mondiale
Poi, sui Mondiali 2006-2022, stima quanto il VALORE ROSA (e feature Klement:
PIL pro capite, popolazione) aggiungono oltre l'ELO → "ELO effettivo" corretto.

Validazione: leave-one-tournament-out sui Mondiali 2010-2022 (log-loss 1X2
vs baseline ELO win-expectancy). Output: match_model.pkl
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import joblib
from scipy.optimize import minimize
from scipy.stats import poisson

import os
_HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.environ.get("WC_RAW") or os.path.join(_HERE, "..", "..", "WorldCup DB", "raw")
OUT = os.environ.get("WC_OUT") or os.path.join(_HERE, "..", "..", "WorldCup DB", "output")
BASE = os.environ.get("WC_BASE") or _HERE

# ── 1. Partite internazionali (era moderna) ───────────────────────────────
m = pd.read_csv(f"{RAW}/elo_matches_computed.csv", parse_dates=["date"])
m = m[(m.date >= "1990-01-01") & m.home_score.notna()].copy()
m["wc"] = (m.tournament == "FIFA World Cup").astype(int)
m["competitive"] = (m.tournament != "Friendly").astype(int)
print(f"Partite training: {len(m):,} (1990→giu 2026) | Mondiali: {m.wc.sum()}")

# capped scores (rari 31-0 distorcono): cap a 8
m["hs"] = m.home_score.clip(upper=8); m["as_"] = m.away_score.clip(upper=8)

# ── 2. Fit Poisson MLE ─────────────────────────────────────────────────────
# log λ_home = a + b·dElo/100 + hadv·(1-neutral) + w·wc
# log λ_away = a − b·dElo/100 + w·wc
dE = ((m.home_elo_pre - m.away_elo_pre) / 100).values
neutral = m.neutral.astype(int).values
wc = m.wc.values
hs, as_ = m.hs.values, m["as_"].values

def nll(p):
    a, b, hadv, w = p
    lh = np.exp(a + b*dE + hadv*(1-neutral) + w*wc)
    la = np.exp(a - b*dE + w*wc)
    return -(poisson.logpmf(hs, lh).sum() + poisson.logpmf(as_, la).sum())

res = minimize(nll, [0.2, 0.15, 0.25, 0.0], method="Nelder-Mead",
               options={"xatol":1e-6,"fatol":1e-4,"maxiter":4000})
a, b, hadv, w = res.x
print(f"\nParametri Poisson: α={a:.4f}  β(elo/100)={b:.4f}  casa={hadv:.4f}  mondiale={w:.4f}")
print(f"  → gol medi neutro pari-elo: {np.exp(a):.2f} | vantaggio casa: ×{np.exp(hadv):.2f} su λ")

# ── 3. ELO effettivo ai Mondiali: aggiunte oltre l'ELO ────────────────────
# Sui match dei Mondiali 2006-2022, testo se le differenze di valore rosa /
# macro (Klement) spiegano i gol residui oltre l'ELO → coefficiente di
# conversione in "punti ELO equivalenti".
teams = pd.read_csv(f"{OUT}/worldcup_teams.csv")
panel = pd.read_csv(f"{OUT}/countries_panel.csv")
wcm = pd.read_csv(f"{OUT}/worldcup_matches.csv")
wcm = wcm[(wcm.year >= 2006) & (wcm.year < 2026)].copy()

tf = teams[["year","team_name","log_market_value","avg_age","avg_caps","pct_top5_leagues","country_iso3"]]
pan = panel[["iso3","year","log_gdppc_ppp_best","log_population"]]
tf = tf.merge(pan, left_on=["country_iso3","year"], right_on=["iso3","year"], how="left")

def join_side(df, side):
    s = tf.add_prefix(f"{side}_")
    return df.merge(s, left_on=["year", f"{side}_team_name"], right_on=[f"{side}_year", f"{side}_team_name"], how="left")
wcm = join_side(wcm, "home"); wcm = join_side(wcm, "away")
wcm = wcm.dropna(subset=["home_log_market_value","away_log_market_value","home_elo_pre","away_elo_pre"])
print(f"\nMatch Mondiali 2006-2022 con feature complete: {len(wcm)}")

dE2  = ((wcm.home_elo_pre - wcm.away_elo_pre)/100).values
dMV  = (wcm.home_log_market_value - wcm.away_log_market_value).values
dGDP = (wcm.home_log_gdppc_ppp_best - wcm.away_log_gdppc_ppp_best).fillna(0).values
dPOP = (wcm.home_log_population - wcm.away_log_population).fillna(0).values
dAGE = (wcm.home_avg_age - wcm.away_avg_age).fillna(0).values
dT5  = (wcm.home_pct_top5_leagues - wcm.away_pct_top5_leagues).fillna(0).values
h2, a2 = wcm.home_team_score.clip(upper=8).values, wcm.away_team_score.clip(upper=8).values

def nll2(p):
    c_mv, c_gdp, c_pop, c_age, c_t5 = p
    adj = c_mv*dMV + c_gdp*dGDP + c_pop*dPOP + c_age*dAGE + c_t5*dT5
    lh = np.exp(a + w + b*dE2 + adj)
    la = np.exp(a + w - b*dE2 - adj)
    return -(poisson.logpmf(h2, lh).sum() + poisson.logpmf(a2, la).sum())

res2 = minimize(nll2, [0.05,0,0,0,0], method="Nelder-Mead", options={"maxiter":6000})
c_mv, c_gdp, c_pop, c_age, c_t5 = res2.x
print("Aggiunte oltre l'ELO (coefficienti su log-rate gol):")
for nme,v in [("Δlog valore rosa",c_mv),("Δlog PIL pc (Klement)",c_gdp),("Δlog popolazione (Klement)",c_pop),("Δetà media",c_age),("Δ% top5 leghe",c_t5)]:
    print(f"  {nme:28} {v:+.4f}  (≈{v/b*100:+.0f} punti ELO per unità)" )

# ── 4. Validazione leave-one-tournament-out (2010-2022) ───────────────────
def match_probs(lh, la, max_g=10):
    P = np.outer(poisson.pmf(np.arange(max_g+1), lh), poisson.pmf(np.arange(max_g+1), la))
    ph = np.tril(P, -1).sum(); pd_ = np.trace(P); pa = np.triu(P, 1).sum()
    return ph, pd_, pa

print("\n── Validazione LOTO (log-loss 1X2, più basso=meglio) ──")
rows=[]
for yr in [2010, 2014, 2018, 2022]:
    te = wcm[wcm.year == yr]
    # baseline ELO: win expectancy → 1X2 grezzo via Poisson elo-only
    ll_elo, ll_full, nm = 0, 0, 0
    for _, r in te.iterrows():
        de = (r.home_elo_pre - r.away_elo_pre)/100
        # elo-only
        lh0, la0 = np.exp(a+w+b*de), np.exp(a+w-b*de)
        # full (mv + klement)
        adj = (c_mv*(r.home_log_market_value-r.away_log_market_value)
               + c_gdp*((r.home_log_gdppc_ppp_best or 0)-(r.away_log_gdppc_ppp_best or 0) if pd.notna(r.home_log_gdppc_ppp_best) and pd.notna(r.away_log_gdppc_ppp_best) else 0)
               + c_age*((r.home_avg_age-r.away_avg_age) if pd.notna(r.home_avg_age) else 0)
               + c_t5*((r.home_pct_top5_leagues-r.away_pct_top5_leagues) if pd.notna(r.home_pct_top5_leagues) else 0))
        lh1, la1 = np.exp(a+w+b*de+adj), np.exp(a+w-b*de-adj)
        out = 0 if r.home_team_score>r.away_team_score else (1 if r.home_team_score==r.away_team_score else 2)
        for ll_ref, (lh,la) in [("elo",(lh0,la0)),("full",(lh1,la1))]:
            p = match_probs(lh,la)
            p = np.clip(p,1e-6,1); p = p/sum(p)
            if ll_ref=="elo": ll_elo += -np.log(p[out])
            else: ll_full += -np.log(p[out])
        nm += 1
    rows.append({"anno":yr,"n":nm,"logloss_elo":ll_elo/nm,"logloss_full":ll_full/nm})
val = pd.DataFrame(rows)
print(val.to_string(index=False))
print(f"\nMedia: elo-only {val.logloss_elo.mean():.4f} | full {val.logloss_full.mean():.4f} "
      f"({(val.logloss_elo.mean()-val.logloss_full.mean())/val.logloss_elo.mean()*100:+.1f}%)")

# ── 5. Salva ───────────────────────────────────────────────────────────────
joblib.dump({"a":a,"b":b,"hadv":hadv,"w":w,
             "c_mv":c_mv,"c_gdp":c_gdp,"c_pop":c_pop,"c_age":c_age,"c_t5":c_t5,
             "validation":val.to_dict("records")},
            f"{BASE}/match_model.pkl")
print("\n✓ match_model.pkl salvato")
