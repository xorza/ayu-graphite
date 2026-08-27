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

# An application that reads its palette out of its own source tree — the table
# is embedded in the binary, so there is nothing to install into a config
# directory and nothing for the application to find at run time. Skipped when
# the checkout is absent.
install_into_checkout() {
    local src=$1 dir=$2
    if [[ -d "$dir" ]]; then
        install_file "$here/$src" "$dir/$(basename "$src")"
        echo "copied $src into $dir"
    else
        echo "$src: no checkout at $dir, skipped"
    fi
}

install_file "$here/zed/ayu-graphite.json"    "$zed_dir/ayu-graphite.json"
install_file "$here/claude/ayu-graphite.json" "$claude_dir/ayu-graphite.json"

echo "copied themes into $zed_dir and $claude_dir"

# macOS Terminal.app: never `open` the .terminal file — Terminal imports it as
# a *new* profile every time ("Ayu Graphite 1", "Ayu Graphite 2", ...). There is
# no on-disk profile to overwrite either; Terminal only reads profiles out of
# its own prefs, so -dict-add writes over the same-named one in place, and
# `killall cfprefsd` flushes the prefs daemon so Terminal sees it on next
# launch. A running Terminal rewrites all of its prefs on quit, clobbering this.
if [[ "$(uname)" == "Darwin" ]]; then
    if pgrep -xq Terminal; then
        echo "Terminal.app is running — quit it and re-run 'make install' to update its profile"
    else
        defaults write com.apple.Terminal "Window Settings" \
            -dict-add "Ayu Graphite" "$(cat "$here/terminal/ayu-graphite.terminal")"
        defaults write com.apple.Terminal "Default Window Settings" -string "Ayu Graphite"
        defaults write com.apple.Terminal "Startup Window Settings" -string "Ayu Graphite"
        killall cfprefsd || true
        echo "updated the 'Ayu Graphite' profile in Terminal.app — relaunch to see it"
    fi
fi

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

install_into_checkout catcad/ayu-graphite.ron   "$HOME/Projects/CatCad/catcad/src/look/palette"
install_into_checkout darkroom/ayu-graphite.ron "$HOME/Projects/Darkroom/darkroom/assets"

# The two targets with no scriptable import path at all. Telegram Desktop takes
# a theme only through its own settings dialog, and Brave only sideloads an
# unpacked extension through its own UI — dropping the directory into the
# profile's Extensions dir does nothing without a signature.
echo "telegram/ayu-graphite.tdesktop-theme: load it manually via Telegram → Settings → Chat Settings"
echo "brave/ayu-graphite: load it manually via brave://extensions → Developer mode → Load unpacked"
