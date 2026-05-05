#!/usr/bin/env python3
"""One-shot tool: re-seed ayu-mirage.toml from upstream Zed Ayu Mirage.

Run this only when you want to refresh the palette from a new upstream snapshot
(after `make fetch-source`). Day-to-day, hand-edit ../ayu-mirage.toml; the
target builders are pure transformers and do not invoke this pipeline.

Reads ./ayu-source.json (upstream Zed Ayu snapshot, lives next to this script)
and writes ../ayu-mirage.toml.

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
"""
import colorsys
import dataclasses
import json
import os
import re
from dataclasses import dataclass
from typing import Any

# ---- knobs ----
GAMMA  = 1.10   # > 1 brightens midtones (lifts dark backgrounds)
K_BG   = 1.40   # contrast boost for chrome (S-curve around MID)
K_FG   = 1.15   # contrast boost for foreground — kept lower so saturated channels don't clamp
K_DIAG = 1.10   # contrast boost for diagnostic tints (info/error/warning/created backgrounds);
                # gentler than K_BG so the dark blue/red/yellow channel doesn't clip to 0 and oversaturate
MID    = 0.40   # midpoint of the S-curve (theme is dark, so < 0.5)
BG_SAT = 0.0    # chroma kept on chrome backgrounds (0 = pure gray)
FG_SAT = 1.30   # chroma multiplier for foreground/accent colors (> 1 = punchier)
FG_LIGHT = 0.88 # lightness multiplier for foreground (< 1 deepens / vivid; > 1 brightens / pastel)
ACCENT_SAT   = 0.65 # saturation multiplier for accent keys (text.accent, link_text.hover) —
                    # < 1 mutes them so they don't read as shouty when used as a button fill
ACCENT_LIGHT = 1.00 # lightness multiplier for accent keys

# Chrome flattening: after channel adj + desat, lerp every chrome value toward
# CHROME_TARGET by CHROME_COMPRESS. 0 = preserve original spread; 1 = all chrome
# becomes the same gray.
CHROME_TARGET   = 45   # RGB component for the chrome mid-gray (~#2d2d2d)
CHROME_COMPRESS = 0.40

# Borders flatten to a darker target than chrome bgs so separators read as
# subtle cracks below panel level instead of mid-gray ridges.
BORDER_TARGET   = 42
BORDER_COMPRESS = 0.75

CHROME_KEYS = {
    "background", "editor.background", "editor.gutter.background",
    "editor.subheader.background", "editor.active_line.background",
    "editor.highlighted_line.background",
    "element.background", "element.hover", "element.active", "element.selected",
    "ghost_element.background", "ghost_element.hover", "ghost_element.active", "ghost_element.selected",
    "surface.background", "elevated_surface.background",
    "panel.background", "status_bar.background", "title_bar.background",
    "title_bar.inactive_background", "tab_bar.background",
    "tab.inactive_background", "tab.active_background",
    "toolbar.background", "terminal.background",
    "scrollbar.track.background", "scrollbar.thumb.background",
    "scrollbar.thumb.hover_background",
    "terminal.ansi.black", "terminal.ansi.dim_black",
}

# Neutral chrome borders — flatten to a darker, desaturated target so panel
# separators don't read with a blue tint and sit below panel level. Status
# borders (info/error/warning/created.border) and focused/selected borders are
# NOT here — they keep hue.
BORDER_KEYS = {
    "border", "border.variant", "border.disabled",
    "hidden.border", "ignored.border", "unreachable.border",
    "scrollbar.thumb.border", "scrollbar.track.border",
}

SAT_NEUTRAL_SUFFIXES = (".background", ".border")
SAT_NEUTRAL_KEYS = {
    "drop_target.background", "ghost_element.background",
    "search.match_background", "search.active_match_background",
    "editor.document_highlight.read_background",
    "editor.document_highlight.write_background",
}

# Foreground colors that ALSO get used as fill behind dark text (project chip,
# notification action button, etc.). Skip the FG_SAT/FG_LIGHT boost so they
# stay close to upstream tone — still readable as text, not shouty as a fill.
ACCENT_KEYS = {"text.accent", "link_text.hover"}

HEX_RE = re.compile(r"#([0-9a-fA-F]{6})([0-9a-fA-F]{2})?")


