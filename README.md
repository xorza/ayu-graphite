# ayu-graphite

A higher-contrast variant of [Ayu](https://github.com/dempfi/ayu) for [Zed](https://zed.dev), [Claude Code](https://claude.com/claude-code), Telegram, KDE Plasma / Konsole, Brave, macOS Terminal, CatCad, and darkroom.

`ayu-graphite.toml` is the only thing you edit. It holds five base colors, three tint brightnesses, one grey ladder, and the roles that name cells of the grid those make. `grid.py` solves the grid when the file is loaded. Every target builder is a pure transformer — it loads the TOML and writes its theme file. To shift the theme, change a base color, a tint or a role and run `make`.

```
ayu-graphite.toml       SINGLE SOURCE OF TRUTH — base colors, tints, greys, roles
palette.py              dataclass + TOML loader (schema lives once)
grid.py                 solves the 5x3 grid and the grey ladder from the inputs
color.py                contrast, APCA Lc, Oklab, perceived lightness
emit.py                 the one hex parse, the shared formats, the file writing
build.py                orchestrator (runs every target builder)
zed/build.py            → ayu-graphite.json
claude/build.py         → ayu-graphite.json
telegram/build.py       → ayu-graphite.tdesktop-theme (zip)
telegram_ios/build.py   → ayu-graphite.tgios-theme
terminal/build.py       → ayu-graphite.terminal (macOS Terminal.app)
kde/build.py            → ayu-graphite.colors (Plasma color scheme)
konsole/build.py        → ayu-graphite.colorscheme
brave/build.py          → ayu-graphite/manifest.json (Chromium theme extension)
catcad/build.py         → ayu-graphite.ron (CatCad, neutralised greys)
darkroom/build.py       → ayu-graphite.ron (darkroom, one derived ground)
tools/audit.py          contrast rules — runs before every build, fails on a violation
tools/render_palette.py renders palette.png — every token as a labeled swatch
```

To add a target, drop a `<target>/build.py` next to its siblings (copy `claude/build.py` — it's the smallest) and add the directory name to `TARGETS` in the root `build.py` and to `TARGETS` in the `Makefile`. The Makefile builds its per-target rule and its `clean` line off that list.

## Usage

```sh
make            # audit the palette, then build every target
make audit      # contrast rules only
make install    # copy generated themes into their app dirs (Telegram and Brave are manual)
```

`make audit` guards what the targets silently depend on: chrome layers that stack in one view stay separable, every foreground clears 4.5:1 where it lands, the 24 ANSI slots stay distinct with dim &lt; normal &lt; bright per hue, the cyan row aside, which is the blue row again, and every cell of a tint row looks equally bright and equally saturated. It runs first, so a bad palette edit fails before any theme is written.

## Applying

- **Zed** — settings → theme → "Ayu Graphite".
- **Claude Code** — `/config` → theme → "Ayu Graphite".
- **KDE Plasma / Konsole** — System Settings → Colors, and Konsole → Edit Profile → Appearance.
- **Telegram Desktop** — Settings → Chat Settings → "Browse..." next to Custom theme, pick `telegram/ayu-graphite.tdesktop-theme`.
- **Telegram iOS** — send `telegram_ios/ayu-graphite.tgios-theme` to Saved Messages from another client (or AirDrop it), tap the file, "Apply Theme".
- **Brave** — `brave://extensions` → Developer mode → "Load unpacked" → `brave/ayu-graphite`. Brave's new-tab background images paint over `ntp_background`; turn them off in `brave://settings/newTab` for the flat panel.
- **macOS Terminal** — `make install` writes the profile into Terminal's own preferences and selects it. Quit Terminal first: a running one rewrites all of its preferences when it quits, over the top of the new profile. Do not open the `.terminal` file — Terminal imports it as a *new* profile on every open ("Ayu Graphite 1", "Ayu Graphite 2", ...), and the one you have selected stays as it was.
- **darkroom** — `make install` writes the table into the checkout at `~/Projects/Darkroom`; it is embedded at build time, so rebuild to see it. The palette carries one colour it does not take from a role: the graph ground sits a ramp step below `bg`, because darkroom stacks six chrome surfaces where the neutral ramp holds five.
- **CatCad** — `make install` writes the table into the checkout at `~/Projects/CatCad`; it is embedded at build time, so rebuild to see it. This is the one target whose greys are neutralised: a CAD viewport is mostly one large flat surface, so it states neutrality rather than inheriting whatever the ramp leans.
