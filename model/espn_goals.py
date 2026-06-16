"""Stadio 2 — gol GIÀ segnati nel Mondiale in corso, da ESPN (per marcatore).
Scrive data/live_goals.json {nome_normalizzato: gol}. Esclude gli autogol.
Lo chiama anche l'auto-update così i gol si sommano da soli dopo ogni partita."""
import urllib.request, json, os, unicodedata, re, datetime
BASE=os.path.dirname(os.path.abspath(__file__))
def clean(s):
    s=re.sub(r'\(.*?\)','',str(s)); s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
    return re.sub(r'[^a-z ]','',s).strip()
def get(u):
    return json.load(urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'Mozilla/5.0'}),timeout=25))

goals={}
d=datetime.date(2026,6,11); today=datetime.date.today()
while d<=today:
    ds=d.strftime('%Y%m%d')
    try: sb=get(f'https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates={ds}')
    except Exception: sb={'events':[]}
    for e in sb.get('events',[]):
        st=e.get('status',{}).get('type',{}).get('state','')
        if st!='post': continue
        try: sm=get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/summary?event={e['id']}")
        except Exception: continue
        for p in sm.get('keyEvents',[]):
            tt=p.get('type',{}).get('text','')
            if not tt.startswith('Goal'): continue
            if 'own' in tt.lower() or 'own goal' in p.get('text','').lower(): continue
            parts=p.get('participants') or []
            if parts:
                nm=parts[0].get('athlete',{}).get('displayName')
                if nm: goals[clean(nm)]=goals.get(clean(nm),0)+1
    d+=datetime.timedelta(days=1)

json.dump(goals, open(os.path.join(BASE,'data','live_goals.json'),'w'))
tot=sum(goals.values())
top=sorted(goals.items(),key=lambda x:-x[1])[:12]
print(f"✓ data/live_goals.json — {tot} gol di {len(goals)} marcatori")
print("Top marcatori finora:", ', '.join(f'{k} ({v})' for k,v in top))
