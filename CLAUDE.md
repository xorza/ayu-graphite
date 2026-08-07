## Single source of truth

`ayu-graphite.toml` is the only palette definition. Do not introduce a second one.

## Build

```sh
make            # build every target
make zed        # one target at a time (also: claude, telegram, telegram_ios, terminal, kde, konsole)
make install    # build + copy/import into Zed, Claude, Terminal.app, KDE Plasma, Konsole (Telegram is manual)
```

## Adding a new target

Drop `<target>/build.py` next to its siblings (copy `claude/build.py` — it's the smallest), `from palette import Palette, load_palette`, then add `"<target>"` to `TARGETS` in the root `build.py` and the matching `clean` line in the `Makefile`. If it has an automatable install step, extend `install.sh`.
