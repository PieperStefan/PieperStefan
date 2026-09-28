/*
 * Spracheingabe fuer Handychat Hermes.
 *
 * Fuegt neben dem Eingabefeld zwei Knoepfe ein:
 *
 *   Mikrofon  - antippen startet das Zuhoeren, nochmal antippen beendet es.
 *   Auto      - schaltet das selbsttaetige Absenden an und aus. Der Zustand
 *               wird im Browser gemerkt.
 *
 * Ist Auto an, wird vier Sekunden nach dem letzten gesprochenen Wort
 * abgeschickt. Ein Ring um den Mikrofonknopf laeuft dabei sichtbar ab und
 * beginnt von vorn, sobald weitergesprochen wird. Antippen des Mikrofons
 * bricht ab. Getipptes loest niemals ein Absenden aus - nur Diktiertes.
 *
 * Gedacht fuer die Bedienung im Auto, deshalb grosse Flaechen und
 * deutlich sichtbarer Zustand.
 *
 * Voraussetzung: Die Seite muss ueber HTTPS ausgeliefert werden. Browser
 * geben das Mikrofon auf unverschluesselten Seiten grundsaetzlich nicht
 * frei - ausser auf localhost. Siehe ANWEISUNG.md, Schritt 1.
 *
 * Einbinden: <script src="/static/mikrofon.js" defer></script>
 */
