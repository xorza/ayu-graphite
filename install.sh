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

install_file "$here/zed/ayu-graphite.json" "$zed_dir/ayu-graphite.json"
install_file "$here/claude/ayu-graphite.json"            "$claude_dir/ayu-graphite.json"

echo "copied themes into $zed_dir and $claude_dir"



# KDE Plasma + Konsole (Linux only). Plasma reads color schemes from
# ~/.local/share/color-schemes; Konsole from ~/.local/share/konsole. Neither
# has a scriptable "set as default" — pick via System Settings → Colors and
# Konsole → Edit Profile → Appearance.
if [[ "$(uname)" == "Linux" ]]; then
    plasma_dir="$HOME/.local/share/color-schemes"
    konsole_dir="$HOME/.local/share/konsole"
    install_file "$here/kde/ayu-graphite.colors"          "$plasma_dir/ayu-graphite.colors"
    install_file "$here/konsole/ayu-graphite.colorscheme" "$konsole_dir/ayu-graphite.colorscheme"
    echo "copied themes into $plasma_dir and $konsole_dir"
fi

# Telegram Desktop has no scriptable theme-import path — load
# telegram/ayu-graphite.tdesktop-theme via Settings → Chat Settings → Custom theme.
echo "telegram/ayu-graphite.tdesktop-theme: load it manually via Telegram → Settings → Chat Settings"

# Brave only sideloads unpacked extensions through its own UI; dropping the
# directory into the profile's Extensions dir does nothing without a signature.
echo "brave/ayu-graphite: load it manually via brave://extensions → Developer mode → Load unpacked"
