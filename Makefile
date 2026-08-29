TARGETS := zed claude telegram telegram_ios terminal kde konsole brave catcad darkroom

# The interpreter that builds the venv. macOS ships `python3` as 3.9, which
# predates the `X | None` annotations in grid.py, so a bare `python3` is not
# safe to assume. Take `python3` when it is new enough, and otherwise the
# newest versioned interpreter on PATH.
PYTHON := $(firstword $(foreach p,python3 python3.14 python3.13 python3.12 python3.11 python3.10,\
	$(shell $(p) -c 'import sys; raise SystemExit(sys.version_info < (3, 10))' 2>/dev/null && echo $(p))))

ifeq ($(PYTHON),)
$(error no python3 >= 3.10 on PATH — install one, for example `brew install python`)
endif

# Every recipe runs the venv interpreter, never the one above. Homebrew and
# Arch both mark their interpreters PEP 668 "externally managed", which makes
# `pip install --user` an error rather than a warning, so a repo-local venv is
# the one install path that works everywhere and touches nothing outside the
# checkout. .venv/ is already gitignored.
VENV := .venv
PY := $(VENV)/bin/python

.PHONY: all deps audit build palette install clean $(TARGETS)

all: audit build palette

# Contrast rules the targets rely on: chrome layers stay separable, every
# foreground clears 4.5:1 where it lands, ANSI stays dim<normal<bright, the
# ANSI rows split ink duty from fill duty, and every cell of a tint row looks
# equally bright. Every ratio prints an APCA Lc beside it, because WCAG 2
# overstates contrast at the dark end.
audit: deps
	$(PY) tools/audit.py

# Build the venv and install requirements.txt into it. The stamp carries the
# dependency on requirements.txt, so an edit there reinstalls and nothing else
# does.
deps: $(VENV)/.stamp

$(VENV)/.stamp: requirements.txt
	$(PYTHON) -m venv $(VENV)
	$(PY) -m pip install -q -r requirements.txt
	@touch $@

# Run every target builder. ayu-graphite.toml is the single source of truth
# (hand-edited); every target builder is a pure transformer.
build: deps
	$(PY) build.py

# Render palette.png swatch sheet from ayu-graphite.toml.
palette: deps
	$(PY) tools/render_palette.py

# Per-target builders, runnable independently when iterating on one target.
$(TARGETS): deps
	$(PY) $@/build.py

# Copy generated themes into the directories their applications read.
install: all
	./install.sh

# Every target writes into its own directory, so the generated files are the
# whole of `<target>/ayu-graphite.*`. ayu-graphite.toml is a source file (the
# hand-edited single source of truth) and sits at the root, out of that reach.
clean:
	rm -f $(addsuffix /ayu-graphite.*,$(TARGETS)) palette.png
	rm -rf brave/ayu-graphite
