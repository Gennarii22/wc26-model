# Mondiale 2026 — Sistema di previsione completo

**Generato l'11 giugno 2026, giorno di apertura del torneo.**
48 squadre · 104 partite · 20.000 simulazioni Monte Carlo · regole FIFA ufficiali.

---

## 1. Sintesi dei risultati

### Probabilità di vincere il Mondiale (top 10)

| # | Squadra | Girone | ELO | P(titolo) | P(finale) | P(semifinale) |
|---|---------|--------|------|-----------|-----------|----------------|
| 1 | **Spagna** | H | 2219 | **34.8%** | 46.5% | 62.8% |
| 2 | Francia | I | 2125 | 14.6% | 24.0% | 41.6% |
| 3 | Inghilterra | L | 2086 | 10.1% | 21.0% | 34.0% |
| 4 | Argentina | J | 2192 | 9.9% | 20.6% | 35.1% |
| 5 | Ecuador | E | 2028 | 5.2% | 11.1% | 23.0% |
| 6 | Portogallo | K | 2043 | 4.5% | 11.2% | 22.1% |
| 7 | Norvegia | I | 1971 | 2.8% | 7.5% | 16.9% |
| 8 | Olanda | F | 2011 | 2.6% | 6.0% | 15.0% |
| 9 | Marocco | C | 2.5% | 6.4% | 14.9% | |
| 10 | Germania | E | 2004 | 1.8% | 5.2% | 12.0% |

### Capocannoniere (Golden Boot)

| # | Giocatore | Squadra | Gol attesi | P(Golden Boot) |
|---|-----------|---------|------------|-----------------|
| 1 | **Harry Kane** | Inghilterra | 7.0 | **28.0%** |
| 2 | Kylian Mbappé | Francia | 6.0 | 16.2% |
| 3 | Lionel Messi | Argentina | 5.8 | 14.1% |
| 4 | Cristiano Ronaldo | Portogallo | 5.3 | 9.2% |
| 5 | Mikel Oyarzabal | Spagna | 5.1 | 8.1% |

Gol del vincitore: **mediana 9** (90° percentile 12) — coerente col benchmark pubblicato (8.4 / 11).

### Partita inaugurale (oggi)
- **Messico–Sudafrica** (Azteca): 1 al 77.8%, risultato più probabile **2-0** (vantaggio casa + altitudine 2.240m)
- **Corea del Sud–Cechia** (Zapopan): equilibrata, 40/28/32, risultato più probabile 1-1

---

## 2. Architettura del modello (stato dell'arte + estensioni)

La ricerca approfondita (letteratura accademica: Groll/Schauberger/Zeileis; Klement; Dixon-Coles; Nate Silver "PELE") indica che la pipeline vincente è: **rating di forma recente + valore rosa + covariate strutturali → Poisson sui gol → Monte Carlo**. È esattamente ciò che abbiamo costruito, con i nostri dati:

**① Modello partita — Poisson sui gol** (allenato su 32.282 partite internazionali 1990→giu 2026):
```
log λ(gol) = 0.091 + 0.184·ΔELO/100 + 0.184·casa(+100 ELO eq., solo nel proprio paese) + 0.078·Mondiale
```
**② Correzioni oltre l'ELO** (stimate sui Mondiali 2006-2022, alla Klement ma più ricche):

| Variabile | Effetto (≈ ELO equivalenti) |
|---|---|
| Valore rosa Transfermarkt (log) | **+33 per unità** |
| Età media rosa | **−46 per anno in più** (giovani meglio) |
| PIL pro capite (Klement) | +14 per unità log |
| Popolazione (Klement) | −7 (trascurabile, conferma letteratura) |

**③ Incertezza di forza**: σ = 41 punti ELO per squadra/simulazione (stimata dalla deriva ELO storica nei tornei, std 59 × 70%) — errore *correlato* tra le partite della stessa squadra.

