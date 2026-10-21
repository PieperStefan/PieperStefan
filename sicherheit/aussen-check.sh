#!/bin/bash
# Wächter: Ist irgendetwas bei mir vom Internet aus erreichbar?
# Prüft nur, ändert nichts. Meldet sich per Mitteilung, wenn etwas offen ist.
#
# Aufruf von Hand:  ~/sicherheit/aussen-check.sh
# Bericht:          ~/Library/Logs/aussen-check-letzter.txt
# Verlauf:          ~/Library/Logs/aussen-check.log

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"

BERICHT="$HOME/Library/Logs/aussen-check-letzter.txt"
VERLAUF="$HOME/Library/Logs/aussen-check.log"
ALARME=()
HINWEISE=()

alarm()   { ALARME+=("$1");   echo "ALARM:   $1"; }
hinweis() { HINWEISE+=("$1"); echo "HINWEIS: $1"; }
ok()      { echo "OK:      $1"; }

tailscale_cli() {
  if command -v tailscale >/dev/null 2>&1; then
    tailscale "$@"
  elif [ -x /Applications/Tailscale.app/Contents/MacOS/Tailscale ]; then
    /Applications/Tailscale.app/Contents/MacOS/Tailscale "$@"
  else
    return 127
  fi
}

{
echo "Aussen-Check $(date '+%d.%m.%Y %H:%M') auf $(scutil --get ComputerName 2>/dev/null || hostname)"
echo "================================================================"

# 1. Öffentliche Adresse und was das Internet dort sieht (Shodan-Datenbank)
echo; echo "--- 1. Oeffentliche Adresse ---"
IP4=$(curl -4 -s -m 10 https://api.ipify.org)
IP6=$(curl -6 -s -m 10 https://api64.ipify.org)
if [ -n "$IP4" ]; then
  echo "IPv4: $IP4"
  SHODAN=$(curl -s -m 15 "https://internetdb.shodan.io/$IP4")
  PORTS=$(echo "$SHODAN" | grep -o '"ports":\[[^]]*\]' | sed 's/"ports":\[//; s/\]//')
  VULNS=$(echo "$SHODAN" | grep -o '"vulns":\[[^]]*\]' | sed 's/"vulns":\[//; s/\]//')
  if [ -n "$PORTS" ]; then
    alarm "Das Internet sieht offene Ports auf $IP4: $PORTS (Quelle: Shodan, kann einige Tage alt sein)"
    [ -n "$VULNS" ] && alarm "Bekannte Schwachstellen auf $IP4: $VULNS"
  elif echo "$SHODAN" | grep -q "No information"; then
    ok "Shodan kennt keine offenen Ports auf $IP4"
  else
    hinweis "Shodan-Abfrage ohne klares Ergebnis: $SHODAN"
  fi
else
  hinweis "Oeffentliche IPv4-Adresse nicht ermittelbar"
fi
if [ -n "$IP6" ] && [ "$IP6" != "$IP4" ]; then
  echo "IPv6: $IP6"
  hinweis "IPv6 ist aktiv. Geraete haben eigene weltweite Adressen; der Router muss eingehende IPv6-Verbindungen blockieren (im Router pruefen)."
fi

# 2. Tailscale Funnel = Dienst oeffentlich im Internet
echo; echo "--- 2. Tailscale ---"
TS_FUNNEL=$(tailscale_cli funnel status 2>&1); TS_RC=$?
if [ $TS_RC -eq 127 ]; then
  hinweis "Tailscale-Befehl nicht gefunden"
else
  echo "$TS_FUNNEL"
  if echo "$TS_FUNNEL" | grep -qi "funnel on"; then
    alarm "Tailscale Funnel ist AN: Dienste dieses Macs sind oeffentlich im Internet"
  else
    ok "Tailscale Funnel ist aus (Dienste nur im eigenen Tailnet)"
  fi
fi

# 3. UPnP: Haben Geraete selbst Ports am Router geoeffnet?
echo; echo "--- 3. Portfreigaben per UPnP am Router ---"
if ! command -v upnpc >/dev/null 2>&1 && command -v brew >/dev/null 2>&1; then
  brew install miniupnpc >/dev/null 2>&1
fi
if command -v upnpc >/dev/null 2>&1; then
  UPNP=$(upnpc -l 2>&1)
  if echo "$UPNP" | grep -qi "No IGD"; then
    ok "Router bietet kein UPnP an (gut)"
  else
    MAPS=$(echo "$UPNP" | grep -E '^ *[0-9]+ +(TCP|UDP) ')
    if [ -n "$MAPS" ]; then
      echo "$MAPS"
      alarm "Am Router sind per UPnP Ports nach aussen geoeffnet (siehe Liste)"
    else
      hinweis "UPnP ist am Router eingeschaltet, aktuell ohne Freigaben. Besser ganz abschalten."
    fi
  fi
else
  hinweis "upnpc nicht verfuegbar (brew install miniupnpc)"
fi

# 4. Firewall dieses Macs
echo; echo "--- 4. Firewall ---"
FW=$(/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate 2>&1)
echo "$FW"
if echo "$FW" | grep -qiE "disabled|deaktiviert|State = 0"; then
  alarm "Firewall des Macs ist AUS"
else
  ok "Firewall ist an"
fi

# 5. Dienste, die auf allen Netzwerkschnittstellen lauschen
echo; echo "--- 5. Dienste dieses Macs, die im ganzen Netz lauschen ---"
lsof -iTCP -sTCP:LISTEN -n -P 2>/dev/null | awk 'NR>1 && ($9 ~ /^\*:/ || $9 ~ /^0\.0\.0\.0:/) {print $1, $9}' | sort -u
echo "(nur ein Problem, wenn einer davon per Portfreigabe, UPnP oder Funnel nach aussen geht)"

# Zusammenfassung
echo; echo "================================================================"
if [ ${#ALARME[@]} -eq 0 ]; then
  echo "ERGEBNIS: Nichts von aussen erreichbar gefunden. ${#HINWEISE[@]} Hinweis(e)."
else
  echo "ERGEBNIS: ${#ALARME[@]} ALARM(E)"
  printf ' - %s\n' "${ALARME[@]}"
fi
} > "$BERICHT" 2>&1

# Alarme in den Verlauf und als Mitteilung
ANZ=$(grep -c '^ALARM:' "$BERICHT")
echo "$(date '+%F %T') Alarme: $ANZ" >> "$VERLAUF"
if [ "$ANZ" -gt 0 ]; then
  grep '^ALARM:' "$BERICHT" >> "$VERLAUF"
  osascript -e "display notification \"$ANZ Fund(e) - Bericht: Logs/aussen-check-letzter.txt\" with title \"Achtung: von aussen erreichbar\" sound name \"Basso\"" 2>/dev/null
fi
cat "$BERICHT"
exit $(( ANZ > 0 ? 1 : 0 ))
