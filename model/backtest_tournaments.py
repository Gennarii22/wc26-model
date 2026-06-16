"""
═══════════════════════════════════════════════════════════════════════════
  BACKTEST STORICO — il modello applicato ai Mondiali 1998-2022
═══════════════════════════════════════════════════════════════════════════

Per ogni edizione: SOLO dati disponibili prima del via (ELO pre-torneo, valore
rosa dell'epoca [dal 2006], età, macro dell'anno) → 10.000 simulazioni col
tabellone standard a 32 squadre → confronto con l'esito reale.

Domande: che probabilità dava al vincitore reale? In che posizione lo
classificava? Il favorito del modello come è andato? Calibrazione complessiva.
"""
import warnings; warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import joblib

import os
_HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.environ.get("WC_OUT") or os.path.join(_HERE, "..", "..", "WorldCup DB", "output")
BASE = os.environ.get("WC_BASE") or _HERE
M = joblib.load(f"{BASE}/match_model.pkl")
a, b, w = M["a"], M["b"], M["w"]
HADV = b * 1.0
SIGMA_S = b * 0.41
N = 10000

teams_all = pd.read_csv(f"{OUT}/worldcup_teams.csv")
matches_all = pd.read_csv(f"{OUT}/worldcup_matches.csv")
panel = pd.read_csv(f"{OUT}/countries_panel.csv")

# esiti reali
REAL = {1998:("France","Brazil"), 2002:("Brazil","Germany"), 2006:("Italy","France"),
        2010:("Spain","Netherlands"), 2014:("Germany","Argentina"),
        2018:("France","Croatia"), 2022:("Argentina","France")}

# tabellone standard 32 squadre (FIFA 1998-2022)
R16 = [("1A","2B"),("1C","2D"),("1B","2A"),("1D","2C"),("1E","2F"),("1G","2H"),("1F","2E"),("1H","2G")]
QFp = [(0,1),(4,5),(2,3),(6,7)]; SFp = [(0,1),(2,3)]

