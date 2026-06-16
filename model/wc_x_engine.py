"""
WC X ENGINE (cloud) — genera post X dai dati del modello e li pubblica.
Gira nella GitHub Action dopo l'aggiornamento del modello.
Chiavi via env (GitHub Secrets): GEMINI_API_KEY, X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET
Uso locale:  python wc_x_engine.py --n 2 [--post]
"""
import os, json, sys, urllib.request

BASE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(BASE, "x_posted_log.json")
GEMINI_MODELS = ["gemini-flash-latest", "gemini-2.5-flash"]

def load_env():
    # in locale legge eventuali .env; in cloud le chiavi sono già in os.environ (Secrets)
    for p in [os.path.join(BASE, ".env"), os.path.join(BASE, "..", ".env")]:
        if os.path.exists(p):
            for line in open(p):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
load_env()

import pandas as pd

def load_facts():
    a = pd.read_csv(f"{BASE}/team_probs.csv").set_index("team")
    try:
        b = pd.read_csv(f"{BASE}/team_probs_before.csv").set_index("team")
    except Exception:
        b = a.copy()
    res = pd.read_csv(f"{BASE}/results_2026.csv")
    res = res[res.status.astype(str).str.contains("FULL|FINAL", na=False)]
    last_date = res.date.max() if len(res) else None
    today_res = res[res.date == last_date] if last_date else res.iloc[0:0]

    def played(team):
        return res[(res.home == team) | (res.away == team)]
    def non_wins(team):
        n = 0
        for _, r in played(team).iterrows():
            hs, as_ = r.home_score, r.away_score
            if r.home == team and hs <= as_: n += 1
            if r.away == team and as_ <= hs: n += 1
        return n

    d = a.join(b, rsuffix="_b")
    for c in ["p_win", "p_win_group"]:
        if c in a and c + "_b" in d: d[c + "_d"] = d[c] - d[c + "_b"]
    return dict(a=a, b=b, d=d, res=res, today=today_res, last_date=last_date,
                played=played, non_wins=non_wins)

def build_stories(F):
    a, d, today = F["a"], F["d"], F["today"]
    S = []
    if "p_win_group_d" in d:
        col = d.sort_values("p_win_group_d").iloc[0]
        if col["p_win_group_d"] <= -10:
            S.append(dict(type="collapse", team=col.name,
                          fact=f"{col.name} group-win probability fell from {col['p_win_group_b']:.0f}% to {col['p_win_group']:.0f}% after their result.",
                          brief="One result, big collapse. A single match doesn't cost 3 points, it reshuffles every path. Hook on the size of the drop."))
        ris = d.sort_values("p_win_group_d").iloc[-1]
        if ris["p_win_group_d"] >= 10:
            S.append(dict(type="riser", team=ris.name,
                          fact=f"{ris.name} group-win probability jumped from {ris['p_win_group_b']:.0f}% to {ris['p_win_group']:.0f}%.",
                          brief="The team nobody is talking about that the model just promoted. Curiosity hook."))
    for _, r in today.iterrows():
        for hi, lo, hs, ls in [(r.home, r.away, r.home_score, r.away_score),
                               (r.away, r.home, r.away_score, r.home_score)]:
            if hi in a.index and lo in a.index:
                mvh, mvl = a.loc[hi, "mv_meur"], a.loc[lo, "mv_meur"]
                if mvh >= 3 * max(mvl, 1) and ls >= hs and mvh > 300:
                    S.append(dict(type="value_upset", team=lo,
                                  fact=f"{lo} (squad value EUR {mvl:.0f}M) held/beat {hi} (EUR {mvh:.0f}M). Result {r.home} {r.home_score}-{r.away_score} {r.away}.",
                                  brief="Provocative question on how much squad value really matters at a World Cup, using this exact mismatch."))
    fav = a.sort_values("p_win", ascending=False).head(2)
    for team in fav.index:
        nw = F["non_wins"](team)
        if nw >= 1:
            S.append(dict(type=f"fav_stumble_{nw}", team=team,
                          fact=f"{team} are the model's {'top' if team==fav.index[0] else 'second'} title pick at {a.loc[team,'p_win']:.0f}%, but have dropped points {nw} time(s).",
                          brief=("First slip: ask 'can [team] really win this?' with a provocative 'really'."
                                 if nw == 1 else
                                 "They keep slipping: question whether they are still the favourite at all. Sharper, more doubtful tone.")))
    S.append(dict(type="model_meta", team="_model",
                  fact="A model that re-simulates the whole World Cup 20,000 times after every match, conditioned on real results.",
                  brief="Builder angle: what it means to re-simulate after every match. Confidence, not hype."))
    return S

