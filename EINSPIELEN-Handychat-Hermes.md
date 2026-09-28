# Handychat Hermes: Umbenennen und Spracheingabe einbauen

Führe das bitte vollständig auf diesem Mac aus. Am Ende will ich im
Browser nur noch neu laden und es sehen.

Die Weboberfläche von Hermes läuft auf Port 5108, erreichbar unter
`http://192.168.1.207:5108`. Ich benutze sie im Auto: chatten und mir die
Antwort vorlesen lassen. Zwei Dinge sollen sich ändern.

---

## Schritt 0 — Erst herausfinden, womit wir es zu tun haben

```bash
lsof -iTCP:5108 -sTCP:LISTEN          # welcher Prozess, welcher Pfad
ls -la ~/.hermes/installs/             # Installationen
```

Finde heraus:

- in welchem Verzeichnis die laufende Anwendung liegt
- wo sie ihre statischen Dateien ausliefert (css/js)
- welche HTML-Datei oder welches Template die Chatseite erzeugt
- wie der Dienst gestartet und neu gestartet wird (launchd? Skript? manuell?)

Ist das Verzeichnis ein Git-Repository? Wenn ja, stelle einen sauberen
Stand sicher. Wenn nein, lege vorher eine Kopie an. Ich will zurückkönnen.

**Zeig mir das Ergebnis, bevor du etwas änderst.**

---

## Schritt 1 — Umbenennen in "Handychat Hermes"

Aktuell steht oben links "Hermes Chat". Das soll überall **Handychat
Hermes** heißen.

```bash
grep -rn --binary-files=without-match "Hermes Chat" .
```

Ändere ausschließlich sichtbaren Text:

- den `<title>`-Tag
- die Überschrift in der Seite
- im Web-App-Manifest das Feld `name`
- das Meta-Tag `apple-mobile-web-app-title`
- Titel, die der Server selbst setzt

**Nicht anfassen:** Ordner- und Dateinamen, besonders unter `~/.hermes/`;
Modul-, Klassen- und Variablennamen; launchd-Labels; Port 5108; URLs und
Routen; Konfigurationsschlüssel. Daran hängen mein Homescreen-Verweis und
der Autostart.

Bist du bei einem Treffer unsicher, ob Beschriftung oder Bezeichner:
stehen lassen und mich fragen.

Ein Punkt zum Schluss: Auf dem iPhone-Homescreen kürzt iOS nach etwa
einem Dutzend Zeichen, "Handychat Hermes" hat 16. Setze es trotzdem
überall so, sag mir danach aber, wie es auf dem Homescreen aussieht, und
biete mir an, nur `short_name` auf `Hermes` zu kürzen.

---

## Schritt 2 — HTTPS einschalten, sonst bleibt das Mikrofon stumm

Das ist keine Kür. Browser geben das Mikrofon auf unverschlüsselten
Seiten grundsätzlich nicht frei, egal welcher Browser, egal welche
Einstellung. Nur `localhost` ist ausgenommen — und vom iPhone aus ist
dieser Mac nicht localhost.

Wir haben Tailscale, das löst es ohne Zertifikatswarnung:

```bash
tailscale serve --help                       # Syntax je nach Version prüfen
tailscale serve --bg http://localhost:5108
tailscale serve status
```

Danach ist die Seite unter `https://mac-studio.tail0b9854.ts.net/`
erreichbar, mit gültigem Zertifikat.

Voraussetzung: Im Tailscale-Adminbereich muss unter DNS die Option
"HTTPS Certificates" eingeschaltet sein. Prüfe, ob es klappt — wenn
nicht, sag mir Bescheid, das muss ich im Browser klicken.

Prüfen:

```bash
curl -sI https://mac-studio.tail0b9854.ts.net/ | head -3
```

---

## Schritt 3 — Mikrofonknopf einbauen

Die Datei liegt öffentlich abrufbar bereit, kein Zugang nötig:

```bash
curl -fsSL -o mikrofon.js \
  https://raw.githubusercontent.com/PieperStefan/PieperStefan/claude/dxf-from-blueprints-jxtt75/hermes-mikrofon/mikrofon.js
```

Lade sie in das Verzeichnis für statische Dateien, das du in Schritt 0
gefunden hast, und binde sie in die Chatseite ein, vor `</body>`:

```html
<script src="/static/mikrofon.js" defer></script>
```

Pfad an die tatsächliche Struktur anpassen.

Oben in der Datei steht ein `CONFIG`-Block. Die Automatik nimmt das
größte sichtbare Textfeld und den ersten Absende-Knopf. Prüfe an der
echten Seite, ob das die richtigen Elemente trifft, und trage sonst
passende CSS-Selektoren ein.

### Was die Datei tut

Sie setzt zwei Knöpfe vor das Eingabefeld:

- **Mikrofon** — antippen startet das Zuhören, nochmal antippen beendet
  es. Pulst rot, solange es hört.
- **Auto 4s** — schaltet das selbsttätige Absenden an und aus. Grün heißt
  an. Die Stellung merkt sich der Browser.

Ist Auto an, wird vier Sekunden nach dem letzten gesprochenen Wort
abgeschickt. Ein oranger Ring um das Mikrofon läuft sichtbar ab und
beginnt von vorn, sobald ich weiterspreche. Antippen des Mikrofons
bricht ab. Getippter Text löst niemals ein Absenden aus.

Beide Knöpfe sind 56 Pixel hoch — das ist für die Bedienung im Auto so
gewählt, bitte nicht verkleinern.

---

## Schritt 4 — Neu starten und prüfen

Dienst neu starten, dann:

```bash
curl -s https://mac-studio.tail0b9854.ts.net/ | grep -i -o "<title>[^<]*</title>"
curl -s https://mac-studio.tail0b9854.ts.net/ | grep -c "mikrofon.js"
```

Erwartet: `Handychat Hermes` und eine 1.

Danach im Browser am Mac über die HTTPS-Adresse öffnen, Mikrofon
antippen, etwas sagen, nochmal antippen. Der Text muss im Eingabefeld
stehen. Prüfe auch, dass ein zweites Diktat den ersten Text anhängt und
nicht überschreibt.

---

## Schritt 5 — Was du mir melden sollst

- wo die Anwendung liegt und wie der Dienst neu gestartet wird
- welche Dateien du geändert hast
- ob HTTPS über Tailscale steht und unter welcher Adresse ich die Seite
  ab jetzt aufrufe
- ob du Selektoren im CONFIG-Block anpassen musstest
- ob ich den Verweis auf meinem iPhone-Homescreen neu anlegen muss

---

## Wenn Safari die Spracherkennung nicht kann

`mikrofon.js` nutzt die Spracherkennung des Browsers. Meldet die Seite,
der Browser kenne keine Spracherkennung, dann sag mir das — fang nicht
ungefragt an, etwas anderes zu bauen.

Der Ausweg wäre: im Browser mit `getUserMedia` und `MediaRecorder`
aufnehmen, das Audio an einen neuen Hermes-Endpunkt schicken und dort
lokal mit faster-whisper transkribieren. Das bliebe vollständig auf
diesem Rechner, braucht aber serverseitigen Code und ein Whisper-Modell.
Darüber entscheide ich, wenn es so weit ist.
