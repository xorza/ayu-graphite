.PHONY: all build install fetch-source clean

all: build

build:
	python3 build.py

# Copy generated themes into Zed and Claude theme dirs.
install: all
	./install.sh

# Refresh the upstream Zed Ayu source.
fetch-source:
	curl -fsSL https://raw.githubusercontent.com/zed-industries/zed/main/assets/themes/ayu/ayu.json > src/ayu-source.json
	@echo "updated src/ayu-source.json"

clean:
	rm -f zed/ayu-mirage-high-contrast.json claude/ayu-mirage.json telegram/ayu-mirage.tdesktop-theme
