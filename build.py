#!/usr/bin/env python3
"""Run every target builder.

Each one reads ayu-graphite.toml — the hand-edited single source of truth —
and writes its own theme file. There is no order dependency between them, so
this script just runs them all for convenience. Nothing here writes back to
the TOML."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TARGETS = ("zed", "claude", "telegram", "telegram_ios", "terminal", "kde",
           "konsole", "brave", "catcad", "darkroom")


def main() -> None:
    for target in TARGETS:
        script = os.path.join(HERE, target, "build.py")
        subprocess.run([sys.executable, script], check=True)


if __name__ == "__main__":
    main()
