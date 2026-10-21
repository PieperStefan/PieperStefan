#!/bin/bash
# Richtet den Aussen-Check auf diesem Mac ein: einmal sofort, danach täglich um 07:50.
set -e
QUELLE="https://raw.githubusercontent.com/PieperStefan/PieperStefan/claude/tender-volta-e8585x/sicherheit"
ZIEL="$HOME/sicherheit"
PLIST="$HOME/Library/LaunchAgents/com.pieper.aussen-check.plist"

mkdir -p "$ZIEL" "$HOME/Library/Logs"
curl -fsSL "$QUELLE/aussen-check.sh" -o "$ZIEL/aussen-check.sh"
chmod +x "$ZIEL/aussen-check.sh"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.pieper.aussen-check</string>
  <key>ProgramArguments</key>
  <array><string>/bin/bash</string><string>$ZIEL/aussen-check.sh</string></array>
  <key>StartCalendarInterval</key>
  <dict><key>Hour</key><integer>7</integer><key>Minute</key><integer>50</integer></dict>
  <key>RunAtLoad</key><false/>
  <key>StandardOutPath</key><string>$HOME/Library/Logs/aussen-check.out</string>
  <key>StandardErrorPath</key><string>$HOME/Library/Logs/aussen-check.out</string>
</dict>
</plist>
EOF

launchctl bootout gui/$(id -u) "$PLIST" 2>/dev/null || true
launchctl bootstrap gui/$(id -u) "$PLIST"
echo "Eingerichtet. Erster Lauf:"
echo
"$ZIEL/aussen-check.sh" || true
