import os, re
"""Compatta i risultati del modello Mondiale in dashboard_data.js per la dashboard."""
import json
import pandas as pd
import numpy as np

BASE = os.environ.get("WC_BASE") or os.path.dirname(os.path.abspath(__file__))

tp = pd.read_csv(f"{BASE}/team_probs.csv")
mp = pd.read_csv(f"{BASE}/match_predictions.csv")
# capocannoniere v2 (golden_boot_v2.csv) + info rosa per età/ruolo/caps
gb = pd.read_csv(f"{BASE}/data/golden_boot_v2.csv")
sqd = pd.read_csv(f"{BASE}/data/squads_2026.csv")[["player","pos","age","caps","goals"]]
ts = gb.merge(sqd, on="player", how="left").sort_values("p_gb", ascending=False)
groups = json.load(open(f"{BASE}/groups_resolved.json"))

out = {"generated": "11 giugno 2026", "teams": [], "groups": {}, "matches": [], "scorers": []}

# snapshot PRE-MONDIALE congelato (giorno-0, prima di ogni risultato)
pre_map = {}
_pre = f"{BASE}/data/pretournament_teams.csv"
if os.path.exists(_pre):
    pdf = pd.read_csv(_pre)
    pre_map = dict(zip(pdf.team, pdf.p_win))

for _, r in tp.iterrows():
    elo_pre = int(r.elo_pre) if "elo_pre" in tp.columns and pd.notna(r.elo_pre) else int(r.elo)
    elo_delta = int(r.elo_delta) if "elo_delta" in tp.columns and pd.notna(r.elo_delta) else 0
    out["teams"].append({"team": r.team, "group": r.group, "elo": int(r.elo),
        "elo_pre": elo_pre, "elo_delta": elo_delta,
        "mv": int(r.mv_meur) if pd.notna(r.mv_meur) else None,
        "p_win_group": round(r.p_win_group, 1), "p_r32": round(r.p_r32, 1),
        "p_r16": round(r.p_r16, 1), "p_qf": round(r.p_qf, 1), "p_sf": round(r.p_sf, 1),
        "p_final": round(r.p_final, 1), "p_win": round(r.p_win, 2),
        "p_win_pre": round(pre_map[r.team], 2) if r.team in pre_map else None})

out["groups"] = groups

for _, r in mp.sort_values("date").iterrows():
    out["matches"].append({"date": r.date, "group": r.group, "home": r.home, "away": r.away,
        "city": r.city, "venue": r.venue, "p1": r.p1, "px": r.px, "p2": r.p2,
        "score": r.score_ml, "lh": r.lh, "la": r.la})

for _, r in ts.head(40).iterrows():
    nm = re.sub(r'\s*\(captain\)', '', str(r.player)).strip()
    out["scorers"].append({"player": nm, "team": r.team, "pos": r.pos,
        "age": int(r.age) if pd.notna(r.age) else None,
        "caps": int(r.caps) if pd.notna(r.caps) else 0,
        "goals_nat": int(r.goals) if pd.notna(r.goals) else 0,
        "exp_goals": round(r.exp_goals, 2), "p90": 0,
        "p_gb": round(r.p_gb, 1)})

with open(f"{BASE}/dashboard_data.js", "w") as f:
    f.write("window.WC = " + json.dumps(out, ensure_ascii=False) + ";")
print(f"✓ dashboard_data.js — {len(out['teams'])} squadre, {len(out['matches'])} partite, {len(out['scorers'])} bomber")