def fresh_stories(stories, n):
    log = json.load(open(LOG)) if os.path.exists(LOG) else []
    used = {(p["type"], p["team"]) for p in log[-30:]}
    fresh = [s for s in stories if (s["type"], s["team"]) not in used]
    pool = fresh if fresh else stories
    return pool[:n]

STYLE = (
    "You write posts for X (Twitter) for Gennaro Pancia, who runs an AI model that simulates the World Cup. "
    "GOAL: ride the live World Cup conversation and get engagement, fast. "
    "VOICE: native to X. Punchy. A hook in the FIRST line that makes people stop scrolling (a bold claim, a sharp number, or a contrarian question). "
    "Short confident sentences. A bit of edge and opinion. Like a smart friend who happens to have a model, not a professor. "
    "NOT formal, NOT an essay, NOT LinkedIn, NOT a tipster, no betting or odds language. "
    "HARD RULES: under 250 characters TOTAL including hashtags. No em-dashes. No arrow characters. Vary structure, sound human not AI. English. "
    "END with 2 to 3 relevant hashtags on their own line: always include #WorldCup2026, plus one team or topic tag (e.g. #Spain, #Ecuador, #football). "
    "Lead with the hook, the model/numbers support it. Do not start with 'The model'."
)
def gemini(prompt):
    key = os.environ.get("GEMINI_API_KEY")
    if not key: return None
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}],
                       "generationConfig": {"temperature": 0.95, "maxOutputTokens": 2048,
                                            "thinkingConfig": {"thinkingBudget": 0}}}).encode()
    for m in GEMINI_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={key}"
        try:
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
            data = json.load(urllib.request.urlopen(req, timeout=45))
            parts = data["candidates"][0]["content"].get("parts")
            if not parts: continue
            txt = "".join(p.get("text", "") for p in parts).strip().strip('"').strip()
            if txt: return txt
        except Exception:
            continue
    return None

def make_post(story):
    prompt = (f"{STYLE}\n\nFACT (true, from the model):\n{story['fact']}\n\n"
              f"ANGLE for this post:\n{story['brief']}\n\nWrite ONE post now. Only the post text.")
    txt = gemini(prompt)
    if txt and len(txt) > 280:
        txt = txt[:277].rsplit(" ", 1)[0] + "..."
    return txt

def post_to_x(text):
    try:
        import tweepy
    except ImportError:
        return False, "tweepy non installato"
    keys = [os.environ.get(k) for k in ("X_API_KEY","X_API_SECRET","X_ACCESS_TOKEN","X_ACCESS_SECRET")]
    if not all(keys): return False, "chiavi X mancanti"
    try:
        client = tweepy.Client(consumer_key=keys[0], consumer_secret=keys[1],
                               access_token=keys[2], access_token_secret=keys[3])
        r = client.create_tweet(text=text)
        return True, r.data.get("id")
    except Exception as e:
        return False, str(e)

def main():
    n = 2; do_post = "--post" in sys.argv
    if "--n" in sys.argv:
        try: n = int(sys.argv[sys.argv.index("--n")+1])
        except Exception: pass
    F = load_facts()
    stories = fresh_stories(build_stories(F), n)
    print(f"WC X ENGINE — risultati al {F['last_date']} — {len(stories)} post")
    log = json.load(open(LOG)) if os.path.exists(LOG) else []
    for i, s in enumerate(stories, 1):
        txt = make_post(s)
        if not txt:
            print(f"[{i}] ({s['type']}) generazione fallita"); continue
        print(f"[{i}] {s['type']} ({len(txt)} char):\n{txt}\n")
        entry = {"date": F["last_date"], "type": s["type"], "team": s["team"], "text": txt}
        if do_post:
            ok, info = post_to_x(txt)
            print(f"    X: {'OK id '+str(info) if ok else 'NO: '+str(info)}")
            entry["posted"] = bool(ok)
        log.append(entry)
    json.dump(log, open(LOG, "w"), indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
