"""
═══════════════════════════════════════════════════════════════════════════
  CAPOCANNONIERE v2 — Motore TASSI + MINUTI ATTESI (per giocatore, rosa 2026)
═══════════════════════════════════════════════════════════════════════════
npxG/90 (la finalizzazione non si ripete) + shrinkage Gamma-Poisson per ruolo
+ club&nazionale pesati per esposizione, RIGORI a parte (solo al rigorista
designato per nazionale), e MINUTI ATTESI dal ruolo reale in nazionale
(fallback: club). Il gol atteso non è il rate: è rate × minuti × (poi, partite).
Output: data/player_rates.csv  →  exp_g_match (gol attesi per partita giocata).
"""
import sqlite3, pandas as pd, numpy as np, unicodedata, re, os
BASE = os.path.dirname(os.path.abspath(__file__))
BS   = os.environ.get("WC_BOXSCORE") or os.path.join(BASE,"..","..","..","Football BoxScore","output")
SEASONS=['2023-2024','2024-2025','2025-2026','2023','2024','2025','2026']
PEN_XG=0.78; PEN_CONV=0.81

def clean(s):  # via "(captain)" e simili, poi normalizza accenti
    s=re.sub(r'\(.*?\)','',str(s))
    s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
    return re.sub(r'[^a-z ]','',s).strip()

def pull(dbpath):
    con=sqlite3.connect(dbpath)
    q=f"""select p.player_name, p.usual_position pos, count(*) apps, sum(p.started) nstart,
             sum(p.minutes) mins, sum(p.goals) g, sum(p.npxg) npxg, sum(p.xg) xg, sum(p.shots) sh
          from player_match_stats p join matches m on p.match_id=m.match_id
          where m.season in ({','.join('?'*len(SEASONS))}) and p.minutes>0
          group by p.player_name, p.usual_position"""
    df=pd.read_sql(q,con,params=SEASONS); con.close()
    df['nn']=df.player_name.apply(clean)
    g=df.groupby('nn').agg(apps=('apps','sum'),nstart=('nstart','sum'),mins=('mins','sum'),
        g=('g','sum'),npxg=('npxg','sum'),xg=('xg','sum'),sh=('sh','sum')).reset_index()
    pos=df.dropna(subset=['pos']).groupby('nn').pos.agg(lambda s:s.mode().iloc[0] if len(s.mode()) else None)
    g['pos']=g.nn.map(pos)
    return g

club=pull(os.path.join(BS,'football_boxscore.db'))
nat =pull(os.path.join(BS,'nations_boxscore.db'))

# ── TASSI: pool club+naz (somma = pesa per esposizione, il club domina) ───────
pool=pd.concat([club,nat]).groupby('nn').agg(mins=('mins','sum'),g=('g','sum'),
      npxg=('npxg','sum'),xg=('xg','sum'),sh=('sh','sum')).reset_index()
pool['n90']=pool.mins/90; pool['pen_xg']=(pool.xg-pool.npxg).clip(lower=0)
posmap=pd.concat([club,nat]).dropna(subset=['pos']).groupby('nn').pos.agg(lambda s:s.mode().iloc[0] if len(s.mode()) else '2')
def macro(p): return {'0':'GK','1':'DEF','2':'MID','3':'FWD'}.get(str(p).strip().replace('.0',''),'MID')
pool['role']=pool.nn.map(posmap).apply(macro)

def eb_prior(sub):
    e=sub.n90.values; c=sub.npxg.values; mu=c.sum()/e.sum()
    r=c/np.maximum(e,1e-9); w=e/e.sum()
    between=max(np.sum(w*(r-mu)**2)-mu*np.sum(w/np.maximum(e,1e-9)), mu*0.04)
    beta=mu/between; return mu*beta, beta, mu
for role,sub in pool[pool.n90>=3].groupby('role'):
    a,b,mu=eb_prior(sub)
    pool.loc[sub.index,'op_rate90']=(a+sub.npxg)/(b+sub.n90)
