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

# macOS Terminal.app: re-importing a .terminal that already exists in defaults
# is a no-op (or creates "Ayu Mirage 1" duplicates). We delete every prior
# Ayu-Mirage-flavored profile first, then `open` the fresh file so changes to
# the .terminal actually take effect on the next launch.
if [[ "$(uname)" == "Darwin" ]]; then
    osascript -e 'tell application "Terminal" to quit' 2>/dev/null || true
    sleep 0.5
    python3 - "$here/terminal/ayu-mirage.terminal" <<'PY'
"""Inject the profile straight into Terminal's prefs.

`open theme.terminal` makes Terminal merge / dedupe / number-suffix the import
unpredictably. Writing the profile dict directly into "Window Settings" via
defaults import sidesteps that, and `killall cfprefsd` flushes the prefs
daemon's cache so Terminal sees the new value on next launch."""
import re, subprocess, sys, plistlib
profile_path = sys.argv[1]
with open(profile_path, 'rb') as f:
    profile = plistlib.load(f)
out = subprocess.run(['defaults', 'export', 'com.apple.Terminal', '-'],
                     capture_output=True, check=True).stdout
d = plistlib.loads(out)
ws = d.setdefault('Window Settings', {})
stale = [k for k in list(ws) if re.match(r'(?i)ayu[\s-]?mirage', k)]
for k in stale:
    del ws[k]
ws['ayu-mirage'] = profile
d['Default Window Settings'] = 'ayu-mirage'
d['Startup Window Settings'] = 'ayu-mirage'
subprocess.run(['defaults', 'import', 'com.apple.Terminal', '-'],
               input=plistlib.dumps(d), check=True)
subprocess.run(['killall', 'cfprefsd'], check=False)
print(f"replaced Terminal profiles {stale or '[]'} with fresh ayu-mirage")
PY
    echo "imported into Terminal.app — relaunch it to see changes"
fi

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