def adj_channel(c: int, k: float) -> int:
    x = (c / 255) ** (1 / GAMMA)
    y = MID + (x - MID) * k
    return max(0, min(255, round(y * 255)))


def scale_sat(r: int, g: int, b: int, factor: float, light_factor: float = 1.0):
    h, light, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    s = max(0.0, min(1.0, s * factor))
    if s > 0.3:
        light = max(0.0, min(1.0, light * light_factor))
    rr, gg, bb = colorsys.hls_to_rgb(h, light, s)
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
    elif key in BORDER_KEYS:
        r, g, b = scale_sat(r, g, b, BG_SAT)
        f = BORDER_COMPRESS
        r = round(r * (1 - f) + BORDER_TARGET * f)
        g = round(g * (1 - f) + BORDER_TARGET * f)
        b = round(b * (1 - f) + BORDER_TARGET * f)
    elif is_diagnostic_bg(key):
        r, g, b = adj_channel(r, K_DIAG), adj_channel(g, K_DIAG), adj_channel(b, K_DIAG)
    elif key in ACCENT_KEYS:
        r, g, b = scale_sat(r, g, b, ACCENT_SAT, ACCENT_LIGHT)
        r, g, b = adj_channel(r, K_FG), adj_channel(g, K_FG), adj_channel(b, K_FG)
    else:
        r, g, b = scale_sat(r, g, b, FG_SAT, FG_LIGHT)
        r, g, b = adj_channel(r, K_FG), adj_channel(g, K_FG), adj_channel(b, K_FG)
    return fmt(r, g, b, a)


def walk(node: Any, key: str = "") -> Any:
    if isinstance(node, dict):
        return {k: walk(v, k) for k, v in node.items()}
    if isinstance(node, list):
        return [walk(v, key) for v in node]
    if isinstance(node, str):
        return transform(node, key)
    return node


@dataclass
class Palette:
    """Mirrors the shape of ../ayu-mirage.toml."""
    # backgrounds
    bg: str
    panel: str
    surface: str
    elem: str
    elem_hover: str
    elem_active: str
    elem_selected: str
    title_bar: str
    title_bar_inactive: str
    # borders
    border: str
    border_focused: str
    # text
    text: str
    text_muted: str
    text_disabled: str
    # accent_status
    accent: str
    success: str
    warning: str
    error: str
    # status_bg
    info_bg: str
    info_border: str
    hint_bg: str
    hint_border: str
    success_bg: str
    success_border: str
    warning_bg: str
    warning_border: str
    error_bg: str
    error_border: str
    # diff
    created: str
    created_bg: str
    deleted: str
    deleted_bg: str
    # ansi
    ansi_blue: str
    ansi_magenta: str
    ansi_cyan: str
    # syntax
    syn_keyword: str
    syn_function: str
    syn_string: str
    syn_string_regex: str
    syn_comment: str
    syn_number: str
    syn_type: str
    syn_operator: str
    syn_attribute: str
    syn_punctuation: str
    syn_doc: str
    syn_string_special: str
    syn_predictive: str

    def as_dict(self) -> dict:
        return dataclasses.asdict(self)


