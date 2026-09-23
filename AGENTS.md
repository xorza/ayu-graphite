# ayu-graphite

A variant of the Ayu dark theme with higher-contrast text and chrome, generated for Zed, Claude Code, Telegram (Desktop and iOS), macOS Terminal, KDE Plasma, Konsole, Brave, CatCad, and darkroom.

One palette, many targets. `ayu-graphite.toml` holds the inputs and the roles: `[base]` is seven colors that each give one hue, `[hues]` names the terminal-only hues, `[tints]` sets the perceived brightness of the `dim` row, `[ink]` names the grounds the `bright` row is solved to clear 4.5:1 on and the APCA floor the inks clear on the editor ground, the `normal` row sits midway between the two, `[ansi]` sets the APCA floor the `light` row (ANSI 1–6) is solved to clear as text, `[selection]` names the inks the selection fill is solved to carry, `[neutrals]` is the grey ladder, and `[semantic]` maps roles (`bg`, `accent`, `on_accent`, `ansi_*`, `syn_*`) onto primitives named by hue and tint (`red_bright`) or by rung (`gray_3`). `grid.py` solves the primitives from the inputs at load time — one L** per row, and per hue as much Oklab chroma as it holds there, up to 1.5 points above the lowest ceiling among the row's syntax hues, so a row is level in both; a terminal hue sits under that line and sets none, and each syntax hue's `bright` cell is its ink, placed alone at its own best brightness under one shared chroma line — and `palette.py` resolves the refs into a `Palette` dataclass that holds the schema for the whole repo. Four root modules are shared: `palette.py` (the schema and the loader), `grid.py` (the derivation), `color.py` (contrast, APCA Lc, Oklab, perceived lightness) and `emit.py` (the one hex parse, the formats more than one target writes, and the file writing). Each `<target>/build.py` is a pure transformer: load the TOML, write one theme file, import a root module but never a sibling. `tools/audit.py` checks the contrast invariants the targets silently depend on (chrome layers stay separable, foregrounds clear 4.5:1 where they land, ANSI stays dim < normal < bright with normal a visible step under bright, ANSI 1–6 clear the `[ansi]` APCA floor as text, every cell of a tint row looks equally bright and equally saturated, and the inks are equally saturated) and runs first in `make`, so a bad palette edit fails before any theme is written.

## Single source of truth

`ayu-graphite.toml` is the only palette definition. Do not introduce a second one.

## Build

```sh
make            # build every target
make zed        # one target at a time (also: claude, telegram, telegram_ios, terminal, kde, konsole, brave, catcad, darkroom)
make install    # build + copy/import into Zed, Claude, Terminal.app, KDE Plasma, Konsole, CatCad, darkroom (Telegram and Brave are manual)
```

## Adding a new target

Drop `<target>/build.py` next to its siblings (copy `claude/build.py` — it's the smallest), `from palette import Palette, load_palette`, then add `"<target>"` to `TARGETS` in the root `build.py` and to `TARGETS` in the `Makefile` — the per-target rule and the `clean` line come off that list. If it has an automatable install step, extend `install.sh`.
