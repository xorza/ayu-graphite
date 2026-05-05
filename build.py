#!/usr/bin/env python3
"""Build a high-contrast Ayu Mirage for Zed and port it to Claude Code.

Reads src/ayu-source.json (upstream Zed Ayu themes file) and writes:
  zed/ayu-mirage-high-contrast.json   processed Zed theme
  claude/ayu-mirage.json              ported Claude Code theme

Pipeline per color:
  1. Per-channel: gamma lift (brightens), then S-curve around MID (boosts contrast).
     Chrome and foreground use different K (S-curve strength) so saturated
     foreground channels don't clamp to 255.
  2. Chrome (window/panel/editor backgrounds): desaturate toward gray,
     then lerp toward CHROME_TARGET to compress the layered range.
  3. Foreground / accents: saturate (HSL) and deepen lightness to turn
     pastels into vivid colors.
  4. Diagnostic backgrounds (error/warning/created/...): contrast bump only,
     hue preserved.

Manual fixes baked into the Claude port:
  - suggestion = warning yellow (highlighted slash-command picker row)
  - userMessageBackground = element.background (visible prompt block)
"""
import colorsys
import json
import os
import re

# ---- knobs ----
GAMMA  = 1.10   # > 1 brightens midtones (lifts dark backgrounds)
K_BG   = 1.40   # contrast boost for chrome (S-curve around MID)
K_FG   = 1.15   # contrast boost for foreground — kept lower so saturated channels don't clamp
MID    = 0.40   # midpoint of the S-curve (theme is dark, so < 0.5)
BG_SAT = 0.0    # chroma kept on chrome backgrounds (0 = pure gray)
FG_SAT = 1.30   # chroma multiplier for foreground/accent colors (> 1 = punchier)
FG_LIGHT = 0.88 # lightness multiplier for foreground (< 1 deepens / vivid; > 1 brightens / pastel)

# Chrome flattening: after channel adj + desat, lerp every chrome value toward
# CHROME_TARGET by CHROME_COMPRESS. 0 = preserve original spread; 1 = all chrome
# becomes the same gray.
CHROME_TARGET   = 45   # RGB component for the chrome mid-gray (~#2d2d2d)
CHROME_COMPRESS = 0.40

CHROME_KEYS = {
    "background", "editor.background", "editor.gutter.background",
    "editor.subheader.background", "editor.active_line.background",
    "editor.highlighted_line.background",
    "element.background", "surface.background", "elevated_surface.background",
    "panel.background", "status_bar.background", "title_bar.background",
    "title_bar.inactive_background", "tab_bar.background",
    "tab.inactive_background", "tab.active_background",
    "toolbar.background", "terminal.background",
    "scrollbar.track.background", "scrollbar.thumb.background",
    "scrollbar.thumb.hover_background",
    "terminal.ansi.black", "terminal.ansi.dim_black",
}

SAT_NEUTRAL_SUFFIXES = (".background", ".border")
SAT_NEUTRAL_KEYS = {
    "drop_target.background", "ghost_element.background",
    "search.match_background", "search.active_match_background",
    "editor.document_highlight.read_background",
    "editor.document_highlight.write_background",
}

HEX_RE = re.compile(r"#([0-9a-fA-F]{6})([0-9a-fA-F]{2})?")


def adj_channel(c: int, k: float) -> int:
    x = (c / 255) ** (1 / GAMMA)
    y = MID + (x - MID) * k
    return max(0, min(255, round(y * 255)))


def scale_sat(r: int, g: int, b: int, factor: float, light_factor: float = 1.0):
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    s = max(0.0, min(1.0, s * factor))
    if s > 0.3:
        l = max(0.0, min(1.0, l * light_factor))
    rr, gg, bb = colorsys.hls_to_rgb(h, l, s)
    return round(rr * 255), round(gg * 255), round(bb * 255)


def parse(s: str):
    m = HEX_RE.fullmatch(s)
    if not m:
        return None
    h = m.group(1)
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), (m.group(2) or "")


def fmt(r, g, b, a):
    return "#%02x%02x%02x%s" % (r, g, b, a)


def strip_alpha(c: str) -> str:
    """#rrggbbaa -> #rrggbb (Claude accepts only 6-digit hex)."""
    m = HEX_RE.fullmatch(c)
    return "#" + m.group(1).lower() if m else c


def is_diagnostic_bg(key: str) -> bool:
    if key in SAT_NEUTRAL_KEYS:
        return True
    return any(key.endswith(suf) for suf in SAT_NEUTRAL_SUFFIXES) and key not in CHROME_KEYS