def run_year(yr):
    rng = np.random.default_rng(yr)
    t = teams_all[teams_all.year == yr].copy()
    m = matches_all[(matches_all.year == yr) & (matches_all.group_stage == 1)].copy()
    m["g"] = m.group_name.str.extract(r"Group ([A-H])")
    pan = panel[panel.year == yr][["iso3","log_gdppc_ppp_best","log_population"]]
    t = t.merge(pan, left_on="country_iso3", right_on="iso3", how="left")
    for c in ["log_gdppc_ppp_best","log_population"]:
        t[c] = t[c].fillna(t[c].median())
    use_mv = yr >= 2006 and t.log_market_value.notna().mean() > 0.9
    if use_mv:
        S = (b*t.elo_pre_tournament/100 + M["c_mv"]*t.log_market_value
             + M["c_gdp"]*t.log_gdppc_ppp_best + M["c_pop"]*t.log_population
             + M["c_age"]*t.avg_age.fillna(t.avg_age.median())
             + M["c_t5"]*t.pct_top5_leagues.fillna(t.pct_top5_leagues.median()))
    else:
        S = b*t.elo_pre_tournament/100
    t["S"] = S - S.mean()
    TEAMS = list(t.team_name); IDX = {x:i for i,x in enumerate(TEAMS)}; nt=len(TEAMS)
    Sv = t.S.values; elo = t.elo_pre_tournament.values
    hosts = set(t[t.host==1].team_name)
    GROUPS = m.groupby("g").apply(lambda d: sorted(set(d.home_team_name)|set(d.away_team_name))).to_dict()
    if len(GROUPS) != 8: return None

    Sn = Sv[None,:] + rng.normal(0, SIGMA_S, (N,nt))
    fixtures = [(r.home_team_name, r.away_team_name) for _,r in m.iterrows()]
    pts=np.zeros((N,nt),np.int32); gd=np.zeros((N,nt),np.int32); gf=np.zeros((N,nt),np.int32)
    for h,aw in fixtures:
        ih,ia=IDX[h],IDX[aw]
        d=Sn[:,ih]-Sn[:,ia]
        hh=HADV if h in hosts else 0.0; ha=HADV if aw in hosts else 0.0
        gh=rng.poisson(np.exp(a+w+d+hh)); ga=rng.poisson(np.exp(a+w-d+ha))
        pts[:,ih]+=np.where(gh>ga,3,np.where(gh==ga,1,0)); pts[:,ia]+=np.where(ga>gh,3,np.where(gh==ga,1,0))
        gd[:,ih]+=gh-ga; gd[:,ia]+=ga-gh; gf[:,ih]+=gh; gf[:,ia]+=ga
    key=pts*1e10+(gd+500)*1e6+gf*1e3+elo/3000
    win_g={}; run_g={}
    for g,ts in GROUPS.items():
        ii=np.array([IDX[x] for x in ts]); o=(-key[:,ii]).argsort(1).argsort(1)
        win_g[g]=ii[o.argmin(1)]; run_g[g]=ii[np.abs(o-1).argmin(1)]
    def ko(hi,ai):
        d=Sn[np.arange(N),hi]-Sn[np.arange(N),ai]
        hostv=np.isin(np.array(TEAMS),list(hosts)).astype(float)
        lh=np.exp(a+w+d+hostv[hi]*HADV); la=np.exp(a+w-d+hostv[ai]*HADV)
        gh,ga=rng.poisson(lh),rng.poisson(la); eh,ea=rng.poisson(lh/3),rng.poisson(la/3)
        pen=rng.random(N)<1/(1+10**(-(d/b*100)*0.5/400))
        wh=np.where(gh!=ga,gh>ga,np.where(eh!=ea,eh>ea,pen))
        return np.where(wh,hi,ai)
    r16w=[ko(win_g[s1[1]] if s1[0]=="1" else run_g[s1[1]],
             win_g[s2[1]] if s2[0]=="1" else run_g[s2[1]]) for s1,s2 in R16]
    qfw=[ko(r16w[x],r16w[y]) for x,y in QFp]
    sfw=[ko(qfw[x],qfw[y]) for x,y in SFp]
    champ=ko(sfw[0],sfw[1])
    pwin=np.bincount(champ,minlength=nt)/N
    out=pd.DataFrame({"team":TEAMS,"p_win":pwin*100,"elo":elo}).sort_values("p_win",ascending=False).reset_index(drop=True)
    return out, use_mv

print(f"{'Anno':<6}{'Favorito modello':<18}{'P':>6}  {'Vincitore reale':<16}{'P(modello)':>10}{'rank':>6}  {'finalista reale':<14}{'rank':>5}")
print("─"*92)
summary=[]
for yr,(winner,finalist) in REAL.items():
    r=run_year(yr)
    if r is None: print(f"{yr}: dati incompleti"); continue
    out,use_mv=r
    fav=out.iloc[0]
    wrow=out[out.team==winner]; frow=out[out.team==finalist]
    wr=int(wrow.index[0])+1 if len(wrow) else None; wp=wrow.p_win.iloc[0] if len(wrow) else 0
    fr=int(frow.index[0])+1 if len(frow) else None
    summary.append({"anno":yr,"fav":fav.team,"fav_p":fav.p_win,"winner":winner,"win_p":wp,"win_rank":wr,
                    "fin_rank":fr,"mv":use_mv,"top1":out.iloc[0].team==winner,
                    "top3":wr<=3 if wr else False,"top5":wr<=5 if wr else False})
    print(f"{yr:<6}{fav.team:<18}{fav.p_win:>5.1f}%  {winner:<16}{wp:>9.1f}%{wr:>6}  {finalist:<14}{fr:>5}")
s=pd.DataFrame(summary)
print("─"*92)
print(f"\nVincitore reale nel TOP-1 del modello: {s.top1.sum()}/7  |  TOP-3: {s.top3.sum()}/7  |  TOP-5: {s.top5.sum()}/7")
print(f"P media assegnata al vincitore reale: {s.win_p.mean():.1f}%  (caso: 3.1%; bookmaker tipico: ~12-15%)")
print(f"Rank medio del vincitore reale: {s.win_rank.mean():.1f} su 32")
s.to_csv(f"{BASE}/backtest_summary.csv", index=False)
print("\n✓ backtest_summary.csv")
