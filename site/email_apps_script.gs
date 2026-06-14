/**
 * Google Apps Script — raccolta email del modello Mondiale 2026.
 * Riceve le email dal form di index.html e le scrive in un Google Sheet che possiedi TU.
 *
 * SETUP (5 minuti):
 * 1. Vai su https://sheets.new → crea un foglio, chiamalo "WC26 Iscritti".
 *    Nella riga 1 metti le intestazioni: A1=Data  B1=Email  C1=Fonte
 * 2. Copia l'ID del foglio dall'URL:
 *    docs.google.com/spreadsheets/d/ >>> QUESTO_E_L_ID <<< /edit
 *    e incollalo qui sotto in SHEET_ID.
 * 3. Nel foglio: menu Estensioni → Apps Script. Cancella tutto e incolla QUESTO file.
 * 4. Salva (icona dischetto).
 * 5. Pulsante "Esegui deployment" (in alto a destra) → Nuovo deployment →
 *    tipo "App web". Configura:
 *       - Esegui come: Me (il tuo account)
 *       - Chi ha accesso: CHIUNQUE
 *    → Esegui deployment → Autorizza (accetta i permessi).
 * 6. Copia l'URL della Web App (finisce con /exec).
 * 7. Aprilo UNA volta nel browser: deve mostrare {"ok":true,...}.
 * 8. Incolla quell'URL in site/index.html al posto di PASTE_APPS_SCRIPT_URL_HERE.
 *
 * Da quel momento ogni email inserita nel sito compare nel foglio in tempo reale.
 */

var SHEET_ID = "INCOLLA_QUI_L_ID_DEL_FOGLIO";

function doPost(e) {
  try {
    var ss = SpreadsheetApp.openById(SHEET_ID);
    var sheet = ss.getSheetByName("WC26 Iscritti") || ss.getActiveSheet();
    var email = (e.parameter.email || "").toString().trim();
    var src = (e.parameter.src || "wc26").toString();
    if (email) sheet.appendRow([new Date(), email, src]);
    return ContentService
      .createTextOutput(JSON.stringify({ ok: true }))
      .setMimeType(ContentService.MimeType.JSON);
  } catch (err) {
    return ContentService
      .createTextOutput(JSON.stringify({ ok: false, error: String(err) }))
      .setMimeType(ContentService.MimeType.JSON);
  }
}

// permette di verificare aprendo l'URL nel browser
function doGet() {
  return ContentService
    .createTextOutput(JSON.stringify({ ok: true, msg: "WC26 email endpoint attivo" }))
    .setMimeType(ContentService.MimeType.JSON);
}
