/*
 * Spracheingabe fuer Handychat Hermes.
 *
 * Fuegt neben dem Eingabefeld einen Mikrofonknopf ein. Antippen startet das
 * Zuhoeren, nochmal antippen beendet es. Gedacht fuer die Bedienung im Auto,
 * deshalb grosse Flaeche und deutlich sichtbarer Zustand.
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
    // 0 schaltet das ab; der Text bleibt dann im Feld stehen.
    autoSendenNachMs: 0,
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
        margin-inline-end: 8px;
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

  function einfuegen(feld, text) {
    const vorher = feld.value.trimEnd();
    feld.value = vorher ? vorher + " " + text : text;
    feld.dispatchEvent(new Event("input", { bubbles: true }));
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
    feld.parentNode.insertBefore(knopf, feld);

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

    function autoSendenPlanen() {
      if (!CONFIG.autoSendenNachMs) return;
      clearTimeout(uhr);
      uhr = setTimeout(() => {
        stopp();
        const s = knopfFinden();
        if (s) s.click();
      }, CONFIG.autoSendenNachMs);
    }

    function stopp() {
      clearTimeout(uhr);
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
        bisher = bisher ? bisher + " " + endgueltig.trim() : endgueltig.trim();
        einfuegen(feld, endgueltig.trim());
        autoSendenPlanen();
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