def transform(value: str, key: str) -> str:
    p = parse(value)
    if not p:
        return value
    r, g, b, a = p
    if key in CHROME_KEYS:
        r, g, b = adj_channel(r, K_BG), adj_channel(g, K_BG), adj_channel(b, K_BG)
        r, g, b = scale_sat(r, g, b, BG_SAT)
        f = CHROME_COMPRESS
        r = round(r * (1 - f) + CHROME_TARGET * f)
        g = round(g * (1 - f) + CHROME_TARGET * f)
        b = round(b * (1 - f) + CHROME_TARGET * f)
    elif is_diagnostic_bg(key):
        r, g, b = adj_channel(r, K_BG), adj_channel(g, K_BG), adj_channel(b, K_BG)
    else:
        r, g, b = scale_sat(r, g, b, FG_SAT, FG_LIGHT)
        r, g, b = adj_channel(r, K_FG), adj_channel(g, K_FG), adj_channel(b, K_FG)
    return fmt(r, g, b, a)


def walk(node, key: str = ""):
    if isinstance(node, dict):
        return {k: walk(v, k) for k, v in node.items()}
    if isinstance(node, list):
        return [walk(v, key) for v in node]
    if isinstance(node, str):
        return transform(node, key)
    return node


def build_zed(src: dict) -> dict:
    theme = next(t for t in src["themes"] if t["name"] == "Ayu Mirage")
    theme = walk(theme)
    theme["name"] = "Ayu Mirage High Contrast"
    theme["appearance"] = "dark"
    return {
        "$schema": "https://zed.dev/schema/themes/v0.2.0.json",
        "name": "Ayu Mirage High Contrast",
        "author": "xxorza",
        "themes": [theme],
    }


def build_claude(zed_theme: dict) -> dict:
    style = zed_theme["themes"][0]["style"]
    syntax = style["syntax"]

    def s(key):
        return strip_alpha(style[key])

    def syn(key):
        return strip_alpha(syntax[key]["color"])

    overrides = {
        "background":              s("editor.background"),
        "userMessageBackground":   s("element.background"),
        "bashMessageBackgroundColor": s("element.background"),
        "memoryBackgroundColor":   s("element.background"),

        "text":         s("text"),
        "inverseText":  s("editor.background"),
        "inactive":     s("text.muted"),
        "subtle":       syn("comment"),
        "suggestion":   s("warning"),
        "remember":     syn("number"),

        "claude":         syn("keyword"),
        "claudeShimmer":  syn("function"),
        "claudeBlue_FOR_SYSTEM_SPINNER":        s("text.accent"),
        "claudeBlueShimmer_FOR_SYSTEM_SPINNER": syn("type"),

        "success":          s("success"),
        "error":            s("error"),
        "warning":          s("warning"),
        "warningShimmer":   syn("function"),

        "permission":         s("warning"),
        "permissionShimmer":  syn("function"),
        "planMode":           s("text.accent"),
        "ide":                s("text.accent"),
        "autoAccept":         s("success"),
        "promptBorder":         s("text.accent"),
        "promptBorderShimmer":  syn("type"),
        "bashBorder":           syn("number"),

        "diffAdded":           s("created.background"),
        "diffAddedDimmed":     s("created.background"),
        "diffAddedWord":       s("created"),
        "diffAddedWordDimmed": s("created"),
        "diffRemoved":         s("deleted.background"),
        "diffRemovedDimmed":   s("deleted.background"),
        "diffRemovedWord":     s("deleted"),
        "diffRemovedWordDimmed": s("deleted"),

        "red_FOR_SUBAGENTS_ONLY":    s("error"),
        "blue_FOR_SUBAGENTS_ONLY":   s("text.accent"),
        "green_FOR_SUBAGENTS_ONLY":  s("success"),
        "yellow_FOR_SUBAGENTS_ONLY": s("warning"),
        "purple_FOR_SUBAGENTS_ONLY": syn("number"),
        "orange_FOR_SUBAGENTS_ONLY": syn("keyword"),
        "pink_FOR_SUBAGENTS_ONLY":   syn("operator"),
        "cyan_FOR_SUBAGENTS_ONLY":   syn("string.regex"),
        "professionalBlue":          s("text.accent"),
    }
    return {"name": "Ayu Mirage", "base": "dark", "overrides": overrides}


def write_json(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"wrote {path}")


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    src = json.load(open(os.path.join(here, "src", "ayu-source.json")))
    zed = build_zed(src)
    claude = build_claude(zed)
    write_json(os.path.join(here, "zed", "ayu-mirage-high-contrast.json"), zed)
    write_json(os.path.join(here, "claude", "ayu-mirage.json"), claude)


if __name__ == "__main__":
    main()
