# ayu-mirage-contrast

A higher-contrast variant of [Ayu Mirage](https://github.com/dempfi/ayu) for [Zed](https://zed.dev) and [Claude Code](https://claude.com/claude-code), generated from the upstream Zed theme by a small Python pipeline.

## Layout

```
src/ayu-source.json                    upstream Zed Ayu theme (Mirage + Dark, both variants)
ayu-mirage.toml                        generated semantic palette (contract for downstream targets)
build.py                               orchestrator — runs every target builder
zed/build.py                           contrast pipeline; emits zed theme + palette TOML
zed/ayu-mirage-high-contrast.json      generated Zed theme
claude/build.py                        reads palette, emits Claude theme
claude/ayu-mirage.json                 generated Claude theme
telegram/build.py                      reads palette, emits Telegram theme
telegram/ayu-mirage.tdesktop-theme     generated Telegram Desktop palette
Makefile                               convenience targets
```

Each target has its own `build.py` next to its outputs:

1. **`zed/build.py`** runs the contrast pipeline (`GAMMA`, `K_BG`, chrome flatten, accent desat, border darken, etc.) against `src/ayu-source.json`. Output: the full Zed theme (`zed/ayu-mirage-high-contrast.json`) and the semantic palette `ayu-mirage.toml` extracted from the processed style.
2. **`claude/build.py`** and **`telegram/build.py`** read `ayu-mirage.toml` and emit their target. They never look at upstream Zed JSON.

`build.py` at the root is just an orchestrator — it shells out to the three target scripts in order (`zed` first, since it writes the palette). Each target builder is self-contained: you can run any one of them alone (`python3 telegram/build.py`) when iterating, as long as the palette TOML already exists.

Zed gets its own pipeline because it needs the full upstream key set (~600 keys: `players[]`, `terminal.ansi.*`, every `syntax.*`, etc.), not just palette tokens. Targets that *do* fit in ~30 semantic tokens (Claude, Telegram) consume the palette directly.

To add a new target (Sublime, iTerm, …), drop a `<target>/build.py` next to its sibling outputs and add the directory name to `TARGETS` in the root `build.py`.

## Usage

```sh
make            # build both themes
make install    # copy generated themes into ~/.config/zed/themes and ~/.claude/themes
./install.sh    # same as `make install`, without make
make fetch-source   # refresh src/ayu-source.json from zed-industries/zed main
```

In Zed: settings → theme → "Ayu Mirage High Contrast".
In Claude Code: `/config` → theme → "Ayu Mirage".
In Telegram Desktop: Settings → Chat Settings → scroll down → "Browse..." next to Custom theme, pick `telegram/ayu-mirage.tdesktop-theme`.

## Tuning

Knobs at the top of `zed/build.py`:

| Knob | Effect |
|---|---|
| `GAMMA` | > 1 brightens midtones (lifts dark backgrounds). |
| `K_BG` | S-curve strength on chrome — stronger means deeper blacks and brighter chrome highs. |
| `K_FG` | S-curve strength on foreground — kept lower so saturated channels don't clamp to 255. |
| `K_DIAG` | S-curve strength on diagnostic tints (`info.background`, `error.background`, …). Gentler than `K_BG` so the dim channel doesn't clip to 0 and oversaturate. |
| `MID` | S-curve midpoint. Lower than 0.5 because the theme is dark-leaning. |
| `BG_SAT` | Chroma kept on chrome backgrounds. 0 = pure neutral gray. |
| `FG_SAT` | Chroma multiplier on foreground/accent colors. |
| `FG_LIGHT` | Lightness multiplier on chromatic foreground. < 1 deepens pastels into vivid; > 1 brightens toward white. |
| `CHROME_TARGET` | RGB component for the mid-gray every chrome value lerps toward. |
| `CHROME_COMPRESS` | How hard chrome lerps toward the target. 0 = preserve original spread; 1 = all chrome becomes the same gray. |

## Pipeline

1. Per-channel: gamma lift, then S-curve around `MID`.
2. Chrome keys (window/panel/editor/terminal backgrounds): desaturate to `BG_SAT`, then lerp toward `CHROME_TARGET` by `CHROME_COMPRESS`. Keeps editor / panels / window chrome reading as one family instead of three different greys.
3. Foreground (text + accents + syntax): saturate first in HSL (so colors don't lose identity to channel clamping), deepen lightness by `FG_LIGHT`, then S-curve.
4. Diagnostic backgrounds (`error.background`, `warning.background`, `created.background`, …): contrast bump only, hue preserved — these tints are signal.

## Claude port

After processing the Zed theme, `build.py` maps its values into Claude Code's custom-theme schema (see `build_claude` for the mapping table). Two manual fixes are baked in:

- `suggestion` ← `warning` so the highlighted row in the slash-command picker is visible.
- `userMessageBackground` ← `element.background` so prompts stand out from the editor background.

## Telegram port

`build_telegram` in `build.py` emits a `.tdesktop-theme` palette (~50 keys covering window chrome, sidebar, chat list, message bubbles, buttons, scrollbar, mentions). Telegram Desktop falls back to its dark defaults for any constant we don't define. Telegram supports `#rrggbbaa`, but every value here is opaque (alpha is stripped on the way out, same as the Claude port).

The output is actually a small zip archive (Telegram still expects the `.tdesktop-theme` extension) containing `colors.tdesktop-theme` plus a solid-color `background.png` matching `windowBg`. That overrides Telegram's default Star Wars chat wallpaper with a flat dark panel. The PNG is generated inline via `zlib` — no Pillow dependency.
