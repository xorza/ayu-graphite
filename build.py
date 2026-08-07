#!/usr/bin/env python3
"""Build all theme outputs.

Each per-target builder is independent: it reads ../ayu-graphite.toml (the
hand-edited single source of truth) and emits its own theme file. There is no
order dependency between them — this script just runs them all for convenience.

  zed/build.py          palette -> zed/ayu-graphite.json
  claude/build.py       palette -> claude/ayu-graphite.json
  telegram/build.py     palette -> telegram/ayu-graphite.tdesktop-theme
  telegram_ios/build.py palette -> telegram_ios/ayu-graphite.tgios-theme
  terminal/build.py     palette -> terminal/ayu-graphite.terminal
  kde/build.py          palette -> kde/ayu-graphite.colors
  konsole/build.py      palette -> konsole/ayu-graphite.colorscheme
  brave/build.py        palette -> brave/ayu-graphite/manifest.json

The TOML is hand-edited; nothing in this repo writes back to it."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TARGETS = ("zed", "claude", "telegram", "telegram_ios", "terminal", "kde",
           "konsole", "brave")


def main() -> None:
    for target in TARGETS:
        script = os.path.join(HERE, target, "build.py")
        subprocess.run([sys.executable, script], check=True)


if __name__ == "__main__":
    main()
