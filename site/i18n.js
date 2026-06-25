/* ═══════════════════════════════════════════════════════════════════════
   i18n — Mondiale 2026 (IT / EN)
   Default: lingua del browser (it→it, altrimenti en). Scelta salvata in localStorage.
   Uso: data-i18n="key" (textContent), data-i18n-html="key" (innerHTML),
        data-i18n-ph="key" (placeholder). In JS: t('key').
   Le pagine che generano contenuto via JS definiscono window.onLangChange = ()=>render().
   ═══════════════════════════════════════════════════════════════════════ */
const I18N = {
 it:{
  "live":"Live",
  // ── Landing ─────────────────────────────────────────────────────────
  "l.badge":"Mondiale 2026",
  "l.hero_label":"Modello probabilistico · 20.000 simulazioni",
  "l.hero_head":'Il Mondiale 2026,<br>in <span class="serif-it">probabilità.</span>',
  "l.hero_lead":'Non pronostici. Un modello Monte Carlo che simula <b>20.000 volte</b> l\'intero torneo, calibrato su <b>32.282 partite internazionali</b> (1990–2026) con forza ELO, valore rosa e covariate strutturali. Probabilità per ogni squadra, tutte le partite, ed <b>edge calcolato vs le quote di mercato</b>. Si ri-simula dopo ogni giornata.',
  "l.t1":"Favorita · P(titolo)","l.t2":"Capocannoniere","l.t3":"Copertura","l.t3k":"partite del torneo",
  "l.f1l":"Titolo & tabellone","l.f1d":'Probabilità per ogni squadra — girone, ottavi, quarti, semifinale, titolo. <b>Ri-simulate dopo ogni giornata reale.</b>',
  "l.f2l":"104 partite","l.f2d":'Esito <b>1 / X / 2</b> e risultato più probabile per ogni gara.',
  "l.f3l":"Edge vs mercato","l.f3d":'La probabilità del modello contro le quote del book — <b>edge de-vigato</b>, calcolo onesto.',
  "l.f4l":"Capocannoniere","l.f4d":'Corsa al Golden Boot con probabilità per giocatore.',
  "l.gate_h":"Sblocca il modello",
  "l.gate_lead":"Lascia nome ed email: apro subito il modello completo e ti avviso quando esce un aggiornamento rilevante — fine gironi, ottavi, quarti. Gratuito.",
  "l.ph_name":"Nome","l.ph_email":"email@dominio.com",
  "l.consent":"Acconsento al trattamento di nome ed email per ricevere aggiornamenti sul modello. Posso revocare il consenso e disiscrivermi in qualsiasi momento.",
  "l.err":"Compila nome, email valida e spunta il consenso.",
  "l.btn":"Sblocca il modello","l.btn_loading":"Sblocco…",
  "l.disc":"Solo a scopo informativo · 18+ · scommettere comporta rischi.",
  "l.unlocked":"Accesso sbloccato",
  "l.bb1l":"Modello & antepost","l.bb1t":"Titolo, gironi, tabellone","l.bb1d":"Probabilità torneo, capocannoniere, calcolo edge.",
  "l.bb2l":"Value · partite","l.bb2t":"Quote fair & edge","l.bb2d":"Tutte le partite, mercati, edge vs il book.",
  "l.savelink":"Salva questo link per tornare:","l.copy":"Copia","l.copied":"Copiato",
  "l.foot":"Gennaro Pancia · modello probabilistico Mondiale 2026 · si aggiorna automaticamente dopo ogni giornata. The numbers don't lie.",
  // ── Dashboard ───────────────────────────────────────────────────────
  "d.h1":"Mondiale 2026 — Modello vs Mercato",
  "d.sub":"48 squadre · 20.000 simulazioni · Poisson ELO + rosa + macro · tabellone FIFA ufficiale (Annexe C)",
  "d.tolink":"Value partite →",
  "d.tab_ante":"Antepost","d.tab_gironi":"Gironi","d.tab_partite":"Partite","d.tab_bomber":"Capocannoniere","d.tab_prewc":"Pre-Mondiale",
  "d.pw_h":"Pre-Mondiale → ora · come si muovono le probabilità titolo a torneo iniziato",
  "d.pw_pre":"P(titolo) pre","d.pw_now":"P(titolo) ora","d.pw_delta":"Δ",
  "d.mercato":"Mercato","d.bankroll":"Bankroll €","d.kelly":"Kelly ×","d.clearq":"Cancella quote",
  "d.ante_title":"Probabilità torneo — 20.000 simulazioni",
  "d.ante_quote_for":"Probabilità torneo — quote per: ",
  "d.foot_ante":"Scegli il mercato, inserisci le quote del book → Edge, EV e stake Kelly si calcolano da soli (le quote restano salvate per ogni mercato). Righe oliva = value. Benchmark titolo: Zeileis Spagna 14,5% · Silver ~16% · Klement scelse l'Olanda — il 35% sulla Spagna è la lettura più aggressiva: la divergenza è il segnale.",
  "d.partite_title":"Pronostici — 72 partite della fase a gironi",
  "d.bomber_title":"Capocannoniere — Golden Boot · gol del vincitore: mediana 9 · inserisci le quote per il valore",
  "d.foot_bomber":"Modello v2: tasso realizzativo da xG/90 (club + nazionale, con shrinkage) × minuti attesi da titolarità × partite giocate (cammino simulato della squadra) + rigoristi designati + gol già segnati nel torneo. Conta di più quanto avanza la squadra che il talento puro. Backtest 2022: il vincitore reale (Mbappé) era il nostro favorito #1.",
  // headers dashboard
  "d.th_squadra":"Squadra","d.th_gir":"Gir.","d.th_rosa":"Rosa","d.th_pgir":"P(1° gir.)","d.th_pfin":"P(Finale)","d.th_ptit":"P(titolo)","d.th_quota":"Quota","d.th_edge":"Edge","d.th_stake":"Stake","d.th_pmk":"P(mercato)",
  "d.th_data":"Data","d.th_partita":"Partita","d.th_sede":"Sede","d.th_ris":"Risultato più prob.",
  "d.th_giocatore":"Giocatore","d.th_ruolo":"Ruolo","d.th_eta":"Età","d.th_golcaps":"Gol/Caps naz.","d.th_golatt":"Gol attesi",
  "d.girone":"Girone","d.th_1gir":"1° gir.","d.th_qualif":"Qualif.","d.th_titolo":"Titolo",
  // market labels (1X2 antepost)
  "mk.p_win":"Vincente Mondiale","mk.p_final":"Arriva in finale","mk.p_sf":"Arriva in semifinale","mk.p_qf":"Arriva ai quarti","mk.p_r16":"Arriva agli ottavi","mk.p_win_group":"Vincente girone","mk.p_r32":"Si qualifica","mk.p_r32_full":"Si qualifica (R32)",
  // ── Betting ─────────────────────────────────────────────────────────
  "b.h1":"Mondiale 2026 — Value & Quote",
  "b.sub":"probabilità dal modello (ELO live) · aggiornato: ",
  "b.tolink":"← Torneo & antepost",
  "b.mkts_h":"Mercati — clicca una riga per portarla nel calcolatore",
  "b.th_esito":"Esito","b.th_prob":"Probabilità","b.th_fair":"Quota fair",
  "b.calc_h":"Calcolatore di valore","b.sel_prompt":"Seleziona un mercato dalla tabella ←",
  "b.lbl_odds":"Quota bookmaker","b.lbl_bank":"Bankroll €","b.lbl_kelly":"Frazione Kelly",
  "b.note":"EV = P_modello × quota − 1 (valore atteso per 1€). Kelly pieno = edge/(quota−1); usa la frazione (0,25 consigliato) per gestire la varianza. Oliva = c'è valore.",
  "b.topsc":"Risultati esatti più probabili","b.heat":"Mappa risultati esatti (P%)","b.dist":"Distribuzione gol attesi",
  "b.scorers":"Marcatori","b.sc_player":"Giocatore","b.sc_p1":"Segna","b.sc_p2":"2+","b.sc_p3":"3+",
  "b.shots":"Tiri","b.shots_tot":"Tiri totali","b.shots_sot":"Tiri in porta","b.sh_o05":"Over 0.5","b.sh_o15":"Over 1.5","b.sh_o25":"Over 2.5","b.sh_o35":"Over 3.5","b.sot_o05":"Porta 0.5","b.sot_o15":"Porta 1.5",
  "b.cards":"Cartellini partita","b.cd_line":"Linea","b.cd_over":"Over","b.cd_under":"Under","b.cd_exp":"Attesi:",
  "b.gol_attesi":"gol attesi","b.in_attesa":"In attesa","b.insert_quota":"inserisci la quota",
  "b.kpi_ev":"Valore (EV/1€)","b.kpi_edge":"Edge","b.kpi_kelly":"Kelly pieno","b.kpi_stake":"Stake",
  "b.pmod":"P modello","b.fair":"fair",
  "bm.1":"1 (casa)","bm.X":"X (pareggio)","bm.2":"2 (trasferta)","bm.1X":"Doppia chance 1X","bm.12":"Doppia chance 12","bm.X2":"Doppia chance X2","bm.GOL":"Gol (BTTS sì)","bm.NOGOL":"No Gol (BTTS no)","bm.O15":"Over 1.5","bm.U15":"Under 1.5","bm.O25":"Over 2.5","bm.U25":"Under 2.5","bm.O35":"Over 3.5","bm.U35":"Under 3.5"
 },
 en:{
  "live":"Live",
  // ── Landing ─────────────────────────────────────────────────────────
  "l.badge":"World Cup 2026",
  "l.hero_label":"Probabilistic model · 20,000 simulations",
  "l.hero_head":'The 2026 World Cup,<br>in <span class="serif-it">probabilities.</span>',
  "l.hero_lead":'Not predictions. A Monte Carlo model that simulates the whole tournament <b>20,000 times</b>, calibrated on <b>32,282 international matches</b> (1990–2026) with ELO strength, squad value and structural covariates. Probabilities for every team, every match, and <b>edge computed vs market odds</b>. Re-simulated after each matchday.',
  "l.t1":"Favourite · P(title)","l.t2":"Top scorer","l.t3":"Coverage","l.t3k":"tournament matches",
  "l.f1l":"Title & bracket","l.f1d":'Probabilities for every team — group, R16, quarters, semis, title. <b>Re-simulated after every real matchday.</b>',
  "l.f2l":"104 matches","l.f2d":'Outcome <b>1 / X / 2</b> and most likely score for every game.',
  "l.f3l":"Edge vs market","l.f3d":'The model\'s probability against the book\'s odds — <b>de-vigged edge</b>, honest math.',
  "l.f4l":"Top scorer","l.f4d":'Golden Boot race with per-player probabilities.',
  "l.gate_h":"Unlock the model",
  "l.gate_lead":"Leave your name and email: I'll open the full model right away and notify you when a meaningful update drops — end of groups, round of 16, quarters. Free.",
  "l.ph_name":"Name","l.ph_email":"email@domain.com",
  "l.consent":"I consent to the processing of my name and email to receive updates about the model. I can withdraw consent and unsubscribe at any time.",
  "l.err":"Enter your name, a valid email and tick the consent box.",
  "l.btn":"Unlock the model","l.btn_loading":"Unlocking…",
  "l.disc":"For informational purposes only · 18+ · betting involves risk.",
  "l.unlocked":"Access unlocked",
  "l.bb1l":"Model & outrights","l.bb1t":"Title, groups, bracket","l.bb1d":"Tournament probabilities, top scorer, edge calculator.",
  "l.bb2l":"Value · matches","l.bb2t":"Fair odds & edge","l.bb2d":"Every match, markets, edge vs the book.",
  "l.savelink":"Save this link to come back:","l.copy":"Copy","l.copied":"Copied",
  "l.foot":"Gennaro Pancia · 2026 World Cup probabilistic model · updates automatically after every matchday. The numbers don't lie.",
  // ── Dashboard ───────────────────────────────────────────────────────
  "d.h1":"World Cup 2026 — Model vs Market",
  "d.sub":"48 teams · 20,000 simulations · Poisson ELO + squad + macro · official FIFA bracket (Annex C)",
  "d.tolink":"Match value →",
  "d.tab_ante":"Outrights","d.tab_gironi":"Groups","d.tab_partite":"Matches","d.tab_bomber":"Top scorer","d.tab_prewc":"Pre-World Cup",
  "d.pw_h":"Pre-World Cup → now · how title probabilities move once the tournament is underway",
  "d.pw_pre":"P(title) pre","d.pw_now":"P(title) now","d.pw_delta":"Δ",
  "d.mercato":"Market","d.bankroll":"Bankroll €","d.kelly":"Kelly ×","d.clearq":"Clear odds",
  "d.ante_title":"Tournament probabilities — 20,000 simulations",
  "d.ante_quote_for":"Tournament probabilities — odds for: ",
  "d.foot_ante":"Pick the market, enter the book's odds → Edge, EV and Kelly stake compute automatically (odds are saved per market). Olive rows = value. Title benchmarks: Zeileis Spain 14.5% · Silver ~16% · Klement picked the Netherlands — our 35% on Spain is the most aggressive read: the divergence is the signal.",
  "d.partite_title":"Forecasts — 72 group-stage matches",
  "d.bomber_title":"Top scorer — Golden Boot · winner's goals: median 9 · enter odds for the value",
  "d.foot_bomber":"Model v2: scoring rate from xG/90 (club + national, with shrinkage) × expected minutes from starter status × matches played (the team's simulated run) + designated penalty takers + goals already scored in the tournament. How far the team goes matters more than raw talent. 2022 backtest: the actual winner (Mbappé) was our #1 pick.",
  "d.th_squadra":"Team","d.th_gir":"Grp","d.th_rosa":"Squad","d.th_pgir":"P(1st)","d.th_pfin":"P(Final)","d.th_ptit":"P(title)","d.th_quota":"Odds","d.th_edge":"Edge","d.th_stake":"Stake","d.th_pmk":"P(market)",
  "d.th_data":"Date","d.th_partita":"Match","d.th_sede":"Venue","d.th_ris":"Most likely score",
  "d.th_giocatore":"Player","d.th_ruolo":"Role","d.th_eta":"Age","d.th_golcaps":"Goals/Caps (nat.)","d.th_golatt":"Exp. goals",
  "d.girone":"Group","d.th_1gir":"1st","d.th_qualif":"Qualify","d.th_titolo":"Title",
  "mk.p_win":"World Cup winner","mk.p_final":"Reaches the final","mk.p_sf":"Reaches the semis","mk.p_qf":"Reaches the quarters","mk.p_r16":"Reaches round of 16","mk.p_win_group":"Wins the group","mk.p_r32":"Qualifies","mk.p_r32_full":"Qualifies (R32)",
  // ── Betting ─────────────────────────────────────────────────────────
  "b.h1":"World Cup 2026 — Value & Odds",
  "b.sub":"probabilities from the model (live ELO) · updated: ",
  "b.tolink":"← Tournament & outrights",
  "b.mkts_h":"Markets — click a row to send it to the calculator",
  "b.th_esito":"Outcome","b.th_prob":"Probability","b.th_fair":"Fair odds",
  "b.calc_h":"Value calculator","b.sel_prompt":"Select a market from the table ←",
  "b.lbl_odds":"Bookmaker odds","b.lbl_bank":"Bankroll €","b.lbl_kelly":"Kelly fraction",
  "b.note":"EV = P_model × odds − 1 (expected value per €1). Full Kelly = edge/(odds−1); use the fraction (0.25 recommended) to manage variance. Olive = there's value.",
  "b.topsc":"Most likely exact scores","b.heat":"Exact-score map (P%)","b.dist":"Expected goals distribution",
  "b.scorers":"Goalscorers","b.sc_player":"Player","b.sc_p1":"Anytime","b.sc_p2":"2+","b.sc_p3":"3+",
  "b.shots":"Shots","b.shots_tot":"Total shots","b.shots_sot":"Shots on target","b.sh_o05":"Over 0.5","b.sh_o15":"Over 1.5","b.sh_o25":"Over 2.5","b.sh_o35":"Over 3.5","b.sot_o05":"On Target 0.5","b.sot_o15":"On Target 1.5",
  "b.cards":"Match cards","b.cd_line":"Line","b.cd_over":"Over","b.cd_under":"Under","b.cd_exp":"Expected:",
  "b.gol_attesi":"expected goals","b.in_attesa":"Waiting","b.insert_quota":"enter the odds",
  "b.kpi_ev":"Value (EV/€1)","b.kpi_edge":"Edge","b.kpi_kelly":"Full Kelly","b.kpi_stake":"Stake",
  "b.pmod":"P model","b.fair":"fair",
  "bm.1":"1 (home)","bm.X":"X (draw)","bm.2":"2 (away)","bm.1X":"Double chance 1X","bm.12":"Double chance 12","bm.X2":"Double chance X2","bm.GOL":"BTTS (yes)","bm.NOGOL":"BTTS (no)","bm.O15":"Over 1.5","bm.U15":"Under 1.5","bm.O25":"Over 2.5","bm.U25":"Under 2.5","bm.O35":"Over 3.5","bm.U35":"Under 3.5"
 }
};

function getLang(){
  const s=localStorage.getItem('wc26_lang');
  if(s==='it'||s==='en') return s;
  return (navigator.language||'en').toLowerCase().startsWith('it') ? 'it' : 'en';
}
function t(key){const L=getLang();return (I18N[L]&&I18N[L][key])!=null?I18N[L][key]:(I18N.it[key]!=null?I18N.it[key]:key);}
function applyI18n(){
  const L=getLang();
  document.documentElement.lang=L;
  document.querySelectorAll('[data-i18n]').forEach(el=>el.textContent=t(el.dataset.i18n));
  document.querySelectorAll('[data-i18n-html]').forEach(el=>el.innerHTML=t(el.dataset.i18nHtml));
  document.querySelectorAll('[data-i18n-ph]').forEach(el=>el.placeholder=t(el.dataset.i18nPh));
  document.querySelectorAll('[data-lang-btn]').forEach(b=>b.classList.toggle('on',b.dataset.langBtn===L));
}
function setLang(l){localStorage.setItem('wc26_lang',l);applyI18n();if(typeof window.onLangChange==='function')window.onLangChange();}
document.addEventListener('DOMContentLoaded',applyI18n);
