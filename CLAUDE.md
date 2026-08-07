# ayu-graphite

A higher-contrast variant of the Ayu dark theme, generated for Zed, Claude Code, Telegram (Desktop and iOS), macOS Terminal, KDE Plasma, Konsole, and Brave.

One palette, many targets. `ayu-graphite.toml` names every color twice — `[primitives]` are hex values named by hue and brightness step, `[semantic]` maps roles (`bg`, `accent`, `on_accent`, `ansi_*`, `syn_*`) onto them — and `palette.py` resolves the refs into a `Palette` dataclass that holds the schema for the whole repo. Each `<target>/build.py` is a pure transformer: load the TOML, write one theme file, import nothing from a sibling. `tools/audit.py` checks the contrast invariants the targets silently depend on (chrome layers stay separable, foregrounds clear 4.5:1 where they land, ANSI stays dim < normal < bright) and runs first in `make`, so a bad palette edit fails before any theme is written.

## Single source of truth

`ayu-graphite.toml` is the only palette definition. Do not introduce a second one.

## Build

```sh
make            # build every target
make zed        # one target at a time (also: claude, telegram, telegram_ios, terminal, kde, konsole, brave)
make install    # build + copy/import into Zed, Claude, Terminal.app, KDE Plasma, Konsole (Telegram is manual)
```

## Adding a new target

Drop `<target>/build.py` next to its siblings (copy `claude/build.py` — it's the smallest), `from palette import Palette, load_palette`, then add `"<target>"` to `TARGETS` in the root `build.py` and the matching `clean` line in the `Makefile`. If it has an automatable install step, extend `install.sh`.
