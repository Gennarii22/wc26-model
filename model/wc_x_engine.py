"""
WC X ENGINE (cloud) — genera post X dai dati del modello e li pubblica.
Riscritto con le 6 REGOLE (feedback Gennaro, 20/06/2026):
  1. LINK al modello SEMPRE  -> footer fisso mondiale.gpancia.com in ogni post.
  2. TEMPISMO: post-partita solo per match finiti da POCO (finestra recency), mai 8h/giorni dopo.
  3. NIENTE post-metodo ("rigira 20k volte / no vibes") e niente ripetizioni (dedup su tipo+team).
  4. NIENTE certezze matematiche spacciate per previsioni (no 100% gruppo da già-qualificata, no eliminazione aritmetica).
  5. UN insight specifico per post, sempre legato a un risultato reale appena avvenuto.
  6. VOCE documentario, niente hype (brand).
Se non c'e' un edge reale e fresco, NON si posta nulla (meglio il silenzio del filler).

Chiavi via env (GitHub Secrets): GEMINI_API_KEY, X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET
Uso locale:  python wc_x_engine.py --n 2 [--post] [--prematch] [--dry]
"""
import os, json, sys, urllib.request, datetime as _dt

BASE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(BASE, "x_posted_log.json")
GEMINI_MODELS = ["gemini-flash-latest", "gemini-2.5-flash"]
LINK = "mondiale.gpancia.com"
RECENCY_MIN = 170          # un match conta come "appena finito" se il fischio d'inizio
                           # e' tra 105 e 170 min fa (cioe' finito da ~0-65 min). REGOLA 2.
RECENCY_MIN_LO = 105

def load_env():
    for p in [os.path.join(BASE, ".env"), os.path.join(BASE, "..", ".env")]:
        if os.path.exists(p):
            for line in open(p):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
load_env()
import pandas as pd

_ALIAS = {"Czechia": "Czech Republic", "USA": "United States", "Türkiye": "Turkey",
          "Cabo Verde": "Cape Verde", "Congo DR": "DR Congo", "Côte d'Ivoire": "Ivory Coast",
          "Curacao": "Curaçao", "Bosnia-Herzegovina": "Bosnia and Herzegovina", "Korea Republic": "South Korea"}
def _canon(n): return _ALIAS.get(n, n)
def _tag(name): return "#" + "".join(w.capitalize() for w in str(name).replace("-", " ").split())

# ── REGOLA 2: match finiti DA POCO (da ESPN, via orario di kickoff) ──────────
def recent_finals(max_age=RECENCY_MIN, min_age=RECENCY_MIN_LO):
    """Ritorna [(home, away, hs, as_, kickoff)] dei match conclusi da poco."""
    now = _dt.datetime.now(_dt.timezone.utc); out = []
    for off in (0, -1):
        d = (now + _dt.timedelta(days=off)).date()
        u = f"https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates={d.strftime('%Y%m%d')}"
        try:
            data = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=20))
        except Exception:
            continue
        for e in data.get("events", []):
            c = e["competitions"][0]
            if c["status"]["type"]["name"] not in ("STATUS_FULL_TIME", "STATUS_POST"):
                continue
            try:
                kt = _dt.datetime.fromisoformat(e["date"].replace("Z", "+00:00"))
            except Exception:
                continue
            age = (now - kt).total_seconds() / 60
            if not (min_age <= age <= max_age):
                continue
            comp = {x["homeAway"]: x for x in c["competitors"]}
            try:
                h, a = _canon(comp["home"]["team"]["displayName"]), _canon(comp["away"]["team"]["displayName"])
                hs, as_ = int(comp["home"].get("score", 0)), int(comp["away"].get("score", 0))
            except Exception:
                continue
            out.append((h, a, hs, as_, kt))
    return out

def load_facts():
    a = pd.read_csv(f"{BASE}/team_probs.csv").set_index("team")
    try:
        b = pd.read_csv(f"{BASE}/team_probs_before.csv").set_index("team")
    except Exception:
        b = a.copy()
    res = pd.read_csv(f"{BASE}/results_2026.csv")
    res = res[res.status.astype(str).str.contains("FULL|FINAL", na=False)]
    def non_wins(team):
        n = 0
        for _, r in res[(res.home == team) | (res.away == team)].iterrows():
            if r.home == team and r.home_score <= r.away_score: n += 1
            if r.away == team and r.away_score <= r.home_score: n += 1
        return n
    d = a.join(b, rsuffix="_b")
    for c in ["p_win", "p_win_group"]:
        if c in a and c + "_b" in d: d[c + "_d"] = d[c] - d[c + "_b"]
    return dict(a=a, b=b, d=d, res=res, non_wins=non_wins)

