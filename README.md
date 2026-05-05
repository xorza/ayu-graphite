# ayu-mirage-contrast

A higher-contrast variant of [Ayu Mirage](https://github.com/dempfi/ayu) for [Zed](https://zed.dev) and [Claude Code](https://claude.com/claude-code), generated from the upstream Zed theme by a small Python pipeline.

## Layout

```
src/ayu-source.json                  upstream Zed Ayu theme (Mirage + Dark, both variants)
build.py                             single pipeline: processes Zed theme + ports it to Claude
zed/ayu-mirage-high-contrast.json    generated Zed theme
claude/ayu-mirage.json               generated Claude theme
Makefile                             convenience targets
```

## Usage

```sh
make            # build both themes
make install    # symlink generated themes into ~/.config/zed/themes and ~/.claude/themes
make fetch-source   # refresh src/ayu-source.json from zed-industries/zed main
```

In Zed: settings → theme → "Ayu Mirage High Contrast".
In Claude Code: `/config` → theme → "Ayu Mirage".

## Tuning

Knobs at the top of `build.py`:

| Knob | Effect |
|---|---|
| `GAMMA` | > 1 brightens midtones (lifts dark backgrounds). |
| `K_BG` | S-curve strength on chrome — stronger means deeper blacks and brighter chrome highs. |
| `K_FG` | S-curve strength on foreground — kept lower so saturated channels don't clamp to 255. |
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
