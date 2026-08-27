.PHONY: all deps audit build palette zed claude telegram telegram_ios terminal kde konsole brave catcad install clean

all: audit build palette

# Contrast rules the targets rely on: chrome layers stay separable, every
# foreground clears 4.5:1 where it lands, ANSI stays dim<normal<bright, the
# ANSI rows split ink duty from fill duty, and every cell of a tint row looks
# equally bright. Every ratio prints an APCA Lc beside it, because WCAG 2
# overstates contrast at the dark end.
audit: deps
	python3 tools/audit.py

# Install python deps (tomli on python <3.11). Idempotent.
# On Python >=3.11, tomllib is stdlib and there's nothing to install, so
# skip pip entirely — avoids PEP 668 "externally-managed-environment" errors
# on distros like Arch where system pip is locked down.
deps:
	@python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' || \
		python3 -m pip install --user -q -r requirements.txt

# Run every target builder. ayu-graphite.toml is the single source of truth
# (hand-edited); the three target builders are pure transformers.
build: deps
	python3 build.py

# Render palette.png swatch sheet from ayu-graphite.toml.
palette: deps
	python3 tools/render_palette.py

# Per-target builders, runnable independently when iterating on one target.
zed:
	python3 zed/build.py

claude:
	python3 claude/build.py

telegram:
	python3 telegram/build.py

telegram_ios:
	python3 telegram_ios/build.py

terminal:
	python3 terminal/build.py

kde:
	python3 kde/build.py

konsole:
	python3 konsole/build.py

brave:
	python3 brave/build.py

catcad:
	python3 catcad/build.py

# Copy generated themes into Zed and Claude theme dirs.
install: all
	./install.sh

# ayu-graphite.toml is a source file (hand-edited single source of truth);
# never delete it here.
clean:
	rm -f zed/ayu-graphite.json claude/ayu-graphite.json telegram/ayu-graphite.tdesktop-theme telegram/ayu-graphite.tdesktop-theme.txt telegram_ios/ayu-graphite.tgios-theme terminal/ayu-graphite.terminal kde/ayu-graphite.colors konsole/ayu-graphite.colorscheme catcad/ayu-graphite.ron palette.png
	rm -rf brave/ayu-graphite