# ── REGOLA 5: un insight per post, SEMPRE legato a un match appena finito ────
def build_stories(F):
    a, d = F["a"], F["d"]
    finals = recent_finals()
    fresh_teams = {t for (h, aw, hs, as_, kt) in finals for t in (h, aw)}
    if not fresh_teams:
        return []                         # REGOLA 2: nessun match fresco -> niente post
    S = []
    # collapse / riser di probabilita' gruppo, SOLO per chi ha appena giocato
    if "p_win_group_d" in d:
        for team in fresh_teams:
            if team not in d.index: continue
            row = d.loc[team]
            now_p, was_p, delta = row["p_win_group"], row.get("p_win_group_b", row["p_win_group"]), row.get("p_win_group_d", 0)
            # REGOLA 4: salta le certezze aritmetiche (gia' qualificata / eliminata)
            if now_p >= 97 or now_p <= 3:
                continue
            if delta <= -12:
                S.append(dict(type="collapse", team=team, tag=_tag(team),
                    fact=f"{team} group-win probability fell from {was_p:.0f}% to {now_p:.0f}% after today's result.",
                    brief="One result reshuffles every path: lead on the size of the drop, sober tone."))
            elif delta >= 12:
                S.append(dict(type="riser", team=team, tag=_tag(team),
                    fact=f"{team} group-win probability climbed from {was_p:.0f}% to {now_p:.0f}% after today's result.",
                    brief="A team the model just promoted that few are discussing. Curiosity, no hype."))
    # value upset: rosa molto piu' costosa che NON vince, nel match appena finito
    for (h, aw, hs, as_, kt) in finals:
        for hi, lo, sh, sl in [(h, aw, hs, as_), (aw, h, as_, hs)]:
            if hi in a.index and lo in a.index:
                mvh, mvl = a.loc[hi, "mv_meur"], a.loc[lo, "mv_meur"]
                if mvh >= 3 * max(mvl, 1) and sl >= sh and mvh > 300:
                    S.append(dict(type="value_upset", team=lo, tag=_tag(lo),
                        fact=f"{lo} (squad value EUR {mvl:.0f}M) held or beat {hi} (EUR {mvh:.0f}M). Final {h} {hs}-{as_} {aw}.",
                        brief="What squad value really buys at a World Cup, using this exact mismatch. A question, not a boast."))
    # favorita che scivola, SOLO se ha appena giocato
    fav = a.sort_values("p_win", ascending=False).head(2)
    for team in fav.index:
        if team not in fresh_teams: continue
        nw = F["non_wins"](team)
        if nw >= 1:
            S.append(dict(type=f"fav_stumble_{nw}", team=team, tag=_tag(team),
                fact=f"{team} are the model's {'top' if team==fav.index[0] else 'second'} title pick at {a.loc[team,'p_win']:.0f}%, but have dropped points {nw} time(s).",
                brief=("First slip: ask plainly whether they can still win it." if nw == 1
                       else "They keep slipping: question whether they are still the favourite. More doubtful, still sober.")))
    return S

def fresh_stories(stories, n):
    log = json.load(open(LOG)) if os.path.exists(LOG) else []
    used = {(p["type"], p["team"]) for p in log[-40:]}
    fresh = [s for s in stories if (s["type"], s["team"]) not in used]   # REGOLA 3: niente ripetizioni
    return fresh[:n]

