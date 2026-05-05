#!/usr/bin/env python3
"""Build all theme outputs.

Runs the per-target builders in dependency order:

  zed/build.py       runs the contrast pipeline against src/ayu-source.json,
                     writes zed/*.json AND ayu-mirage.toml (palette).
  claude/build.py    reads ayu-mirage.toml, writes claude/*.json.
  telegram/build.py  reads ayu-mirage.toml, writes telegram/*.tdesktop-theme.

Each builder is a self-contained script — you can run any one of them directly
when iterating on a single target."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TARGETS = ("zed", "claude", "telegram")


def main() -> None:
    for target in TARGETS:
        script = os.path.join(HERE, target, "build.py")
        subprocess.run([sys.executable, script], check=True)


if __name__ == "__main__":
    main()
