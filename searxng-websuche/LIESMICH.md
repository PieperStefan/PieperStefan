# Eigene Suchmaschine fuer Open WebUI

SearXNG ist eine Metasuchmaschine: Sie fragt in Ihrem Auftrag bei Brave,
DuckDuckGo, Startpage, Wikipedia und anderen an, wirft Werbung und Tracker
weg und gibt Ihnen das Ergebnis zurueck. Kein Konto, kein API-Schluessel,
keine Kosten. Sie betreiben den "Anbieter" selbst.

## Einrichten

1. Ordner auf den Mac Studio kopieren, dann darin:

   ```bash
   echo "SEARXNG_SECRET=$(openssl rand -hex 32)" > .env
   docker compose up -d
   ```

2. Pruefen, ob die JSON-Schnittstelle antwortet - das ist der Punkt,
   an dem die meisten Installationen scheitern:

   ```bash
   curl "http://localhost:8088/search?q=test&format=json" | head -c 300
   ```

   Kommt JSON zurueck: gut. Kommt 403: in `searxng/settings.yml` fehlt
   `- json` unter `search.formats`, oder der Limiter ist noch an.

3. In Open WebUI: Admin Panel -> Settings -> Web Search
   - Web Search einschalten
   - Suchmaschine: **searxng**
   - Query URL eintragen (siehe unten)

## Die richtige Query URL

Je nachdem, wie Ihr Open WebUI laeuft:

| Open WebUI laeuft ... | Query URL |
|---|---|
| direkt auf dem Mac (nicht in Docker) | `http://localhost:8088/search?q=<query>` |
| in Docker, im selben Compose-Netz | `http://searxng:8080/search?q=<query>` |

Der Platzhalter `<query>` muss woertlich so dastehen.

Laeuft Ihr Open WebUI bereits als eigener Container, haengen Sie ihn
einmalig ins selbe Netz - das aendert nichts an seinen Daten:

```bash
docker network connect suche open-webui
```

## Danach

Im Chat die Web-Suche pro Unterhaltung aktivieren (Globus-Symbol
beziehungsweise Plus im Eingabefeld). Ohne das antwortet das Modell
weiter aus dem Gedaechtnis.

## Wenn Treffer fehlen

Es laeuft bewusst die Standard-Engineliste von SearXNG - darin sind
Brave, DuckDuckGo, Startpage, Wikipedia und viele weitere bereits
enthalten. Ein eigener `engines:`-Block ist nicht noetig und birgt
das Risiko, dass ein Tippfehler im Namen den Start verhindert.

Einzelne Engines sperren zeitweise (Google blockt Abfragen von einer
einzelnen Privatadresse besonders schnell). Welche gerade klemmt,
zeigt:

```bash
docker compose logs -f searxng
```

Stoerende Engines schalten Sie am einfachsten in der Weboberflaeche
unter http://localhost:8088/preferences ab. Erst wenn Sie das dauerhaft
festschreiben wollen, lohnt ein `engines:`-Block in der settings.yml -
die gueltigen Namen stehen dann in der SearXNG-Dokumentation.
