# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Single source of truth

`ayu-graphite.toml` is the only palette definition. Do not introduce a second one.

- The palette schema (field names, types) lives once in `palette.py` (`Palette` dataclass + `load_palette`). Every builder and tool imports from there. Adding/renaming a token = edit `palette.py` + `ayu-graphite.toml` together; do not redeclare the dataclass elsewhere.
- Per-target builders (`zed/`, `claude/`, `telegram/`, `telegram_ios/`, `terminal/`, `kde/`, `konsole/`) are pure transformers: TOML in, target file out. No upstream JSON, no pipeline, no cross-builder imports.
- `tools/ayu-source.json` is kept only as a structural reference for upstream Zed key names — nothing reads it at build time.
- No hardcoded hex literals in builders. Every color a target emits routes through a palette token; line-number ink, ANSI bright/dim siblings, scrollbar overlays, player cursor backgrounds, etc. all live in `ayu-graphite.toml` and `palette.py` like any other token. Adding a new role = add the field to both files, then reference it. Pure-black overlays use `overlay_black`; transparent layers use any palette color with `alpha(..., "00")`.
- Anything drawn on a bright fill (`accent`, `success`, `warning`, `error`) uses `on_accent`, never `text` — `text` on `accent` is 1.28:1. Selected rows use `selection_bg`/`selection_fg` in every target, not a per-target grey.
- Terminal targets read the `ansi_*` rows verbatim. Don't hand-pick syntax or status colors into ANSI slots; that's how bright red became plain red and Faint yellow became grey.
- `tools/audit.py` encodes those rules and runs first in `make`. If a palette edit trips it, fix the palette — don't relax the rule to match. Narrowing a check is only right when it was asserting a pairing no target actually emits.

## Build

```sh
make            # build every target
make zed        # one target at a time (also: claude, telegram, telegram_ios, terminal, kde, konsole)
make install    # build + copy/import into Zed, Claude, Terminal.app, KDE Plasma, Konsole (Telegram is manual)
```

Each builder is runnable directly (`python3 zed/build.py`) from any cwd; the `sys.path` shim at the top resolves `palette.py` at the repo root.

## Adding a new target

Drop `<target>/build.py` next to its siblings (copy `claude/build.py` — it's the smallest), `from palette import Palette, load_palette`, then add `"<target>"` to `TARGETS` in the root `build.py` and the matching `clean` line in the `Makefile`. If it has an automatable install step, extend `install.sh`.
