# Mondiale 2026 — Go-Live (3 passi)

## 1. Email → Google Sheet (5 min)
Segui le istruzioni in `site/email_apps_script.gs` (in cima al file):
crea il foglio, incolla lo script, fai il deploy come Web App ("Chiunque"),
copia l'URL `/exec` e incollalo in `site/index.html` al posto di
`PASTE_APPS_SCRIPT_URL_HERE`.

## 2. Pubblica su Netlify (5 min)
- Vai su app.netlify.com → "Add new site" → "Deploy manually".
- Trascina la cartella **`site/`**. Online subito su un URL `*.netlify.app`.
- (Aggiorna `index.html` con l'URL Apps Script PRIMA di trascinare, o ri-trascini dopo.)

## 3. Dominio gpancia.com (10 min)
- Netlify → Site settings → Domain management → Add custom domain.
- Consigliato un sottodominio: **mondiale.gpancia.com**.
- Netlify ti dà un record DNS (CNAME): lo aggiungi dal pannello dove gestisci
  i DNS di gpancia.com (registrar/hosting). HTTPS automatico in pochi minuti.

## Aggiornamento (per ora manuale, poi cloud)
Dopo le partite: `./aggiorna_mondiale.sh` → rigenera tutto e aggiorna `site/`.
Poi ri-trascini `site/` su Netlify (o, una volta connesso GitHub, è automatico).

## Prossimo: auto-update cloud (GitHub Actions)
Serve un repo GitHub. Una volta connesso a Netlify, una Action schedulata
gira la pipeline ogni sera e ripubblica da sola (anche a Mac spento).
