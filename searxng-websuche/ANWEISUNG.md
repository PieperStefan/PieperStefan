Richte auf diesem Mac eine eigene Websuche für Open WebUI ein, damit meine
lokalen Ollama-Modelle aktuelle Informationen nutzen können. Ich will dafür
kein Konto, keinen API-Schlüssel und keine laufenden Kosten — also SearXNG
selbst gehostet.

Arbeite das bitte komplett ab und melde mir am Ende, was läuft.

## 1. Vorbedingungen prüfen

- Läuft Docker? (`docker info`)
- Ist Port 8088 frei? (`lsof -iTCP:8088 -sTCP:LISTEN`)
  Falls belegt, nimm den nächsten freien Port und verwende ihn unten durchgängig.
- Läuft Open WebUI als Docker-Container oder nativ auf dem Mac?
  (`docker ps --format '{{.Names}}'` und `lsof -iTCP:8080 -sTCP:LISTEN`)
  Das Ergebnis brauchst du in Schritt 5.

## 2. Ordner und Dateien anlegen

Lege `~/searxng/` an, darin den Unterordner `searxng/`.

`~/searxng/docker-compose.yml`:

```yaml
services:
  searxng:
    image: searxng/searxng:latest
    container_name: searxng
    restart: unless-stopped
    ports:
      - "127.0.0.1:8088:8080"
    volumes:
      - ./searxng:/etc/searxng:rw
    environment:
      - SEARXNG_BASE_URL=http://localhost:8088/
      - SEARXNG_SECRET=${SEARXNG_SECRET:?Bitte .env anlegen}
    cap_drop:
      - ALL
    cap_add:
      - CHOWN
      - SETGID
      - SETUID
    logging:
      driver: json-file
      options:
        max-size: "1m"
        max-file: "1"
    networks:
      - suche

networks:
  suche:
    name: suche
```

`~/searxng/searxng/settings.yml`:

```yaml
use_default_settings: true

server:
  bind_address: "0.0.0.0"
  port: 8080
  secret_key: "wird-aus-SEARXNG_SECRET-gesetzt"
  limiter: false
  image_proxy: true

search:
  safe_search: 0
  default_lang: "de"
  formats:
    - html
    - json

ui:
  default_locale: de
```

Wichtig, das sind die beiden Stellen, an denen solche Installationen
üblicherweise scheitern:

- `formats` muss `json` enthalten. Fehlt es, antwortet SearXNG dem
  Open WebUI mit 403, und die Suche liefert stumm keine Ergebnisse —
  ohne sichtbare Fehlermeldung im Chat.
- `limiter` muss `false` sein, sonst blockt SearXNG die automatisierten
  Abfragen von Open WebUI.

Lege keinen eigenen `engines:`-Block an. Die Standardliste enthält Brave,
DuckDuckGo, Startpage, Wikipedia und viele weitere; ein Tippfehler in einem
Engine-Namen verhindert dagegen den Start.

## 3. Starten

```bash
cd ~/searxng
echo "SEARXNG_SECRET=$(openssl rand -hex 32)" > .env
docker compose up -d
```

## 4. Prüfen, bevor du weitergehst

```bash
curl "http://localhost:8088/search?q=test&format=json" | head -c 300
```

Kommt JSON zurück, ist SearXNG in Ordnung. Kommt 403 oder leeres Ergebnis,
korrigiere `formats` beziehungsweise `limiter` und starte neu
(`docker compose restart`). Gehe erst weiter, wenn dieser Test sauber ist.

## 5. Open WebUI verbinden

Läuft Open WebUI als Docker-Container, hänge ihn einmalig ins selbe Netz
(das verändert seine Daten nicht):

```bash
docker network connect suche <name-des-open-webui-containers>
```

Die Query URL hängt davon ab, wie Open WebUI läuft:

| Open WebUI läuft … | Query URL |
|---|---|
| nativ auf dem Mac | `http://localhost:8088/search?q=<query>` |
| als Docker-Container im Netz `suche` | `http://searxng:8080/search?q=<query>` |

Der Platzhalter `<query>` muss wörtlich so stehen bleiben.

Einstellen in Open WebUI unter: Admin Panel → Settings → Web Search
→ Web Search einschalten → Suchmaschine `searxng` → Query URL eintragen.

Das ist eine Weboberfläche, die du nicht selbst bedienen kannst. Sag mir
also genau, welche Query URL ich dort eintragen muss. Falls Open WebUI im
Container läuft, geht es alternativ über Umgebungsvariablen — die Namen
haben sich zwischen den Versionen geändert, prüfe sie gegen die aktuelle
Open-WebUI-Dokumentation, bevor du sie setzt.

## 6. Was du mir melden sollst

- ob SearXNG läuft und der JSON-Test bestanden ist
- die exakte Query URL, die ich in Open WebUI eintragen muss
- ob Open WebUI nativ oder im Container läuft
- den verwendeten Port, falls du von 8088 abweichen musstest
- den Hinweis, dass ich die Websuche im Chat zusätzlich pro Unterhaltung
  aktivieren muss (Globus-Symbol beziehungsweise Plus im Eingabefeld),
  sonst antwortet das Modell weiter aus dem Gedächtnis

## Hinweis zum Ressourcenverbrauch

Websuche schiebt schnell mehrere tausend Token Seiteninhalt in den Kontext.
Bei größeren Modellen kann das den Kontext sprengen und zum Abbruch führen.
Sag mir, welchen Wert `num_ctx` bei meinen Modellen hat und ob der Speicher
des Rechners dafür ausreicht.
