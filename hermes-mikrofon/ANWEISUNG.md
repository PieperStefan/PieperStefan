Baue Spracheingabe in die Weboberfläche von Handychat Hermes ein
(Port 5108). Ich will im Auto sprechen statt tippen — bisher nutze ich
die Diktierfunktion der Tastatur, das soll direkt in die Seite.

Die fertige Datei `mikrofon.js` liegt bei. Sie ist in Chromium gegen drei
Fälle getestet: Erkennung vorhanden, Browser ohne Erkennung, unsichere
Seite. In allen dreien verhält sie sich wie beschrieben.

## 1. Zuerst HTTPS — ohne das geht gar nichts

Die Seite läuft heute über `http://192.168.1.207:5108`. Browser geben das
Mikrofon auf unverschlüsselten Seiten grundsätzlich nicht frei, egal welcher
Browser, egal welche Einstellung. Nur `localhost` ist ausgenommen, und vom
iPhone aus ist der Mac Studio nicht localhost.

Wir haben Tailscale, das löst es ohne Zertifikatswarnung:

```bash
tailscale serve --help          # Syntax je nach Version prüfen
tailscale serve --bg http://localhost:5108
tailscale serve status
```

Danach ist die Seite unter `https://mac-studio.tail0b9854.ts.net/`
erreichbar, mit gültigem Zertifikat.

Voraussetzung: Im Tailscale-Adminbereich muss unter DNS die Option
"HTTPS Certificates" eingeschaltet sein. Prüfe das und sag mir Bescheid,
falls es fehlt — das muss ich im Browser klicken.

Ab dann rufe ich die Seite über diese Adresse auf, nicht mehr über die IP.
Der Verweis auf meinem iPhone-Homescreen muss entsprechend neu angelegt
werden.

## 2. Datei einbauen

- `mikrofon.js` in den Ordner legen, aus dem die Oberfläche ihre
  statischen Dateien ausliefert
- im HTML vor `</body>` einbinden:

  ```html
  <script src="/static/mikrofon.js" defer></script>
  ```

  Pfad an die tatsächliche Struktur anpassen.

## 3. Auswahl prüfen

Oben in `mikrofon.js` steht ein `CONFIG`-Block. Die Automatik nimmt das
größte sichtbare Textfeld und den ersten Absende-Knopf. Prüfe an der
echten Seite, ob das die richtigen Elemente trifft; falls nicht, trage
dort passende CSS-Selektoren ein.

Der Knopf wird direkt vor dem Eingabefeld eingefügt, ist 56 × 56 Pixel
groß und pulst rot, solange er zuhört. Beides ist für die Bedienung im
Auto so gewählt — bitte nicht verkleinern.

## 4. Auto-Senden

`CONFIG.autoSendenNachMs` steht auf 0, also aus. Der Text bleibt nach dem
Diktat im Feld stehen und ich schicke ihn selbst ab.

Frag mich, ob ich das anders will: Ein Wert von etwa 2000 schickt zwei
Sekunden nach dem letzten gesprochenen Wort automatisch ab. Im Auto ist
das bequem, kann aber auch ungewollt abschicken.

## 5. Testen

- am Mac in Safari über die HTTPS-Adresse: Knopf antippen, sprechen,
  nochmal antippen — der Text muss im Feld stehen
- danach auf dem iPhone, das ist der eigentliche Anwendungsfall
- prüfe, dass ein zweites Diktat den ersten Text nicht überschreibt,
  sondern anhängt

Falls die Seite meldet, der Browser kenne keine Spracherkennung, siehe
Abschnitt 6.

## 6. Falls Safari nicht mitspielt — die private Variante

`mikrofon.js` nutzt die Spracherkennung des Browsers. Apple erkennt auf
neueren Geräten auf dem Gerät selbst, kann aber auch an Apple-Server
schicken. Wenn dir das nicht passt oder Safari sich weigert, bauen wir es
anders:

- im Browser mit `getUserMedia` und `MediaRecorder` aufnehmen
- Audio an einen neuen Hermes-Endpunkt schicken
- dort lokal mit whisper.cpp oder faster-whisper transkribieren

Das bleibt vollständig im Haus und funktioniert unabhängig davon, was
Safari kann. Es braucht aber serverseitigen Code und ein Whisper-Modell.
Sag mir, ob ich das aufsetzen soll — fang nicht ungefragt damit an.

## 7. Melden

- ob HTTPS über Tailscale steht und unter welcher Adresse
- in welche Dateien du `mikrofon.js` eingebunden hast
- ob du Selektoren im CONFIG-Block anpassen musstest
- ob die Erkennung in Safari auf dem iPhone tatsächlich anspringt
