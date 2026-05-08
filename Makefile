.PHONY: all deps build zed claude telegram telegram_ios terminal kde konsole reseed install fetch-source clean

all: build

# Install python deps (tomli on python <3.11). Idempotent.
deps:
	python3 -m pip install --user -q -r requirements.txt

# Run every target builder. ayu-mirage.toml is the single source of truth
# (hand-edited); the three target builders are pure transformers.
build: deps
	python3 build.py

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

# One-shot: re-seed ayu-mirage.toml from upstream tools/ayu-source.json by
# running the legacy contrast pipeline. Review the diff before committing.
reseed:
	python3 tools/import_from_zed.py

# Copy generated themes into Zed and Claude theme dirs.
install: all
	./install.sh

# Refresh the upstream Zed Ayu source.
fetch-source:
	curl -fsSL https://raw.githubusercontent.com/zed-industries/zed/main/assets/themes/ayu/ayu.json > tools/ayu-source.json
	@echo "updated tools/ayu-source.json"

# ayu-mirage.toml is a source file (hand-edited single source of truth);
# never delete it here.
clean:
	rm -f zed/ayu-mirage-high-contrast.json claude/ayu-mirage.json telegram/ayu-mirage.tdesktop-theme telegram_ios/ayu-mirage.tgios-theme terminal/ayu-mirage.terminal kde/ayu-mirage.colors konsole/ayu-mirage.colorscheme
