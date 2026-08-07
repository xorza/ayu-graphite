# ayu-graphite

A higher-contrast variant of [Ayu Graphite](https://github.com/dempfi/ayu) for [Zed](https://zed.dev), [Claude Code](https://claude.com/claude-code), Telegram, KDE Plasma / Konsole, and macOS Terminal.

## Layout

```
ayu-graphite.toml                        SINGLE SOURCE OF TRUTH — hand-edited semantic palette
palette.py                             dataclass + TOML loader (schema lives once)
build.py                               orchestrator (runs every target builder)
zed/build.py                           palette → ayu-graphite.json
claude/build.py                        palette → ayu-graphite.json
telegram/build.py                      palette → ayu-graphite.tdesktop-theme (zip)
telegram_ios/build.py                  palette → ayu-graphite.tgios-theme
terminal/build.py                      palette → ayu-graphite.terminal (macOS Terminal.app)
kde/build.py                           palette → ayu-graphite.colors (Plasma color scheme)
konsole/build.py                       palette → ayu-graphite.colorscheme
tools/ayu-source.json                  reference snapshot of upstream Zed Ayu (not read at build time)
tools/render_palette.py                renders palette.png — every token as a labeled swatch
tools/audit.py                         contrast rules — runs before every build, fails on a violation
Makefile                               convenience targets
```

The model is dead simple: `ayu-graphite.toml` is the only thing you edit. Every target builder is a pure transformer — it loads the TOML and writes its target file. No pipeline, no upstream JSON, no internal computation. To shift the theme, edit a hex value in the TOML and run `make`.

To add a new target (Sublime, iTerm, …), drop a `<target>/build.py` next to its sibling outputs (copy `claude/build.py` as a starting point — it's the smallest), and add the directory name to `TARGETS` in the root `build.py`.

## Usage

```sh
make            # audit the palette, then build every target
make audit      # contrast rules only
make install    # copy generated themes into their app dirs (Telegram is manual)
./install.sh    # same as `make install`, without make
```

`make audit` is the guard on the parts of the palette that targets silently
depend on: chrome layers that stack in one view stay separable, every
foreground clears 4.5:1 on the surfaces it lands on, and the 24 ANSI slots
stay distinct with dim &lt; normal &lt; bright per hue. It runs first in `make`,
so a palette edit that breaks one of those fails before any theme is written.

In Zed: settings → theme → "Ayu Graphite".
In Claude Code: `/config` → theme → "Ayu Graphite".
In Telegram Desktop: Settings → Chat Settings → scroll down → "Browse..." next to Custom theme, pick `telegram/ayu-graphite.tdesktop-theme`.
In Telegram iOS: send `telegram_ios/ayu-graphite.tgios-theme` to Saved Messages from any other client (or AirDrop it to your phone), tap the file, then "Apply Theme".
In macOS Terminal: double-click `terminal/ayu-graphite.terminal` (or `open terminal/ayu-graphite.terminal`) — Terminal imports it as a profile. Then Terminal → Settings → Profiles → "Ayu Graphite" → "Default" to make it the default.

## Claude port

After processing the Zed theme, `build.py` maps its values into Claude Code's custom-theme schema (see `build_claude` for the mapping table). Two manual fixes are baked in:

- `suggestion` ← `warning` so the highlighted row in the slash-command picker is visible.
- `userMessageBackground` ← `element.background` so prompts stand out from the editor background.

## Telegram port

`build_telegram` in `build.py` emits a `.tdesktop-theme` palette (~50 keys covering window chrome, sidebar, chat list, message bubbles, buttons, scrollbar, mentions). Telegram Desktop falls back to its dark defaults for any constant we don't define. Telegram supports `#rrggbbaa`, but every value here is opaque (alpha is stripped on the way out, same as the Claude port).

The output is actually a small zip archive (Telegram still expects the `.tdesktop-theme` extension) containing `colors.tdesktop-theme` plus a solid-color `background.png` matching `windowBg`. That overrides Telegram's default Star Wars chat wallpaper with a flat dark panel. The PNG is generated inline via `zlib` — no Pillow dependency.
