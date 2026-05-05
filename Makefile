.PHONY: all palette themes install fetch-source clean

all: themes

# Run the contrast pipeline against src/ayu-source.json. Produces the Zed
# theme and the shared palette/ayu-mirage.toml.
palette:
	python3 src/build_palette.py

# Read palette/ayu-mirage.toml and produce the smaller targets (Claude,
# Telegram). Implicit dependency on palette via the file.
themes: palette
	python3 build.py

# Copy generated themes into Zed and Claude theme dirs.
install: all
	./install.sh

# Refresh the upstream Zed Ayu source.
fetch-source:
	curl -fsSL https://raw.githubusercontent.com/zed-industries/zed/main/assets/themes/ayu/ayu.json > src/ayu-source.json
	@echo "updated src/ayu-source.json"

clean:
	rm -f zed/ayu-mirage-high-contrast.json claude/ayu-mirage.json telegram/ayu-mirage.tdesktop-theme ayu-mirage.toml
