.PHONY: all deps build palette zed claude telegram telegram_ios terminal kde konsole install clean

all: build palette

# Install python deps (tomli on python <3.11). Idempotent.
# On Python >=3.11, tomllib is stdlib and there's nothing to install, so
# skip pip entirely — avoids PEP 668 "externally-managed-environment" errors
# on distros like Arch where system pip is locked down.
deps:
	@python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' || \
		python3 -m pip install --user -q -r requirements.txt

# Run every target builder. ayu-mirage.toml is the single source of truth
# (hand-edited); the three target builders are pure transformers.
build: deps
	python3 build.py

# Render palette.png swatch sheet from ayu-mirage.toml.
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

# Copy generated themes into Zed and Claude theme dirs.
install: all
	./install.sh

# ayu-mirage.toml is a source file (hand-edited single source of truth);
# never delete it here.
clean:
	rm -f zed/ayu-mirage-high-contrast.json claude/ayu-mirage.json telegram/ayu-mirage.tdesktop-theme telegram/ayu-mirage.tdesktop-theme.txt telegram_ios/ayu-mirage.tgios-theme terminal/ayu-mirage.terminal kde/ayu-mirage.colors konsole/ayu-mirage.colorscheme palette.png
