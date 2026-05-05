.PHONY: all build install fetch-source clean

all: build

build:
	python3 build.py

# Symlink generated themes into Zed and Claude theme dirs.
install: all
	mkdir -p $$HOME/.config/zed/themes $$HOME/.claude/themes
	ln -sf $(CURDIR)/zed/ayu-mirage-high-contrast.json $$HOME/.config/zed/themes/ayu-mirage-high-contrast.json
	ln -sf $(CURDIR)/claude/ayu-mirage.json $$HOME/.claude/themes/ayu-mirage.json
	@echo "linked themes into ~/.config/zed/themes and ~/.claude/themes"

# Refresh the upstream Zed Ayu source.
fetch-source:
	curl -fsSL https://raw.githubusercontent.com/zed-industries/zed/main/assets/themes/ayu/ayu.json > src/ayu-source.json
	@echo "updated src/ayu-source.json"

clean:
	rm -f zed/ayu-mirage-high-contrast.json claude/ayu-mirage.json
