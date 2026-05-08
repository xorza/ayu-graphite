# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Single source of truth

`ayu-mirage.toml` is the only palette definition. Do not introduce a second one.

- The palette schema (field names, types) lives once in `palette.py` (`Palette` dataclass + `load_palette`). Every builder and tool imports from there. Adding/renaming a token = edit `palette.py` + `ayu-mirage.toml` together; do not redeclare the dataclass elsewhere.
- Per-target builders (`zed/`, `claude/`, `telegram/`, `telegram_ios/`, `terminal/`, `kde/`, `konsole/`) are pure transformers: TOML in, target file out. No upstream JSON, no pipeline, no cross-builder imports.
- The contrast pipeline (gamma, S-curve, chrome flatten, accent desat, …) lives only in `tools/import_from_zed.py` and only runs on `make reseed`. Never call it from a target builder.
- No hardcoded hex literals in builders. Every color a target emits routes through a palette token; line-number ink, ANSI bright/dim siblings, scrollbar overlays, player cursor backgrounds, etc. all live in `ayu-mirage.toml` and `palette.py` like any other token. Adding a new role = add the field to both files, then reference it. Pure-black overlays use `overlay_black`; transparent layers use any palette color with `alpha(..., "00")`.

## Build

```sh
make            # build every target
make zed        # one target at a time (also: claude, telegram, telegram_ios, terminal, kde, konsole)
make install    # build + copy/import into Zed, Claude, Terminal.app, KDE Plasma, Konsole (Telegram is manual)
make reseed     # rewrite ayu-mirage.toml from tools/ayu-source.json — review the diff before committing
make fetch-source   # refresh tools/ayu-source.json from upstream Zed
```

Each builder is runnable directly (`python3 zed/build.py`) from any cwd; the `sys.path` shim at the top resolves `palette.py` at the repo root.

## Adding a new target

Drop `<target>/build.py` next to its siblings (copy `claude/build.py` — it's the smallest), `from palette import Palette, load_palette`, then add `"<target>"` to `TARGETS` in the root `build.py` and the matching `clean` line in the `Makefile`. If it has an automatable install step, extend `install.sh`.