pool['g90']=pool.g/pool.n90
pool['op_rate90']=0.85*pool.op_rate90 + 0.15*(pool.g90-pool.pen_xg/pool.n90).clip(lower=0)  # blend finitura elite
pool['pen_per90']=pool.pen_xg/pool.n90

# ── MINUTI ATTESI: ruolo reale in NAZIONALE, fallback club ────────────────────
nat['pstart']=nat.nstart/nat.apps.clip(lower=1); nat['minpg']=nat.mins/nat.apps.clip(lower=1)
club['pstart']=club.nstart/club.apps.clip(lower=1)
nm=nat.set_index('nn'); cm=club.set_index('nn')
def exp_minutes(nn):
    if nn in nm.index and nm.loc[nn,'apps']>=4:
        ps=nm.loc[nn,'pstart']; return float(np.clip(ps*max(nm.loc[nn,'minpg'],75)+(1-ps)*18,0,92))
    if nn in cm.index and cm.loc[nn,'apps']>=10:        # nessun dato naz → usa titolarità CLUB
        ps=cm.loc[nn,'pstart']; return float(np.clip(ps*85+(1-ps)*20,0,92))
    return None

# ── Aggancio rosa 2026 ────────────────────────────────────────────────────────
sq=pd.read_csv(os.path.join(BASE,'data','squads_2026.csv')); sq['nn']=sq.player.apply(clean)
m=sq.merge(pool[['nn','mins','op_rate90','pen_per90','role','g','npxg']],on='nn',how='left')
ROLEPRIOR={'FW':0.30,'MF':0.12,'DF':0.05,'GK':0.0}
m['op_rate90']=m.op_rate90.fillna(m.pos.map(ROLEPRIOR)).fillna(0.10)
m['mn']=m.mins.fillna(0)
m['exp_min']=m.nn.apply(exp_minutes)
m['exp_min']=m.exp_min.fillna(m.pos.map({'FW':70,'MF':62,'DF':72,'GK':90})).fillna(60)

# ── RIGORISTA designato: 1 per nazionale (max pen_per90, con dati) ────────────
m['pen_per90']=m.pen_per90.fillna(0)
m['is_taker']=False
for team,grp in m.groupby('team'):
    cand=grp[(grp.pen_per90>0.03)&(grp.mn>=600)]
    if len(cand): m.loc[cand.pen_per90.idxmax(),'is_taker']=True
m['pen_rate90']=np.where(m.is_taker, m.pen_per90*(PEN_CONV/PEN_XG), 0.0)
m['exp_g90']=m.op_rate90+m.pen_rate90
m['exp_g_match']=m.exp_g90*(m.exp_min/90.0)
m.to_csv(os.path.join(BASE,'data','player_rates.csv'),index=False)

att=m[m.pos.isin(['FW','MF'])].sort_values('exp_g_match',ascending=False).head(18)
print('═══ GOL ATTESI PER PARTITA (ritmo × minuti reali) — rosa 2026 ═══')
print(f"{'Giocatore':22}{'Naz':12}{'min_att':>8}{'g/90':>7}{'rig':>5}{'g/match':>9}")
for _,r in att.iterrows():
    nm_=re.sub(r'\(captain\)','',str(r.player)).strip()
    print(f"{nm_[:21]:22}{str(r.team)[:11]:12}{r.exp_min:>8.0f}{r.exp_g90:>7.3f}{'  R' if r.is_taker else '':>5}{r.exp_g_match:>9.3f}")
print('\nControllo nomi chiave:')
for n in ['Kylian Mbappé','Harry Kane','Erling Haaland','Gonçalo Ramos','Lionel Messi']:
    r=m[m.nn==clean(n)]
    if len(r): r=r.iloc[0]; print(f"  {n}: min_att {r.exp_min:.0f}, g/90 {r.exp_g90:.3f}, rigorista={r.is_taker} → g/partita {r.exp_g_match:.3f}")
    else: print(f"  {n}: NON MATCHATO")
print('\n✓ data/player_rates.csv')