def palette_from_zed(zed_theme: dict) -> Palette:
    style = zed_theme["themes"][0]["style"]
    syntax = style["syntax"]

    def s(key):
        return strip_alpha(style[key])

    def syn(key):
        return strip_alpha(syntax[key]["color"])

    # info.background/border get the manual override applied in build_zed
    # below. Pull the OVERRIDDEN values so re-seeding preserves the chip tint.
    return Palette(
        bg=s("editor.background"),
        panel=s("panel.background"),
        surface=s("surface.background"),
        elem=s("element.background"),
        elem_hover=s("element.hover"),
        elem_active=s("element.active"),
        elem_selected=s("element.selected"),
        title_bar=s("title_bar.background"),
        title_bar_inactive=s("title_bar.inactive_background"),
        border=s("border"),
        border_focused=s("border.focused"),
        text=s("text"),
        text_muted=s("text.muted"),
        text_disabled=s("text.disabled"),
        accent=s("text.accent"),
        success=s("success"),
        warning=s("warning"),
        error=s("error"),
        info_bg=s("info.background"),
        info_border=s("info.border"),
        hint_bg=s("hint.background"),
        hint_border=s("hint.border"),
        success_bg=s("success.background"),
        success_border=s("success.border"),
        warning_bg=s("warning.background"),
        warning_border=s("warning.border"),
        error_bg=s("error.background"),
        error_border=s("error.border"),
        created=s("created"),
        created_bg=s("created.background"),
        deleted=s("deleted"),
        deleted_bg=s("deleted.background"),
        ansi_blue=s("terminal.ansi.blue"),
        ansi_magenta=s("terminal.ansi.magenta"),
        ansi_cyan=s("terminal.ansi.cyan"),
        syn_keyword=syn("keyword"),
        syn_function=syn("function"),
        syn_string=syn("string"),
        syn_string_regex=syn("string.regex"),
        syn_comment=syn("comment"),
        syn_number=syn("number"),
        syn_type=syn("type"),
        syn_operator=syn("operator"),
        syn_attribute=syn("attribute"),
        syn_punctuation=syn("punctuation"),
        syn_doc=syn("comment.doc"),
        syn_string_special=syn("string.special"),
        syn_predictive=syn("predictive"),
    )


def build_zed(src: dict) -> dict:
    theme = next(t for t in src["themes"] if t["name"] == "Ayu Mirage")
    theme = walk(theme)
    theme["name"] = "Ayu Mirage High Contrast"
    theme["appearance"] = "dark"

    # Manual override: info.background/border drive the title-bar project chip
    # when its dropdown is open (Zed's Tinted(Accent) button style → status.info_*).
    # The diagnostic-bg pipeline still produces a heavy navy that reads as out
    # of theme. Substitute a softer mid-blue panel + accent-toned border.
    style = theme["style"]
    style["info.background"] = "#2c4a60ff"
    style["info.border"]     = "#4a8ab0ff"

    return {
        "$schema": "https://zed.dev/schema/themes/v0.2.0.json",
        "name": "Ayu Mirage High Contrast",
        "author": "xxorza",
        "themes": [theme],
    }


def write_palette_toml(path: str, p: Palette) -> None:
    """Write the palette to TOML. Re-seeded values OVERWRITE the hand-edited
    file — review the diff before committing."""
    sections = [
        ("backgrounds", ["bg", "panel", "surface", "elem", "elem_hover",
                         "elem_active", "elem_selected", "title_bar",
                         "title_bar_inactive"]),
        ("borders", ["border", "border_focused"]),
        ("text", ["text", "text_muted", "text_disabled"]),
        ("accent_status", ["accent", "success", "warning", "error"]),
        ("status_bg", ["info_bg", "info_border", "hint_bg", "hint_border",
                       "success_bg", "success_border",
                       "warning_bg", "warning_border",
                       "error_bg", "error_border"]),
        ("diff", ["created", "created_bg", "deleted", "deleted_bg"]),
        ("ansi", ["ansi_blue", "ansi_magenta", "ansi_cyan"]),
        ("syntax", ["syn_keyword", "syn_function", "syn_string",
                    "syn_string_regex", "syn_comment", "syn_number",
                    "syn_type", "syn_operator", "syn_attribute",
                    "syn_punctuation", "syn_doc", "syn_string_special",
                    "syn_predictive"]),
    ]
    d = p.as_dict()
    lines = ["# Ayu Mirage High Contrast — semantic palette (single source of truth)",
             "# Re-seeded by tools/import_from_zed.py from tools/ayu-source.json.",
             "# Hand-edit me; the target builders are pure transformers.",
             ""]
    for section, keys in sections:
        lines.append(f"[{section}]")
        for k in keys:
            lines.append(f'{k} = "{d[k]}"')
        lines.append("")
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(lines).rstrip() + "\n")
    print(f"wrote {path}")


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))   # .../tools
    repo = os.path.dirname(here)
    src = json.load(open(os.path.join(here, "ayu-source.json")))
    zed = build_zed(src)                # full pipeline pass
    palette = palette_from_zed(zed)     # extract semantic tokens
    write_palette_toml(os.path.join(repo, "ayu-mirage.toml"), palette)


if __name__ == "__main__":
    main()