**④ Torneo esatto**: 72 partite con sede reale (vantaggio casa solo nel proprio paese; Azteca/Guadalajara/Monterrey per il Messico), tiebreaker FIFA Art. 13 (**head-to-head prima della differenza reti** — novità 2026, niente sorteggio: decide il ranking), migliori 8 terze, assegnazione terze nel tabellone con la **tabella ufficiale FIFA Annexe C (tutte le 495 combinazioni)**, tabellone R32→finale con sedi ufficiali, supplementari (λ/3) e rigori (50% ± tilt ELO).

**⑤ Capocannoniere**: gol di squadra per simulazione distribuiti ai 1.247 giocatori delle rose ufficiali via multinomiale; quota-giocatore = rate di segnatura in nazionale (gol/presenze, shrinkato per ruolo: prior FW 2.0/9, MF 0.8/11, DF 0.25/14) × proxy titolarità (caps relativi).

---

## 3. Validazione (onesta)

- **Leave-one-tournament-out sui Mondiali 2010-2022**: log-loss 1X2 medio **0.966** vs 0.980 dell'ELO puro (+1.4%, batte l'ELO in 3 tornei su 4).
- **Calibrazione favoriti**: nei bin 50-65% e 65-80% di P(vittoria) predetta, la frequenza reale è 64% e 72% — il modello semmai *sottostima* i favoriti.
- **Il potere predittivo dell'ELO non si attenua tra top team**: shrink ottimale k=1.00 anche limitando a partite con entrambe le squadre sopra 1900 ELO (n=108). Questo giustifica il nostro 34.8% sulla Spagna.

### Confronto con i benchmark pubblici 2026

| Fonte | Favorita | P(titolo) |
|---|---|---|
| **Questo modello** | Spagna | **34.8%** |
| Zeileis/Groll (accademico) | Spagna | 14.5% |
| Nate Silver (PELE) | Spagna/Francia | ~16% |
| Klement (macro) | **Olanda** campione | — |

La nostra Spagna è più alta di tutti: il distacco ELO (+94 sul 2°) più il valore rosa più alto e la rosa giovane si compongono su 7 turni. I bookmaker comprimono i favoriti (margine, diversificazione). **Per il tuo trading: se il mercato quota la Spagna sopra ~2.9, il modello vede valore enorme; viceversa, il modello "ama" meno di tutti i benchmark le outsider di fascia media.**

Nota di colore: il nostro modello dà l'**Ecuador 5° favorito (5.2%)** — ELO 2028 (più di Germania e Olanda), rosa giovanissima (26.1 anni). È la "scommessa caratteristica" del modello rispetto al consenso. L'Olanda di Klement per noi è all'8° posto (2.6%).

---

## 4. File prodotti

| File | Contenuto |
|---|---|
| `dashboard.html` | Dashboard interattiva: Antepost (con **quote a mano** → Edge/EV), Gironi, 72 Partite, Capocannoniere |
| `team_probs.csv` | Probabilità complete per le 48 squadre |
| `match_predictions.csv` | 1X2 + risultato più probabile + xG per le 72 partite dei gironi |
| `top_scorer.csv` | Tutti i 1.247 giocatori con gol attesi e P(Golden Boot) |
| `train_match_model.py` / `simulate.py` / `top_scorer.py` | Pipeline riproducibile (seed fissi) |
| `match_model.pkl` | Modello allenato |

---

## 5. Limiti dichiarati

1. **Spagna 34.8%** è la lettura più aggressiva tra i modelli pubblici — guidata dai dati, ma su un solo torneo il consenso può aver ragione: usa la divergenza come segnale, non come certezza.
2. **Capocannoniere**: non vede rigoristi designati, minutaggio reale, né il declino dei veterani (Messi 38, Ronaldo 41 sono probabilmente sovrastimati).
3. Tiebreaker: head-to-head esatto per le coppie; per gli arrivi a 3+ squadre a pari punti usa DR/GF totali (approssimazione, frequenza bassa).
4. Niente infortuni/squalifiche in corso di torneo; le rose sono quelle ufficiali al via.
5. Il modello non si aggiorna ancora partita-per-partita (possibile estensione: ricalcolo dopo ogni giornata dei gironi).
