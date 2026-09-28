Benenne die Weboberfläche von Hermes von "Hermes Chat" in
**"Handychat Hermes"** um. Das ist die Oberfläche, die ich im Auto
benutze — Chat mit Sprachausgabe, erreichbar unter Port 5108.

Ändere ausschließlich Beschriftungen. Technische Bezeichner bleiben
unangetastet, daran hängen mein Homescreen-Verweis und der Autostart.

## 1. Erst absichern

- Ist das Projekt ein Git-Repository? (`git status`)
  Falls ja: sauberer Stand vor der Änderung, damit ich zurück kann.
  Falls nein: vorher eine Kopie des betroffenen Ordners anlegen.
- Finde heraus, wo die Anwendung liegt. Ausgangspunkt:
  `/Users/Pieper/.hermes/installs/` — der laufende Dienst hört auf Port 5108
  (`lsof -iTCP:5108 -sTCP:LISTEN`).

## 2. Vorkommen finden, noch nichts ändern

```bash
grep -rn --binary-files=without-match "Hermes Chat" . 
grep -rn --binary-files=without-match "apple-mobile-web-app-title\|short_name\|manifest" .
```

Zeig mir die Trefferliste und ordne jeden Treffer einer der beiden
Gruppen zu, bevor du etwas anfasst.

## 3. Was geändert wird

Nur sichtbarer Text:

- der `<title>`-Tag der Seite
- die Überschrift im Fenster (aktuell "Hermes Chat" oben links)
- im Web-App-Manifest das Feld `name`
- das Meta-Tag `apple-mobile-web-app-title`
- Fenster- oder Seitentitel, die der Server selbst setzt

Neuer Wert überall: `Handychat Hermes`

## 4. Was nicht angefasst wird

- Ordner- und Dateinamen, besonders unterhalb von `~/.hermes/`
- Modul-, Klassen- und Variablennamen im Python-Code
- launchd-Labels, Dienstnamen, Autostart-Einträge
- Port 5108, URLs, Routen, API-Pfade
- Konfigurationsschlüssel und deren Werte
- alles, was generiert wird oder aus einem Paket stammt

Wenn du unsicher bist, ob ein Treffer Beschriftung oder Bezeichner ist:
nicht ändern, sondern mich fragen.

## 5. Ein Punkt, den du mir vorlegen sollst

Auf dem iPhone-Homescreen kürzt iOS die Beschriftung nach etwa einem
Dutzend Zeichen. "Handychat Hermes" hat 16 und erscheint dort
abgeschnitten.

Setze trotzdem zunächst überall "Handychat Hermes" — auch in
`short_name`. Sag mir danach, wie es auf dem Homescreen aussieht, und
biete mir an, nur `short_name` auf `Hermes` zu kürzen. Das ist eine
einzelne Zeile und ändert sonst nichts.

## 6. Neu starten und prüfen

Dienst neu starten, dann:

```bash
curl -s http://localhost:5108/ | grep -i -o "<title>[^<]*</title>"
```

Muss `Handychat Hermes` zeigen.

## 7. Melden

- welche Dateien du geändert hast, mit Zeilennummern
- welche Treffer du bewusst stehen gelassen hast und warum
- ob der Dienst sauber neu gestartet ist
- ob ich auf dem iPhone den Homescreen-Verweis neu anlegen muss, damit
  der Name dort ankommt
