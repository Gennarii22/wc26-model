# Contenuto di traffico — Giorno 1 (pronto da pubblicare)

Tono: data-journalism asciutto, zero hype. Il numero è il gancio. Tutto in inglese.
Account faceless. CTA al prodotto solo nell'ultimo post / in bio, mai aggressiva.

---

## X / Twitter — Thread principale

**1/**
I ran 20,000 Monte Carlo simulations of the entire 2026 World Cup.
Spain wins it 34.8% of the time — more than France, England and Argentina *combined* (34.6%).
The full bracket 🧵

**2/**
Title odds (top 6):
🇪🇸 Spain — 34.8%
🇫🇷 France — 14.6%
🏴 England — 10.1%
🇦🇷 Argentina — 9.9%
🇪🇨 Ecuador — 5.2%
🇵🇹 Portugal — 4.5%
Spain's ELO (2219) is in a tier of its own.

**3/**
The model isn't vibes. It's a Poisson goals model trained on 32,282 international matches (1990–2026), plus squad value, squad age and structural covariates — then 20k full-tournament sims under official FIFA rules.

**4/**
Golden Boot race:
🥇 Kane — 28.0% (7.0 xG)
🥈 Mbappé — 16.2%
🥉 Messi — 14.1%
Ronaldo — 9.2%
Oyarzabal — 8.1%

**5/**
Fun stat: the eventual winner scores a median of 9 goals across the tournament (90th pct: 12). Lines up with the historical benchmark (8.4 / 11).

**6/**
I'm re-running the whole model after every matchday and posting the value bets vs the bookmakers' lines.
Full pass (104 matches + edges + updates to the final): [LINK]
Not a tipster. Just the numbers.

---

## Reddit — r/soccerbetting / r/SoccerBetting / r/worldcup

**Titolo:** I built a 20k-simulation World Cup model (Poisson + squad value, trained on 32k matches). Here are the title odds and the first value bets.

**Corpo:**
Long-time lurker. I built a Monte Carlo model for the 2026 WC and figured this sub would tear it apart properly, which is what I want.

Method: Poisson goals model (ΔELO + home + squad value + age + GDP per cap), trained on 32,282 internationals 1990–2026, then 20,000 full-tournament sims under FIFA rules. Approach follows Groll/Zeileis and Silver's PELE.

Title odds: Spain 34.8, France 14.6, England 10.1, Argentina 9.9, Ecuador 5.2, Portugal 4.5.
Golden Boot: Kane 28%, Mbappé 16%, Messi 14%.

Where I think there's value right now vs the lines: [inserire 2-3 value bet reali dall'output di gen_betting.py].

Happy to share methodology. Re-running it each matchday. Roast it.

*(Reddit: NIENTE link al prodotto nel post — verresti bannato. Il link va solo in bio/profilo. Il valore del post crea i follower; la bio converte.)*

---

## Note operative
- Pubblica il thread X la mattina di una giornata con big match.
- Su Reddit rispondi a OGNI commento tecnico: la credibilità = vendite.
- I 2-3 value bet reali li estraggo io da `gen_betting.py` / `betting_data.js` prima della pubblicazione.
