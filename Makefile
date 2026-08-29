TARGETS := zed claude telegram telegram_ios terminal kde konsole brave catcad darkroom

# macOS ships `python3` as 3.9, which predates both the `X | None` annotations
# and the stdlib tomllib this repo uses, so a bare `python3` recipe dies in
# grid.py before any target is written. Take `python3` when it is new enough,
# and otherwise the newest versioned interpreter on PATH.
PYTHON := $(firstword $(foreach p,python3 python3.14 python3.13 python3.12 python3.11 python3.10,\
	$(shell $(p) -c 'import sys; raise SystemExit(sys.version_info < (3, 10))' 2>/dev/null && echo $(p))))

ifeq ($(PYTHON),)
$(error no python3 >= 3.10 on PATH — install one, for example `brew install python`)
endif

.PHONY: all deps audit build palette install clean $(TARGETS)

all: audit build palette

# Contrast rules the targets rely on: chrome layers stay separable, every
# foreground clears 4.5:1 where it lands, ANSI stays dim<normal<bright, the
# ANSI rows split ink duty from fill duty, and every cell of a tint row looks
# equally bright. Every ratio prints an APCA Lc beside it, because WCAG 2
# overstates contrast at the dark end.
audit: deps
	$(PYTHON) tools/audit.py

# Install python deps (tomli on python <3.11). Idempotent.
# On Python >=3.11, tomllib is stdlib and there's nothing to install, so
# skip pip entirely — avoids PEP 668 "externally-managed-environment" errors
# on distros like Arch where system pip is locked down.
deps:
	@$(PYTHON) -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)' || \
		$(PYTHON) -m pip install --user -q -r requirements.txt

# Run every target builder. ayu-graphite.toml is the single source of truth
# (hand-edited); every target builder is a pure transformer.
build: deps
	$(PYTHON) build.py

# Render palette.png swatch sheet from ayu-graphite.toml.
palette: deps
	$(PYTHON) tools/render_palette.py

# Per-target builders, runnable independently when iterating on one target.
$(TARGETS): deps
	$(PYTHON) $@/build.py

# Copy generated themes into the directories their applications read.
install: all
	./install.sh

# Every target writes into its own directory, so the generated files are the
# whole of `<target>/ayu-graphite.*`. ayu-graphite.toml is a source file (the
# hand-edited single source of truth) and sits at the root, out of that reach.
clean:
	rm -f $(addsuffix /ayu-graphite.*,$(TARGETS)) palette.png
	rm -rf brave/ayu-graphite
