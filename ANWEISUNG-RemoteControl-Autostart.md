# Remote Control dauerhaft und neustartfest einrichten

Ich will nicht jedes Mal `/rc` eintippen. Die Sitzung soll nach jedem
Neustart und nach jeder Anmeldung von selbst wieder da sein, damit ich
sie vom Handy und über claude.ai erreiche.

Zielrechner ist der **Mac Studio** — der läuft durch. Erreichbar per SSH
unter `mac-studio.tail0b9854.ts.net`.

## Schritt 1 — Erst herausfinden, was überhaupt geht

Rate nicht. Kläre zuerst, ob Remote Control ohne Terminalfenster laufen
kann:

```bash
ssh mac-studio.tail0b9854.ts.net '~/.local/bin/claude --help'
ssh mac-studio.tail0b9854.ts.net '~/.local/bin/claude remote-control --help'
```

Achte darauf, ob es eine Betriebsart ohne Bedienoberfläche gibt
(Stichworte: headless, daemon, background, --print). Sag mir, was du
findest, bevor du etwas einrichtest.

Falls Remote Control zwingend ein Terminal braucht, sag mir das offen —
dann bauen wir es anders, etwa über eine dauerhafte tmux-Sitzung. Bastle
in dem Fall keinen launchd-Job, der still scheitert.

## Schritt 2 — Zwei Stolpersteine, die wir schon kennen

Beide haben mich heute schon Zeit gekostet, plane sie ein:

- **Das Home-Verzeichnis geht nicht.** Claude verweigert dort den
  Vertrauensstatus. Der Dienst braucht ein Projektverzeichnis als
  Arbeitsverzeichnis, zum Beispiel `~/Server-KI-Projekte`. Dort muss
  einmal `claude` gelaufen und der Vertrauensdialog bestätigt worden
  sein — prüfe, ob das schon der Fall ist.
- **PATH gilt in launchd nicht.** Benutze überall den vollen Pfad
  `/Users/Pieper/.local/bin/claude`, niemals nur `claude`.

## Schritt 3 — Einrichten

Lege einen LaunchAgent an, keinen LaunchDaemon — Remote Control braucht
meine Benutzersitzung und den Schlüsselbund:

`~/Library/LaunchAgents/com.pieper.claude-remote-control.plist`

mit:

- `RunAtLoad` = true, damit es bei der Anmeldung startet
- `KeepAlive` = true, damit es nach einem Absturz wieder hochkommt
- `WorkingDirectory` = das Projektverzeichnis aus Schritt 2
- `StandardOutPath` und `StandardErrorPath` in eine Logdatei unter
  `~/Library/Logs/`, damit ich nachsehen kann, wenn es klemmt
- der Aufruf aus Schritt 1, mit vollem Pfad

Dann laden:

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.pieper.claude-remote-control.plist
launchctl kickstart -k gui/$(id -u)/com.pieper.claude-remote-control
```

## Schritt 4 — Beweisen, dass es hält

Es reicht mir nicht, dass es einmal läuft. Zeig mir:

1. `launchctl print gui/$(id -u)/com.pieper.claude-remote-control` —
   Zustand und letzter Beendigungsgrund
2. die letzten Zeilen der Logdatei
3. dass die Sitzung tatsächlich angemeldet ist
4. **den Neustarttest:** Prozess hart beenden, dann nach zehn Sekunden
   prüfen, ob launchd ihn wieder hochgezogen hat

Wenn die Logdatei eine Schleife zeigt — Start, Absturz, Neustart im
Sekundentakt — dann ist es nicht eingerichtet, sondern kaputt. Sag mir
das, statt es als erledigt zu melden.

## Schritt 5 — Melden

- ob Remote Control ohne Terminal läuft, und mit welchem Aufruf
- wo der LaunchAgent liegt und wo seine Logdatei
- das Ergebnis des Neustarttests
- die Adresse, unter der ich die Sitzung ab jetzt erreiche
- ob dasselbe auch auf dem MacBook Air sinnvoll ist oder ob eine
  dauerhafte Sitzung auf dem Mac Studio reicht
