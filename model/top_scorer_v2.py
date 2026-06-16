"""
═══════════════════════════════════════════════════════════════════════════
  CAPOCANNONIERE v2 — Stadio 3: simulazione Golden Boot (argmax Monte Carlo)
═══════════════════════════════════════════════════════════════════════════
P(capocannoniere) = P(segna più di tutti). Niente formula: Monte Carlo.
Per ogni torneo simulato, ogni squadra gioca M partite (3 gironi + KO campionati
dalle sue prob di avanzamento), ogni giocatore segna Poisson(M × gol/partita)
+ i gol GIÀ segnati nel torneo (ESPN). Argmax → capocannoniere di quel torneo.
Driver dominante = quanto avanza la squadra, esattamente come da ricerca.
"""
import pandas as pd, numpy as np, os, json
BASE=os.path.dirname(os.path.abspath(__file__)); RNG=np.random.default_rng(42); N=20000
pr=pd.read_csv(os.path.join(BASE,'data','player_rates.csv'))
tp=pd.read_csv(os.path.join(BASE,'team_probs.csv'))

# gol GIÀ segnati nel Mondiale in corso (da ESPN, se presente; vuoto = parte da 0)
live={}
lp=os.path.join(BASE,'data','live_goals.json')
if os.path.exists(lp): live=json.load(open(lp))

# candidati: chi può segnare (riduce il calcolo, tiene i marcatori)
import unicodedata,re
def clean(s):
    s=re.sub(r'\(.*?\)','',str(s)); s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
    return re.sub(r'[^a-z ]','',s).strip()
pr['nn']=pr.player.apply(clean)
cand=pr[(pr.exp_g_match>0.04)].copy().reset_index(drop=True)
cand['live']=cand.nn.map(lambda k: live.get(k,0)).fillna(0).astype(float)

# prob di GIOCARE ogni turno KO per squadra (reach = gioca quel match)
RP=['p_r32','p_r16','p_qf','p_sf','p_final']
teams=tp.team.tolist(); tidx={t:i for i,t in enumerate(teams)}
probs=tp[RP].values/100.0                                   # (nteams, 5)
pti=cand.team.map(tidx).fillna(-1).astype(int).values        # player→team idx
valid=pti>=0
cand=cand[valid].reset_index(drop=True); pti=pti[valid]
egm=cand.exp_g_match.values; livev=cand.live.values
np_=len(cand)

win=np.zeros(np_); goalsum=np.zeros(np_)
CH=4000
for s0 in range(0,N,CH):
    n=min(CH,N-s0)
    U=RNG.random((n,len(teams),1))
    M=3+(U<probs[None,:,:]).sum(2)                           # (n, nteams) partite per squadra
    lam=M[:,pti]*egm[None,:]                                 # (n, np) λ per giocatore
    g=RNG.poisson(lam).astype(np.int32)+livev[None,:].astype(np.int32)
    w=g.argmax(1)
    np.add.at(win, w, 1)
    goalsum+=g.sum(0)
cand['p_gb']=win/N*100
cand['exp_goals']=goalsum/N
out=cand.sort_values('p_gb',ascending=False)
print('═══ GOLDEN BOOT v2 — P(capocannoniere) su 20.000 tornei ═══')
print(f"{'Giocatore':22}{'Naz':12}{'g/match':>8}{'rig':>5}{'gol attesi':>11}{'P(GB)':>8}")
for _,r in out.head(18).iterrows():
    nm=re.sub(r'\(captain\)','',str(r.player)).strip()
    print(f"{nm[:21]:22}{str(r.team)[:11]:12}{r.exp_g_match:>8.3f}{'  R' if r.is_taker else '':>5}{r.exp_goals:>11.2f}{r.p_gb:>7.1f}%")
out[['player','team','exp_g_match','is_taker','exp_goals','p_gb']].to_csv(os.path.join(BASE,'data','golden_boot_v2.csv'),index=False)
print(f"\nlive goals caricati: {sum(live.values()) if live else 0} | ✓ data/golden_boot_v2.csv")
