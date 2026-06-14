import os
"""Compatta i risultati del modello Mondiale in dashboard_data.js per la dashboard."""
import json
import pandas as pd
import numpy as np

BASE = os.environ.get("WC_BASE") or os.path.dirname(os.path.abspath(__file__))

tp = pd.read_csv(f"{BASE}/team_probs.csv")
mp = pd.read_csv(f"{BASE}/match_predictions.csv")
ts = pd.read_csv(f"{BASE}/top_scorer.csv")
groups = json.load(open(f"{BASE}/groups_resolved.json"))

out = {"generated": "11 giugno 2026", "teams": [], "groups": {}, "matches": [], "scorers": []}

for _, r in tp.iterrows():
    out["teams"].append({"team": r.team, "group": r.group, "elo": int(r.elo),
        "mv": int(r.mv_meur) if pd.notna(r.mv_meur) else None,
        "p_win_group": round(r.p_win_group, 1), "p_r32": round(r.p_r32, 1),
        "p_r16": round(r.p_r16, 1), "p_qf": round(r.p_qf, 1), "p_sf": round(r.p_sf, 1),
        "p_final": round(r.p_final, 1), "p_win": round(r.p_win, 2)})

out["groups"] = groups

for _, r in mp.sort_values("date").iterrows():
    out["matches"].append({"date": r.date, "group": r.group, "home": r.home, "away": r.away,
        "city": r.city, "venue": r.venue, "p1": r.p1, "px": r.px, "p2": r.p2,
        "score": r.score_ml, "lh": r.lh, "la": r.la})

for _, r in ts.head(40).iterrows():
    out["scorers"].append({"player": r.player, "team": r.team_sim, "pos": r.pos,
        "age": int(r.age) if pd.notna(r.age) else None, "caps": int(r.caps), "goals_nat": int(r.goals),
        "exp_goals": round(r.exp_goals, 2), "p90": round(r.goals_90pct, 0),
        "p_gb": round(r.p_golden_boot, 1)})

with open(f"{BASE}/dashboard_data.js", "w") as f:
    f.write("window.WC = " + json.dumps(out, ensure_ascii=False) + ";")
print(f"✓ dashboard_data.js — {len(out['teams'])} squadre, {len(out['matches'])} partite, {len(out['scorers'])} bomber")
