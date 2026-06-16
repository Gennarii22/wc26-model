# Come funziona il modello — tutti i calcoli, passo per passo

Documento di trasparenza totale: la catena che porta da 49.400 partite storiche
a "Spagna 34.8%", con i numeri veri e il backtest storico 1998-2022.

---

## La catena di calcolo in 5 passi

### Passo 1 — L'ELO di ogni nazionale
Calcolato da zero processando in ordine cronologico **49.400 partite internazionali dal 1872 al 9 giugno 2026** con la formula World Football Elo Ratings:

```
attesa    W_e = 1 / (1 + 10^(−(ELO_A − ELO_B + 100·casa)/400))
update    ELO' = ELO + K · G · (risultato − W_e)
```
con K=60 ai Mondiali, 50 continentali, 40 qualificazioni, 20 amichevoli; G = moltiplicatore del margine (1 / 1.5 / 1.75 / +1/8 per gol oltre il 3°). Validato: la top-15 coincide con eloratings.net.

→ L'11 giugno 2026: **Spagna 2219** (1ª), Argentina 2192, Francia 2125, Inghilterra 2086, Brasile 2069, **Ecuador 2028 (8ª)**, Olanda 2011, Germania 2004…

### Passo 2 — Dall'ELO ai gol attesi (Poisson)
Su **32.282 partite internazionali (1990→2026)** ho stimato per massima verosimiglianza:

```
log λ(gol squadra) = 0.0912 + 0.1844·(ΔELO/100) + 0.2829·casa + 0.0776·Mondiale
```
- a parità di ELO, campo neutro: **1.10 gol attesi a testa**
- +100 ELO di vantaggio → i tuoi gol attesi ×1.20, quelli dell'avversario ÷1.20
- vantaggio casa: ×1.33 sui gol (ai Mondiali lo modero a +100 ELO eq., standard letteratura, **solo nelle partite nel proprio paese**)

I gol di una partita escono da due Poisson indipendenti con questi λ. Da lì: P(1), P(X), P(2), P(ogni risultato esatto).

**Esempio reale — Uruguay-Spagna (26/6, Guadalajara):**
λ_Uruguay = 0.62, λ_Spagna = 2.25 → **8.7% / 16.8% / 74.4%**, risultato più probabile 0-2.

### Passo 3 — Le correzioni oltre l'ELO (il pezzo "alla Klement, ma più ricco")
Sui 320 match dei Mondiali 2006-2022 ho stimato quanto le differenze di rosa/macro spiegano i gol **oltre** l'ELO. In punti ELO equivalenti:

