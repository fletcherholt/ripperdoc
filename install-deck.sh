#!/usr/bin/env bash
# Registers Night City Save Editor in the Steam Deck / Linux app menu with its
# icon, so it shows up properly (no blank question mark) and can be added to
# Steam as a non-Steam game. Run once from Desktop Mode.
set -e
cd "$(dirname "$0")"
APP="$PWD"
ICON_NAME="night-city-save-editor"
mkdir -p "$HOME/.local/share/applications" "$HOME/.local/share/icons/hicolor/512x512/apps" "$HOME/.local/share/icons/hicolor/scalable/apps"
cp assets/icon-512.png "$HOME/.local/share/icons/hicolor/512x512/apps/$ICON_NAME.png"
cp assets/icon.svg     "$HOME/.local/share/icons/hicolor/scalable/apps/$ICON_NAME.svg"
cat > "$HOME/.local/share/applications/$ICON_NAME.desktop" <<DESK
[Desktop Entry]
Type=Application
Name=Night City Save Editor
Comment=Cyberpunk 2077 save editor
Exec=$APP/run-deck.sh
Icon=$ICON_NAME
Terminal=false
Categories=Game;Utility;
DESK
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
gtk-update-icon-cache "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
echo "Installed. Find 'Night City Save Editor' in your app menu, or add it to Steam as a non-Steam game."