# ── REGOLA 6: voce documentario, niente hype. + hook in prima riga. ──────────
STYLE = (
    "You write a single post for X for Gennaro Pancia, who built an AI model that re-simulates the World Cup after every match. "
    "VOICE: documentary, calm, factual, confident. A sharp first line that makes people stop (a number, a fact, or a clean question). "
    "Then one or two short sentences that land the point. NO hype, NO bravado, NO exclamation marks, NO 'no vibes just data', "
    "NO self-congratulation about the model, NO betting or odds language (no bet/odds/value/lock/units/tips). "
    "Sound like a sharp analyst stating something true, not a hype account. English. "
    "HARD LIMITS: max 200 characters. No em-dashes. No arrow characters. No hashtags and NO links (those are added after). "
    "Do not start with 'The model'. Lead with the fact or the hook; the numbers support it."
)
def gemini(prompt):
    key = os.environ.get("GEMINI_API_KEY")
    if not key: return None
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}],
                       "generationConfig": {"temperature": 0.9, "maxOutputTokens": 2048,
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
    """Genera il corpo + appende SEMPRE link e hashtag (REGOLA 1)."""
    prompt = (f"{STYLE}\n\nFACT (true, from the model):\n{story['fact']}\n\n"
              f"ANGLE:\n{story['brief']}\n\nWrite ONLY the post body now (no hashtags, no link).")
    body = gemini(story and prompt)
    if not body: return None
    body = body.replace("—", ",").replace("\n", " ").strip()
    if len(body) > 200:
        body = body[:197].rsplit(" ", 1)[0] + "..."
    tag = story.get("tag", "")
    footer = f"\n\n{LINK}\n#WorldCup2026" + (f" {tag}" if tag else "")
    return body + footer

def post_to_x(text):
    try:
        import tweepy
    except ImportError:
        return False, "tweepy non installato"
    keys = [os.environ.get(k) for k in ("X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET")]
    if not all(keys): return False, "chiavi X mancanti"
    try:
        client = tweepy.Client(consumer_key=keys[0], consumer_secret=keys[1],
                               access_token=keys[2], access_token_secret=keys[3])
        r = client.create_tweet(text=text)
        return True, r.data.get("id")
    except Exception as e:
        return False, str(e)

def fetch_upcoming():
    out = []; now = _dt.datetime.now(_dt.timezone.utc)
    for off in (0, 1):
        d = (now + _dt.timedelta(days=off)).date()
        u = f"https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates={d.strftime('%Y%m%d')}"
        try:
            data = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=20))
        except Exception:
            continue
        for e in data.get("events", []):
            c = e["competitions"][0]
            if c["status"]["type"]["name"] != "STATUS_SCHEDULED": continue
            try:
                kt = _dt.datetime.fromisoformat(e["date"].replace("Z", "+00:00"))
            except Exception:
                continue
            comp = {x["homeAway"]: x["team"]["displayName"] for x in c["competitors"]}
            out.append((kt, _canon(comp.get("home", "")), _canon(comp.get("away", ""))))
    return out

def prematch_stories(lo=20, hi=80):
    try:
        mp = pd.read_csv(f"{BASE}/match_predictions.csv")
        tp = pd.read_csv(f"{BASE}/team_probs.csv").set_index("team")
    except Exception:
        return []
    now = _dt.datetime.now(_dt.timezone.utc); S = []
    for kt, h, a in fetch_upcoming():
        mins = (kt - now).total_seconds() / 60
        if not (lo <= mins <= hi): continue
        row = mp[((mp.home == h) & (mp.away == a)) | ((mp.home == a) & (mp.away == h))]
        if not len(row): continue
        r = row.iloc[0]
        S.append(dict(type="prematch", team=f"{h}_vs_{a}", tag=f"{_tag(h)} {_tag(a)}",
            fact=f"{r.home} vs {r.away} kicks off in about {int(mins)} minutes. Model: {r.home} {r.p1:.0f}%, draw {r.px:.0f}%, {r.away} {r.p2:.0f}%. Most likely score {r.score_ml}.",
            brief="A pre-match post minutes before kickoff. Hook on the lean (clear favourite, coin flip, or a live underdog) or the likely score. Make people want to watch. Do not just list three percentages."))
    return S

def main():
    n = 2; do_post = "--post" in sys.argv; dry = "--dry" in sys.argv
    if "--n" in sys.argv:
        try: n = int(sys.argv[sys.argv.index("--n") + 1])
        except Exception: pass
    if "--prematch" in sys.argv:
        stories = fresh_stories(prematch_stories(), n)
        label = "PRE-MATCH"
    else:
        stories = fresh_stories(build_stories(load_facts()), n)
        label = "POST-MATCH"
    print(f"WC X ENGINE [{label}] — {len(stories)} post candidati")
    if not stories:
        print("Nessun edge fresco: non posto nulla (REGOLA 2/5)."); return
    log = json.load(open(LOG)) if os.path.exists(LOG) else []
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M")
    for i, s in enumerate(stories, 1):
        txt = make_post(s)
        if not txt:
            print(f"[{i}] ({s['type']}) generazione fallita"); continue
        print(f"[{i}] {s['type']} ({len(txt)} char):\n{txt}\n")
        entry = {"ts": stamp, "type": s["type"], "team": s["team"], "text": txt}
        if do_post and not dry:
            ok, info = post_to_x(txt)
            print(f"    X: {'OK id ' + str(info) if ok else 'NO: ' + str(info)}")
            entry["posted"] = bool(ok)
        log.append(entry)
    if not dry:
        json.dump(log, open(LOG, "w"), indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
