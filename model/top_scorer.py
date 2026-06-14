"""
═══════════════════════════════════════════════════════════════════════════
  MONDIALE 2026 — Modello Capocannoniere (Golden Boot)
═══════════════════════════════════════════════════════════════════════════

Architettura (stato dell'arte praticante):
  1. team_goals per simulazione (dai 20k tornei simulati: gironi + stima KO)
  2. quota-gol di ogni giocatore nella squadra: rate di segnatura in nazionale
     (gol/cap shrinkato verso il prior di ruolo) → share multinomiale
  3. per ogni sim: gol_giocatore ~ Multinomial(team_goals, shares)
     → capocannoniere = max; P(Golden Boot) = frequenza

Dati: squads_2026.csv (1.247 giocatori: caps, gol in nazionale, ruolo, età).
"""
import os
import warnings; warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd

RAW = os.environ.get("WC_RAW") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
BASE = os.environ.get("WC_BASE") or os.path.dirname(os.path.abspath(__file__))
RNG = np.random.default_rng(7)

sq = pd.read_csv(f"{RAW}/squads_2026.csv")
team_probs = pd.read_csv(f"{BASE}/team_probs.csv")
team_goals_group = np.load(f"{BASE}/team_goals_group.npy")   # (n_sims, n_teams)
TEAMS = list(pd.read_csv(f"{BASE}/team_probs.csv").sort_index().team) if False else None

# l'ordine delle colonne di team_goals_group = ordine TEAMS del simulatore
import json
TEAMS = json.load(open(f"{BASE}/teams_order.json"))
IDX = {t: i for i, t in enumerate(TEAMS)}
n_sims = team_goals_group.shape[0]

# ── stima gol KO aggiuntivi per squadra/sim ────────────────────────────────
# approssimazione: gol attesi per partita ~ gol_gironi/3; n. partite KO dalla
# progressione media → uso le probabilità di avanzamento per simulare i gol KO
tp = team_probs.set_index("team")
extra_matches_exp = (tp.p_r32/100*0 + tp.p_r16/100 + tp.p_qf/100 + tp.p_sf/100
                     + tp.p_final/100 + (tp.p_r32/100))   # R32 +1, R16 +1, ...
# (R32 giocata da chi si qualifica: +1; poi una partita in più per ogni turno raggiunto)

# ── pesi giocatore ─────────────────────────────────────────────────────────
POS_PRIOR = {"FW": (2.0, 9.0), "MF": (0.8, 11.0), "DF": (0.25, 14.0), "GK": (0.01, 30.0)}
sq["pos"] = sq["pos"].str.upper().str[:2].map(lambda p: p if p in POS_PRIOR else "MF")
sq["caps"] = pd.to_numeric(sq.caps, errors="coerce").fillna(0)
sq["goals"] = pd.to_numeric(sq.goals, errors="coerce").fillna(0)

def rate(row):
    a0, b0 = POS_PRIOR[row.pos]
    return (row.goals + a0) / (row.caps + b0)
sq["rate"] = sq.apply(rate, axis=1)
# proxy titolarità: caps alti = più probabile titolare → peso minuti
sq["min_w"] = np.clip(sq.caps / (sq.groupby("team").caps.transform("max") + 1), 0.25, 1.0)
sq["weight"] = sq.rate * sq.min_w

# normalizza share dentro la squadra
sq["share"] = sq.weight / sq.groupby("team").weight.transform("sum")

# allinea nomi squadra squads ↔ simulatore
fix = {"South Korea":"South Korea","USA":"United States","Czechia":"Czech Republic",
       "Bosnia":"Bosnia and Herzegovina","Ivory Coast":"Ivory Coast","DR Congo":"DR Congo",
       "Cabo Verde":"Cape Verde","Curacao":"Curaçao"}
sq["team_sim"] = sq.team.map(lambda t: fix.get(t, t))
missing = set(sq.team_sim) - set(TEAMS)
if missing: print("⚠ squadre non allineate:", missing)
sq = sq[sq.team_sim.isin(TEAMS)]

# ── simulazione capocannoniere ─────────────────────────────────────────────
print(f"Distribuisco i gol di {n_sims:,} tornei simulati su {len(sq)} giocatori…")
players = sq.reset_index(drop=True)
gb_wins = np.zeros(len(players))
gb_goals_sum = np.zeros(len(players))

# per ogni squadra: matrice share
by_team = {t: players[players.team_sim == t] for t in TEAMS}
ko_extra = {t: float(1 + tp.loc[t, ["p_r16","p_qf","p_sf","p_final"]].sum()/100) if t in tp.index else 1.0 for t in TEAMS}
# fattore: se ti qualifichi giochi almeno R32(+1) e in media ko_extra partite → gol KO ~ gol/partita gironi × partite KO
gpm = team_goals_group.mean(axis=0) / 3.0   # gol/partita medi nei gironi

# campiono in blocco: per ridurre il costo, simulo 20k tornei in batch per squadra
SAMPLE = min(n_sims, 20000)
sel = RNG.choice(n_sims, SAMPLE, replace=False)
player_goals = np.zeros((SAMPLE, len(players)), dtype=np.int16)
for t in TEAMS:
    grp = by_team[t]
    if len(grp) == 0: continue
    ii = grp.index.values
    shares = grp.share.values
    g_group = team_goals_group[sel, IDX[t]]
    # gol KO: Poisson(qualificato? × gol/partita × partite_ko_attese)
    p_qual = tp.loc[t, "p_r32"]/100 if t in tp.index else 0.3
    qual = RNG.random(SAMPLE) < p_qual
    g_ko = RNG.poisson(gpm[IDX[t]] * ko_extra[t], SAMPLE) * qual
    g_tot = (g_group + g_ko).astype(int)
    # multinomial per ogni sim (vettorizzato per valori unici di g_tot)
    for gval in np.unique(g_tot):
        if gval == 0: continue
        mask = g_tot == gval
        draws = RNG.multinomial(gval, shares, size=mask.sum())
        player_goals[np.where(mask)[0][:, None], ii[None, :]] += draws.astype(np.int16)

# golden boot per sim
top = player_goals.max(axis=1)
for s in range(SAMPLE):
    winners = np.where(player_goals[s] == top[s])[0]
    gb_wins[winners] += 1.0 / len(winners)
gb_goals_sum = player_goals.mean(axis=0)

players["p_golden_boot"] = gb_wins / SAMPLE * 100
players["exp_goals"] = gb_goals_sum
players["goals_90pct"] = np.percentile(player_goals, 90, axis=0)
out = players[["player","team_sim","pos","age","caps","goals","share","exp_goals","goals_90pct","p_golden_boot"]] \
    .sort_values("p_golden_boot", ascending=False)
out.to_csv(f"{BASE}/top_scorer.csv", index=False)
print("\nTOP 15 candidati Golden Boot:")
print(out.head(15).to_string(index=False))
print(f"\nGol del vincitore: mediana {np.median(top):.0f}, 90° pct {np.percentile(top,90):.0f}")
print("✓ top_scorer.csv salvato")
