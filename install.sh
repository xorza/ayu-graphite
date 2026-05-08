#!/usr/bin/env bash
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

zed_dir="$HOME/.config/zed/themes"
claude_dir="$HOME/.claude/themes"

install_file() {
    local src=$1 dst=$2
    mkdir -p "$(dirname "$dst")"
    rm -f "$dst"
    cp "$src" "$dst"
}

install_file "$here/zed/ayu-mirage-high-contrast.json" "$zed_dir/ayu-mirage-high-contrast.json"
install_file "$here/claude/ayu-mirage.json"            "$claude_dir/ayu-mirage.json"

echo "copied themes into $zed_dir and $claude_dir"



# KDE Plasma + Konsole (Linux only). Plasma reads color schemes from
# ~/.local/share/color-schemes; Konsole from ~/.local/share/konsole. Neither
# has a scriptable "set as default" — pick via System Settings → Colors and
# Konsole → Edit Profile → Appearance.
if [[ "$(uname)" == "Linux" ]]; then
    plasma_dir="$HOME/.local/share/color-schemes"
    konsole_dir="$HOME/.local/share/konsole"
    install_file "$here/kde/ayu-mirage.colors"          "$plasma_dir/ayu-mirage.colors"
    install_file "$here/konsole/ayu-mirage.colorscheme" "$konsole_dir/ayu-mirage.colorscheme"
    echo "copied themes into $plasma_dir and $konsole_dir"
fi

# Telegram Desktop has no scriptable theme-import path — load
# telegram/ayu-mirage.tdesktop-theme via Settings → Chat Settings → Custom theme.
echo "telegram/ayu-mirage.tdesktop-theme: load it manually via Telegram → Settings → Chat Settings"