| Variabile | Effetto |
|---|---|
| Valore rosa (log, Transfermarkt d'epoca) | **+33 ELO per unità log** |
| Età media della rosa | **−46 ELO per anno in più** |
| PIL pro capite log (Klement) | +14 |
| Popolazione log (Klement) | −7 (≈ niente, conferma la letteratura) |

La forza finale di ogni squadra è S = ELO + correzioni. La classifica S 2026 (ELO-equivalenti relativi):

| | ELO | Valore rosa | Età | **S relativa** |
|---|---|---|---|---|
| Spagna | 2219 | €1.220M | 26.7 | **+446** |
| Francia | 2125 | €1.520M | 27.0 | +348 |
| Inghilterra | 2086 | €1.360M | 27.1 | +298 |
| Argentina | 2192 | €782M | **29.1** | +292 |
| **Ecuador** | 2028 | €369M | **26.1** | **+250** |
| Portogallo | 2043 | €1.010M | 28.0 | +221 |

Nota come l'**Argentina** (ELO 2192!) scivoli al 4° per l'età (29.1 anni = −109 ELO eq. vs Spagna) e come il log comprima le differenze di valore rosa (€369M vs €1.220M = solo −39 ELO eq.).

### Passo 4 — L'incertezza sulla forza
La forza pre-torneo è una stima: forma, infortuni, sorprese. Ho misurato la **deriva ELO storica** durante i Mondiali (224 squadre-torneo): std = 59 punti. Ne uso il 70% (il resto è fortuna spicciola già nel Poisson): in ogni simulazione la forza di ogni squadra viene perturbata di **σ = 41 ELO**, in modo **correlato** su tutte le sue partite. È ciò che allarga le code (senza, la Spagna sarebbe ancora più alta).

### Passo 5 — 20.000 tornei simulati con le regole FIFA esatte
72 partite dei gironi con sede reale (vantaggio casa solo in patria, Azteca compresa) → classifiche con i tiebreaker 2026 (head-to-head prima della differenza reti, ranking come ultimo criterio — mai sorteggio) → migliori 8 terze → assegnazione nel tabellone con la **tabella ufficiale FIFA Annexe C (495 combinazioni)** → R32…finale con supplementari (λ/3) e rigori (50% ± tilt ELO).

P(titolo) = quante volte su 20.000 alzi la coppa.

---

## Perché la Spagna è al 34.8% (e non al 15% dei bookmaker)

Il 34.8% non è un numero "scelto": è il prodotto di 7 passaggi, ognuno ragionevole:

| Passaggio | P | P condizionata al precedente |
|---|---|---|
| Vince il girone H | 89.5% | — |
| Supera il R32 | 86.4% | (vs una terza: ~93%) |
| Ottavi → Quarti | 72.7% | 84% |
| Quarti → Semi | 62.8% | 86% |
| Semi → Finale | 46.5% | 74% |
| **Vince la finale** | **34.8%** | 75% |

Nessuna singola riga è folle — il girone H ha Capo Verde e Arabia Saudita (due delle più deboli del torneo), e ogni singola P condizionata è quella di un grande favorito contro avversari mediamente più deboli di lui di 150-250 ELO. **La differenza col mercato sta nella composizione**: i bookmaker comprimono i favoriti (margine ~15-20% sull'antepost + diversificazione del pubblico).

Tre verifiche fatte apposta per la tua obiezione:
1. **Calibrazione per-partita**: nei Mondiali 1998-2022, quando il modello dà al favorito il 50-65%, quello vince il **63.9%** delle volte (semmai sottostima).
2. **L'ELO non perde potere tra top team**: shrink ottimale k = 1.00 anche restringendo alle 108 partite con entrambe sopra 2000... cioè proprio le partite da cui passa il titolo.
3. **Precedente storico**: il backtest 2010 dà **Spagna 41.9%** pre-torneo — più estremo di oggi. La Spagna **vinse**.

## Perché l'Ecuador è 5° (4.7-5.2%)

Tre fattori, tutti verificabili:
1. **L'ELO 2028 è guadagnato sul campo.** Ultime 20 partite: **8V-11N-1P**, con vittoria sull'**Argentina** (1-0, set 2025), su Colombia, e pareggi con Brasile (×2), Olanda, Uruguay, Marocco, Messico. Una sola sconfitta in 21 mesi. È la miglior difesa del Sudamerica.
2. **Rosa giovanissima** (26.1 anni, la penalità-età più bassa tra le big) — e il valore rosa, in log, lo penalizza poco.
3. **Girone E morbido + tabellone**: Germania a ELO 2004 (storicamente debole), Costa d'Avorio, Curaçao → 54% di vincere il girone, e da 1E si pesca una terza al R32.

**Lettura onesta**: 11 pareggi su 20 dicono che è una squadra che non perde ma nemmeno stravince — nel KO finirebbe spesso ai rigori (50/50). Il mercato la quota ~50-66: la distanza col nostro 5% è la divergenza più "caratteristica" del modello. Per il tuo trading è il caso da monitorare, non necessariamente da giocare subito.

---

## L'affidabilità nel tempo: il backtest 1998-2022

Per ogni edizione ho fatto girare il modello **con i soli dati pre-torneo dell'epoca** (10.000 sim, tabellone reale a 32):

| Anno | Favorito del modello | Vincitore reale | P data al vincitore | Suo rank |
|---|---|---|---|---|
| 1998 | Brasile 26.1% | Francia | 13.4% | **3°** |
| 2002 | Francia 29.2% | Brasile | 3.0% | 8° |
| 2006 | Inghilterra 20.4% | Italia | 2.9% | 9° |
| 2010 | **Spagna 41.9%** | **Spagna** ✓ | **41.9%** | **1°** |
| 2014 | Brasile 24.9% | Germania | 24.8% | **2°** |
| 2018 | Germania 22.4% | Francia | 15.5% | **3°** |
| 2022 | Spagna 17.7% | Argentina | 16.3% | **3°** |

**Sintesi:**
- Vincitore reale nella **top-3 del modello: 5 volte su 7** · top-1: 1/7 · rank medio 4.1 su 32
- **P media assegnata al vincitore reale: 16.8%** — contro il 3.1% del caso e il ~12-15% che i bookmaker dell'epoca davano agli stessi vincitori. Il modello retrodice **al livello del mercato o meglio**.
- I 2 buchi sono i Mondiali più caotici di sempre: 2002 (flop di Francia e Argentina, Ronaldo) e 2006 (l'Italia di Calciopoli, vincitrice da non-favorita).
- Il favorito del modello ha vinto 1 volta su 7 con P media del 26% → attesi 1.8 successi, osservato 1: **nessuna sovraconfidenza statisticamente rilevabile** (con n=7 è dentro il rumore).

**Caveat onesti:** per il 2006-2022 i coefficienti delle correzioni (valore rosa, età) sono stimati sugli stessi anni → quei backtest hanno una componente in-sample; 1998 e 2002 (solo ELO) sono puliti al 100%. E sette edizioni sono poche: il backtest dice che il modello è *serio*, non che è infallibile.

---

## Il verdetto per come lo usi tu

Il modello produce probabilità **decision-grade**: calibrate per-partita, retrodittive al livello dei bookmaker, costruite su regole FIFA esatte. La Spagna al 34.8% è la lettura più aggressiva sul mercato — come l'Inter al 40% quando il mercato la dava a 4. Il backtest dice che quando il modello ha avuto un super-favorito così (2010), aveva ragione; ma dice anche che 2 volte su 7 il vincitore è arrivato da fuori dalla top-5. **Usalo come usi l'antepost Serie A: la divergenza modello-mercato è il segnale d'ingresso, la convergenza è il momento di bloccare il profitto.**
