.PHONY: all build zed claude telegram install fetch-source clean

all: build

# Run every target builder in dependency order (zed first — it produces
# ayu-mirage.toml; claude/telegram consume it).
build:
	python3 build.py

# Per-target builders, runnable independently when iterating on one target.
zed:
	python3 zed/build.py

claude:
	python3 claude/build.py

telegram:
	python3 telegram/build.py

# Copy generated themes into Zed and Claude theme dirs.
install: all
	./install.sh

# Refresh the upstream Zed Ayu source.
fetch-source:
	curl -fsSL https://raw.githubusercontent.com/zed-industries/zed/main/assets/themes/ayu/ayu.json > src/ayu-source.json
	@echo "updated src/ayu-source.json"

clean:
	rm -f zed/ayu-mirage-high-contrast.json claude/ayu-mirage.json telegram/ayu-mirage.tdesktop-theme ayu-mirage.toml