(function () {
  "use strict";

  const CONFIG = {
    // Diese beiden Angaben an die Seite anpassen, falls die Automatik
    // das Falsche findet.
    eingabeFeld: "textarea, input[type=text]",
    sendenKnopf: 'button[type="submit"], #senden',
    sprache: "de-DE",
    // Nach wie vielen Millisekunden Stille automatisch abgeschickt wird.
    autoSendenNachMs: 4000,
    // Stellung des Auto-Knopfes beim allerersten Aufruf.
    autoSendenVoreinstellung: true,
  };

  const Erkennung =
    window.SpeechRecognition || window.webkitSpeechRecognition || null;

  function feldFinden() {
    const felder = Array.from(document.querySelectorAll(CONFIG.eingabeFeld));
    // Das groesste sichtbare Feld ist in aller Regel das Nachrichtenfeld.
    return felder
      .filter((f) => f.offsetParent !== null)
      .sort((a, b) => b.clientWidth * b.clientHeight - a.clientWidth * a.clientHeight)[0] || null;
  }

  function knopfFinden() {
    return document.querySelector(CONFIG.sendenKnopf);
  }

  function stilAnlegen() {
    if (document.getElementById("mikrofon-stil")) return;
    const s = document.createElement("style");
    s.id = "mikrofon-stil";
    s.textContent = `
      .mikrofon-knopf {
        width: 56px; height: 56px; min-width: 56px;
        border: 0; border-radius: 50%;
        background: #2f3b33; color: #e8f0ea;
        font-size: 26px; line-height: 1;
        cursor: pointer; touch-action: manipulation;
        display: inline-flex; align-items: center; justify-content: center;
        margin-inline-end: 8px; position: relative;
      }
      .mikrofon-knopf:disabled { opacity: .45; cursor: not-allowed; }
      .mikrofon-knopf.hoert {
        background: #b23b3b;
        animation: mikrofon-puls 1.1s ease-in-out infinite;
      }
      @keyframes mikrofon-puls {
        0%,100% { box-shadow: 0 0 0 0 rgba(178,59,59,.65); }
        50%     { box-shadow: 0 0 0 12px rgba(178,59,59,0); }
      }
      .mikrofon-knopf.gleich::after {
        content: ""; position: absolute; inset: -5px;
        border-radius: 50%; border: 3px solid #e0a13a;
        animation: mikrofon-ablauf var(--mikrofon-frist, 4s) linear forwards;
      }
      @keyframes mikrofon-ablauf {
        from { clip-path: inset(0 0 0 0); opacity: 1; }
        to   { clip-path: inset(0 0 100% 0); opacity: .25; }
      }
      .auto-knopf {
        height: 56px; padding: 0 16px;
        border: 2px solid #4a5a4e; border-radius: 28px;
        background: #222a24; color: #8a978d;
        font-size: 15px; font-weight: 600;
        cursor: pointer; touch-action: manipulation;
        margin-inline-end: 8px;
      }
      .auto-knopf[aria-pressed="true"] {
        background: #2f5d3a; border-color: #468a56; color: #eaf5ec;
      }
      .mikrofon-hinweis {
        font-size: 13px; line-height: 1.4; padding: 8px 10px; margin: 6px 0;
        border-radius: 8px; background: #3a2f2f; color: #f0e2e2;
      }
      @media (prefers-reduced-motion: reduce) {
        .mikrofon-knopf.hoert { animation: none; }
      }
    `;
    document.head.appendChild(s);
  }

  function hinweis(text) {
    const feld = feldFinden();
    if (!feld) return;
    let box = document.getElementById("mikrofon-hinweis");
    if (!box) {
      box = document.createElement("div");
      box.id = "mikrofon-hinweis";
      box.className = "mikrofon-hinweis";
      box.setAttribute("role", "status");
      feld.parentNode.insertBefore(box, feld);
    }
    box.textContent = text;
  }

  function wertSetzen(feld, wert) {
    // Ueber den nativen Setter, sonst bekommen Frameworks (React, Vue, Svelte)
    // die Aenderung nicht mit und ueberschreiben sie beim naechsten Zeichnen.
    const art = feld instanceof HTMLTextAreaElement
      ? HTMLTextAreaElement.prototype
      : HTMLInputElement.prototype;
    const setter = Object.getOwnPropertyDescriptor(art, "value");
    if (setter && setter.set) setter.set.call(feld, wert);
    else feld.value = wert;
  }

  function einfuegen(feld, text) {
    const vorher = (feld.value || "").trimEnd();
    const wert = vorher ? vorher + " " + text : text;

    try { feld.focus(); } catch (e) { /* egal */ }
    wertSetzen(feld, wert);
    try { feld.setSelectionRange(wert.length, wert.length); } catch (e) { /* egal */ }

    // Breit streuen: verschiedene Oberflaechen hoeren auf verschiedene Ereignisse.
    for (const art of ["input", "change"]) {
      feld.dispatchEvent(new Event(art, { bubbles: true }));
    }
    for (const art of ["keydown", "keyup"]) {
      feld.dispatchEvent(new KeyboardEvent(art, { bubbles: true, key: " " }));
    }

    // Kam es an? Sonst sagen wir es, statt still zu versagen.
    if ((feld.value || "").indexOf(text) === -1) {
      hinweis(
        "Der erkannte Text wurde nicht übernommen: \u201e" + text + "\u201c. " +
        "Das Eingabefeld nimmt ihn nicht an — bitte melden."
      );
      return false;
    }
    return true;
  }

  function start() {
    stilAnlegen();
    const feld = feldFinden();
    if (!feld) {
      console.warn("[Mikrofon] Kein Eingabefeld gefunden - CONFIG.eingabeFeld anpassen.");
      return;
    }

    const knopf = document.createElement("button");
    knopf.type = "button";
    knopf.className = "mikrofon-knopf";
    knopf.textContent = "🎤";
    knopf.setAttribute("aria-label", "Spracheingabe starten");
    knopf.style.setProperty("--mikrofon-frist", CONFIG.autoSendenNachMs + "ms");
    feld.parentNode.insertBefore(knopf, feld);

    // Knopf fuer das selbsttaetige Absenden
    const autoKnopf = document.createElement("button");
    autoKnopf.type = "button";
    autoKnopf.className = "auto-knopf";
    const sekunden = Math.round(CONFIG.autoSendenNachMs / 1000);
    autoKnopf.textContent = "Auto " + sekunden + "s";
    let autoAn = gemerkt();
    function gemerkt() {
      try {
        const g = localStorage.getItem("hermes-autosenden");
        if (g === "an") return true;
        if (g === "aus") return false;
      } catch (e) { /* Speicher gesperrt */ }
      return CONFIG.autoSendenVoreinstellung;
    }
    function autoAnzeigen() {
      autoKnopf.setAttribute("aria-pressed", autoAn ? "true" : "false");
      autoKnopf.setAttribute(
        "aria-label",
        autoAn
          ? "Selbsttätiges Absenden ist an. Antippen schaltet es aus."
          : "Selbsttätiges Absenden ist aus. Antippen schaltet es an."
      );
    }
    autoAnzeigen();
    autoKnopf.addEventListener("click", () => {
      autoAn = !autoAn;
      try { localStorage.setItem("hermes-autosenden", autoAn ? "an" : "aus"); }
      catch (e) { /* Speicher gesperrt */ }
      autoAnzeigen();
      if (!autoAn) ablaufAbbrechen();
    });
    feld.parentNode.insertBefore(autoKnopf, feld);

    // Die beiden Faelle, in denen es gar nicht erst losgehen kann.
    if (!window.isSecureContext) {
      knopf.disabled = true;
      hinweis(
        "Mikrofon nicht verfügbar: Die Seite läuft über unverschlüsseltes HTTP. " +
          "Browser geben das Mikrofon nur über HTTPS frei."
      );
      return;
    }
    if (!Erkennung) {
      knopf.disabled = true;
      hinweis(
        "Dieser Browser kennt keine Spracherkennung. Auf dem iPhone Safari " +
          "verwenden, sonst die Whisper-Variante einbauen."
      );
      return;
    }

    const erk = new Erkennung();
    erk.lang = CONFIG.sprache;
    erk.continuous = true;
    erk.interimResults = true;

    let hoert = false;
    let uhr = null;
    let bisher = "";

    function ablaufAbbrechen() {
      clearTimeout(uhr);
      uhr = null;
      knopf.classList.remove("gleich");
    }

    function autoSendenPlanen() {
      if (!autoAn || !CONFIG.autoSendenNachMs) return;
      clearTimeout(uhr);
      // Ring neu starten: Klasse ab, Umbruch erzwingen, Klasse dran.
      knopf.classList.remove("gleich");
      void knopf.offsetWidth;
      knopf.classList.add("gleich");
      uhr = setTimeout(() => {
        knopf.classList.remove("gleich");
        stopp();
        const s = knopfFinden();
        if (s) s.click();
      }, CONFIG.autoSendenNachMs);
    }

    function stopp() {
      ablaufAbbrechen();
      if (hoert) {
        hoert = false;
        try { erk.stop(); } catch (e) { /* bereits gestoppt */ }
      }
      knopf.classList.remove("hoert");
      knopf.setAttribute("aria-label", "Spracheingabe starten");
    }

    erk.onresult = (ereignis) => {
      let endgueltig = "";
      let vorlaeufig = "";
      for (let i = ereignis.resultIndex; i < ereignis.results.length; i++) {
        const stueck = ereignis.results[i][0].transcript;
        if (ereignis.results[i].isFinal) endgueltig += stueck;
        else vorlaeufig += stueck;
      }
      if (endgueltig) {
        const stueck = endgueltig.trim();
        bisher = bisher ? bisher + " " + stueck : stueck;
        knopf.setAttribute("title", "zuletzt erkannt: " + stueck);
        if (einfuegen(feld, stueck)) autoSendenPlanen();
      }
      if (vorlaeufig) {
        feld.setAttribute("placeholder", vorlaeufig.trim());
        autoSendenPlanen();
      }
    };

    erk.onerror = (ereignis) => {
      const texte = {
        "not-allowed": "Zugriff aufs Mikrofon wurde abgelehnt. In den Browsereinstellungen für diese Seite erlauben.",
        "service-not-allowed": "Zugriff aufs Mikrofon wurde vom System blockiert.",
        "audio-capture": "Kein Mikrofon gefunden.",
        "network": "Die Spracherkennung konnte den Dienst nicht erreichen.",
        "no-speech": "Nichts gehört.",
      };
      if (ereignis.error !== "no-speech") {
        hinweis(texte[ereignis.error] || ("Spracherkennung: " + ereignis.error));
      }
      stopp();
    };

    erk.onend = () => { if (hoert) { try { erk.start(); } catch (e) { stopp(); } } };

    knopf.addEventListener("click", () => {
      if (hoert) { stopp(); return; }
      bisher = "";
      hoert = true;
      knopf.classList.add("hoert");
      knopf.setAttribute("aria-label", "Spracheingabe beenden");
      try {
        erk.start();
      } catch (e) {
        hoert = false;
        knopf.classList.remove("hoert");
        hinweis("Spracherkennung ließ sich nicht starten: " + e.message);
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }
})();
