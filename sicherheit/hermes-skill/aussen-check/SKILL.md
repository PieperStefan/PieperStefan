---
name: aussen-check
description: Prüft, ob Stefans Mac Studio oder Heimnetz vom Internet aus erreichbar ist (Shodan-Außensicht, Tailscale Funnel, UPnP am Router, Firewall, IPv6). Verwenden bei Fragen wie "Bin ich von außen erreichbar?", "Ist mein Netz sicher?", "Sicherheitscheck", und für den täglichen Wächterlauf.
---

# Außen-Check

Stefan will auf keinen Fall, dass seine Geräte vom Internet aus erreichbar
sind. Dieser Skill prüft das und erklärt das Ergebnis auf Deutsch, kurz und
ohne Fachjargon.

## Ablauf

1. Prüfen, ob das Prüfskript da ist:

   ```bash
   test -x ~/sicherheit/aussen-check.sh && echo da || echo fehlt
   ```

   Fehlt es, einrichten:

   ```bash
   curl -fsSL https://raw.githubusercontent.com/PieperStefan/PieperStefan/claude/tender-volta-e8585x/sicherheit/einrichten.sh | bash
   ```

2. Prüfung laufen lassen und den Bericht lesen:

   ```bash
   ~/sicherheit/aussen-check.sh
   ```

   Exit-Code 0 = nichts gefunden, 1 = mindestens ein Alarm. Der Bericht
   liegt danach auch in `~/Library/Logs/aussen-check-letzter.txt`.

3. Antwort an Stefan:
   - Erste Zeile: **"Von außen nichts erreichbar."** oder
     **"Achtung: N Dinge sind von außen erreichbar."**
   - Danach jeden ALARM in einem Satz: was offen ist und was das bedeutet.
   - HINWEISE nur kurz erwähnen.
   - Zu jedem Alarm die passende Abhilfe aus der Tabelle unten nennen.

## Abhilfe – nur nach Stefans ausdrücklichem OK ausführen

Nie selbstständig Einstellungen ändern. Erst vorschlagen, auf ein klares
"ja" warten, dann ausführen und mit einem erneuten Lauf von
`aussen-check.sh` beweisen, dass es zu ist.

| Fund | Abhilfe |
|---|---|
| Tailscale Funnel ist AN | `tailscale funnel status` zeigen, dann `tailscale funnel reset`. `tailscale serve` (nur im Tailnet, z. B. Hermes auf 8443) bleibt davon unberührt. |
| Firewall des Macs ist AUS | `sudo /usr/libexec/ApplicationFirewall/socketfilterfw --setglobalstate on` |
| UPnP-Freigaben am Router | Kann der Mac nicht abschalten. Stefan sagen: Router-Oberfläche öffnen, UPnP ausschalten, Liste der Freigaben leeren. Welches Gerät die Freigabe angelegt hat, steht in der Liste (IP-Adresse). |
| Shodan sieht offene Ports | Router-Oberfläche → Portfreigaben prüfen und alles löschen, was nicht ausdrücklich gewollt ist. Shodan-Daten können einige Tage alt sein; nach dem Schließen ist der Alarm erst nach Shodans nächstem Scan weg. |
| IPv6 aktiv (Hinweis) | Im Router prüfen, dass eingehende IPv6-Verbindungen blockiert sind und keine IPv6-Freigaben existieren. |

## Täglicher Wächterlauf

Läuft dieser Skill als geplante Aufgabe, nur dann eine Nachricht an Stefan
schicken, wenn es einen ALARM gibt. Bei "nichts gefunden" still bleiben.

## Grenzen offen sagen

- Shodan ist eine Außensicht mit Verzögerung, kein Live-Portscan.
- Portfreigaben im Router sieht man direkt nur in der Router-Oberfläche.
- Geht etwas nicht (kein Internet, Tailscale-Befehl fehlt), das sagen –
  nie "alles sicher" melden, wenn eine Prüfung nicht gelaufen ist.
