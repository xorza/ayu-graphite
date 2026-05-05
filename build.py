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
import struct
import zipfile
import zlib

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
        r, g, b = adj_channel(r, K_DIAG), adj_channel(g, K_DIAG), adj_channel(b, K_DIAG)
    elif key in ACCENT_KEYS:
        r, g, b = scale_sat(r, g, b, ACCENT_SAT, ACCENT_LIGHT)
        r, g, b = adj_channel(r, K_FG), adj_channel(g, K_FG), adj_channel(b, K_FG)
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


def build_telegram(zed_theme: dict) -> str:
    """Emit a .tdesktop-theme palette. Telegram falls back to defaults for any
    constant we don't define, so we cover the visible ~50 keys."""
    style = zed_theme["themes"][0]["style"]
    syntax = style["syntax"]

    def s(key):
        return strip_alpha(style[key])

    def syn(key):
        return strip_alpha(syntax[key]["color"])

    bg          = s("editor.background")
    panel       = s("panel.background")
    surface     = s("surface.background")
    elem        = s("element.background")
    elem_hover  = s("element.hover")
    elem_sel    = s("element.selected")
    text_fg     = s("text")
    text_mut    = s("text.muted")
    accent      = s("text.accent")
    success_fg  = s("success")
    error_fg    = s("error")
    warn_fg     = s("warning")
    string_fg   = syn("string")
    func_fg     = syn("function")

    pairs = [
        ("windowBg",                  bg),
        ("windowBgOver",              elem_hover),
        ("windowBgRipple",            elem_sel),
        ("windowBgActive",            accent),
        ("windowFg",                  text_fg),
        ("windowFgOver",              text_fg),
        ("windowSubTextFg",           text_mut),
        ("windowSubTextFgOver",       text_mut),
        ("windowBoldFg",              text_fg),
        ("windowBoldFgOver",          text_fg),
        ("windowFgActive",            bg),
        ("windowActiveTextFg",        accent),

        ("sideBarBg",                 panel),
        ("sideBarBgActive",           elem_sel),
        ("topBarBg",                  s("title_bar.background")),

        ("titleBg",                   s("title_bar.inactive_background")),
        ("titleBgActive",             s("title_bar.background")),
        ("titleFg",                   text_mut),
        ("titleFgActive",             text_fg),
        ("titleShadow",               bg),
        ("titleButtonBg",             s("title_bar.background")),
        ("titleButtonFg",             text_fg),
        ("titleButtonBgOver",         elem_hover),
        ("titleButtonFgOver",         text_fg),

        ("dialogsBg",                 panel),
        ("dialogsBgOver",             elem_hover),
        ("dialogsBgActive",           elem_sel),
        ("dialogsNameFg",             text_fg),
        ("dialogsNameFgActive",       text_fg),
        ("dialogsTextFg",             text_mut),
        ("dialogsTextFgActive",       text_fg),
        ("dialogsDateFg",             text_mut),
        ("dialogsDateFgActive",       text_mut),
        ("dialogsUnreadBg",           accent),
        ("dialogsUnreadBgMuted",      text_mut),
        ("dialogsUnreadFg",           bg),
        ("dialogsUnreadFgActive",     bg),

        ("msgInBg",                   surface),
        ("msgInBgSelected",           elem_sel),
        ("msgOutBg",                  elem),
        ("msgOutBgSelected",          elem_sel),
        ("msgInDateFg",               text_mut),
        ("msgOutDateFg",              text_mut),
        ("msgInServiceFg",            accent),
        ("msgOutServiceFg",           accent),
        ("msgInMonoFg",               string_fg),
        ("msgOutMonoFg",              string_fg),
        ("msgInReplyBarColor",        accent),
        ("msgOutReplyBarColor",       func_fg),
        ("msgServiceBg",              panel),
        ("msgServiceFg",              text_mut),

        ("activeButtonBg",            accent),
        ("activeButtonBgOver",        accent),
        ("activeButtonFg",            bg),
        ("activeButtonFgOver",        bg),
        ("lightButtonBg",             elem),
        ("lightButtonBgOver",         elem_hover),
        ("lightButtonFg",             accent),
        ("lightButtonFgOver",         accent),

        ("scrollBg",                  panel),
        ("scrollBgOver",              elem_hover),
        ("scrollBarBg",               text_mut),
        ("scrollBarBgOver",           text_fg),

        ("boxTextFgGood",             success_fg),
        ("boxTextFgError",            error_fg),
        ("activeLineFgError",         error_fg),
        ("attentionButtonFg",         warn_fg),

        # Dividers / separators / shadows — Telegram defaults these bright in
        # popup menus when undefined. Keep them subtle and dark.
        ("shadowFg",                  panel),
        ("windowShadowFg",            panel),
        ("windowShadowFgFallback",    panel),
        ("boxDividerBg",              panel),
        ("boxDividerFg",              elem),
        ("menuBg",                    panel),
        ("menuBgOver",                elem_hover),
        ("menuBgRipple",              elem_sel),
        ("menuFg",                    text_fg),
        ("menuFgDisabled",            text_mut),
        ("menuIconFg",                text_mut),
        ("menuIconFgOver",            text_fg),
        ("menuSubmenuArrowFg",        text_mut),
        ("menuSeparatorFg",           elem),

        ("mentionBg",                 elem),
        ("mentionFg",                 accent),
    ]
    lines = ["// Ayu Mirage High Contrast — Telegram Desktop palette", ""]
    lines += [f"{k}: {v};" for k, v in pairs]
    return "\n".join(lines) + "\n"


def write_json(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"wrote {path}")


def solid_png(hex_color: str, size: int = 8) -> bytes:
    """Tiny solid-color PNG (no Pillow). Telegram tiles/scales it as wallpaper."""
    h = hex_color.lstrip("#")
    rgb = bytes((int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)))

    def chunk(typ: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + typ + data
                + struct.pack(">I", zlib.crc32(typ + data) & 0xffffffff))

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)  # 8-bit RGB
    raw = b"".join(b"\x00" + rgb * size for _ in range(size))  # filter byte + row
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


def write_telegram(path: str, palette: str, bg_hex: str) -> None:
    """Zipped .tdesktop-theme bundling palette + solid background.png."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("colors.tdesktop-theme", palette)
        z.writestr("background.png", solid_png(bg_hex))
    print(f"wrote {path}")


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    src = json.load(open(os.path.join(here, "src", "ayu-source.json")))
    zed = build_zed(src)
    claude = build_claude(zed)
    telegram = build_telegram(zed)
    write_json(os.path.join(here, "zed", "ayu-mirage-high-contrast.json"), zed)
    write_json(os.path.join(here, "claude", "ayu-mirage.json"), claude)
    bg_hex = strip_alpha(zed["themes"][0]["style"]["editor.background"])
    write_telegram(os.path.join(here, "telegram", "ayu-mirage.tdesktop-theme"),
                   telegram, bg_hex)


if __name__ == "__main__":
    main()
