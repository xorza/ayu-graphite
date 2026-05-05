#!/usr/bin/env python3
"""Read ayu-mirage.toml (produced by src/build_palette.py) and emit
the small theme outputs that consume the shared semantic palette:

  claude/ayu-mirage.json              Claude Code custom theme
  telegram/ayu-mirage.tdesktop-theme  Telegram Desktop theme (zip with
                                      colors.tdesktop-theme + solid bg PNG)

The Zed theme is produced by the palette builder, not here, because Zed needs
the full upstream key set, not just palette tokens.
"""
import json
import os
import struct
import tomllib
import zipfile
import zlib
from dataclasses import dataclass


@dataclass
class Palette:
    """Semantic color tokens. Mirrors the shape of palette/ayu-mirage.toml."""
    bg: str
    panel: str
    surface: str
    elem: str
    elem_hover: str
    elem_active: str
    elem_selected: str
    title_bar: str
    title_bar_inactive: str

    text: str
    text_muted: str
    text_disabled: str

    accent: str
    success: str
    warning: str
    error: str

    created: str
    created_bg: str
    deleted: str
    deleted_bg: str

    syn_keyword: str
    syn_function: str
    syn_string: str
    syn_string_regex: str
    syn_comment: str
    syn_number: str
    syn_type: str
    syn_operator: str

    info_bg: str
    info_border: str


def load_palette(path: str) -> Palette:
    with open(path, "rb") as f:
        data = tomllib.load(f)
    flat = {k: v for section in data.values() for k, v in section.items()}
    return Palette(**flat)


def build_claude(p: Palette) -> dict:
    overrides = {
        "background":                 p.bg,
        "userMessageBackground":      p.elem,
        "bashMessageBackgroundColor": p.elem,
        "memoryBackgroundColor":      p.elem,

        "text":         p.text,
        "inverseText":  p.bg,
        "inactive":     p.text_muted,
        "subtle":       p.syn_comment,
        "suggestion":   p.warning,
        "remember":     p.syn_number,

        "claude":         p.syn_keyword,
        "claudeShimmer":  p.syn_function,
        "claudeBlue_FOR_SYSTEM_SPINNER":        p.accent,
        "claudeBlueShimmer_FOR_SYSTEM_SPINNER": p.syn_type,

        "success":          p.success,
        "error":            p.error,
        "warning":          p.warning,
        "warningShimmer":   p.syn_function,

        "permission":         p.warning,
        "permissionShimmer":  p.syn_function,
        "planMode":           p.accent,
        "ide":                p.accent,
        "autoAccept":         p.success,
        "promptBorder":         p.accent,
        "promptBorderShimmer":  p.syn_type,
        "bashBorder":           p.syn_number,

        "diffAdded":             p.created_bg,
        "diffAddedDimmed":       p.created_bg,
        "diffAddedWord":         p.created,
        "diffAddedWordDimmed":   p.created,
        "diffRemoved":           p.deleted_bg,
        "diffRemovedDimmed":     p.deleted_bg,
        "diffRemovedWord":       p.deleted,
        "diffRemovedWordDimmed": p.deleted,

        "red_FOR_SUBAGENTS_ONLY":    p.error,
        "blue_FOR_SUBAGENTS_ONLY":   p.accent,
        "green_FOR_SUBAGENTS_ONLY":  p.success,
        "yellow_FOR_SUBAGENTS_ONLY": p.warning,
        "purple_FOR_SUBAGENTS_ONLY": p.syn_number,
        "orange_FOR_SUBAGENTS_ONLY": p.syn_keyword,
        "pink_FOR_SUBAGENTS_ONLY":   p.syn_operator,
        "cyan_FOR_SUBAGENTS_ONLY":   p.syn_string_regex,
        "professionalBlue":          p.accent,
    }
    return {"name": "Ayu Mirage", "base": "dark", "overrides": overrides}


def build_telegram(p: Palette) -> str:
    """Emit a .tdesktop-theme palette. Telegram falls back to defaults for any
    constant we don't define, so we cover the visible ~50 keys."""
    pairs = [
        ("windowBg",                  p.bg),
        ("windowBgOver",              p.elem_hover),
        ("windowBgRipple",            p.elem_selected),
        ("windowBgActive",            p.accent),
        ("windowFg",                  p.text),
        ("windowFgOver",              p.text),
        ("windowSubTextFg",           p.text_muted),
        ("windowSubTextFgOver",       p.text_muted),
        ("windowBoldFg",              p.text),
        ("windowBoldFgOver",          p.text),
        ("windowFgActive",            p.bg),
        ("windowActiveTextFg",        p.accent),

        ("sideBarBg",                 p.panel),
        ("sideBarBgActive",           p.elem_selected),
        ("topBarBg",                  p.title_bar),

        ("titleBg",                   p.title_bar_inactive),
        ("titleBgActive",             p.title_bar),
        ("titleFg",                   p.text_muted),
        ("titleFgActive",             p.text),
        ("titleShadow",               p.bg),
        ("titleButtonBg",             p.title_bar),
        ("titleButtonFg",             p.text),
        ("titleButtonBgOver",         p.elem_hover),
        ("titleButtonFgOver",         p.text),

        ("dialogsBg",                 p.panel),
        ("dialogsBgOver",             p.elem_hover),
        ("dialogsBgActive",           p.elem_selected),
        ("dialogsNameFg",             p.text),
        ("dialogsNameFgActive",       p.text),
        ("dialogsTextFg",             p.text_muted),
        ("dialogsTextFgActive",       p.text),
        ("dialogsDateFg",             p.text_muted),
        ("dialogsDateFgActive",       p.text_muted),
        ("dialogsUnreadBg",           p.accent),
        ("dialogsUnreadBgMuted",      p.text_muted),
        ("dialogsUnreadFg",           p.bg),
        ("dialogsUnreadFgActive",     p.bg),

        ("msgInBg",                   p.surface),
        ("msgInBgSelected",           p.elem_selected),
        ("msgOutBg",                  p.elem),
        ("msgOutBgSelected",          p.elem_selected),
        ("msgInDateFg",               p.text_muted),
        ("msgOutDateFg",              p.text_muted),
        ("msgInServiceFg",            p.accent),
        ("msgOutServiceFg",           p.accent),
        ("msgInMonoFg",               p.syn_string),
        ("msgOutMonoFg",              p.syn_string),
        ("msgInReplyBarColor",        p.accent),
        ("msgOutReplyBarColor",       p.syn_function),
        ("msgServiceBg",              p.panel),
        ("msgServiceFg",              p.text_muted),

        ("activeButtonBg",            p.accent),
        ("activeButtonBgOver",        p.accent),
        ("activeButtonFg",            p.bg),
        ("activeButtonFgOver",        p.bg),
        ("lightButtonBg",             p.elem),
        ("lightButtonBgOver",         p.elem_hover),
        ("lightButtonFg",             p.accent),
        ("lightButtonFgOver",         p.accent),

        ("scrollBg",                  p.panel),
        ("scrollBgOver",              p.elem_hover),
        ("scrollBarBg",               p.text_muted),
        ("scrollBarBgOver",           p.text),

        ("boxTextFgGood",             p.success),
        ("boxTextFgError",            p.error),
        ("activeLineFgError",         p.error),
        ("attentionButtonFg",         p.warning),

        # Dividers / separators / shadows — Telegram defaults these bright in
        # popup menus when undefined. Keep them subtle and dark.
        ("shadowFg",                  p.panel),
        ("windowShadowFg",            p.panel),
        ("windowShadowFgFallback",    p.panel),
        ("boxDividerBg",              p.panel),
        ("boxDividerFg",              p.elem),
        ("menuBg",                    p.panel),
        ("menuBgOver",                p.elem_hover),
        ("menuBgRipple",              p.elem_selected),
        ("menuFg",                    p.text),
        ("menuFgDisabled",            p.text_muted),
        ("menuIconFg",                p.text_muted),
        ("menuIconFgOver",            p.text),
        ("menuSubmenuArrowFg",        p.text_muted),
        ("menuSeparatorFg",           p.elem),

        ("mentionBg",                 p.elem),
        ("mentionFg",                 p.accent),
    ]
    lines = ["// Ayu Mirage High Contrast — Telegram Desktop palette", ""]
    lines += [f"{k}: {v};" for k, v in pairs]
    return "\n".join(lines) + "\n"


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


def write_json(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"wrote {path}")


def write_telegram(path: str, palette: str, bg_hex: str) -> None:
    """Zipped .tdesktop-theme bundling palette + solid background.png."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("colors.tdesktop-theme", palette)
        z.writestr("background.png", solid_png(bg_hex))
    print(f"wrote {path}")


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    p = load_palette(os.path.join(here, "ayu-mirage.toml"))
    write_json(os.path.join(here, "claude", "ayu-mirage.json"), build_claude(p))
    write_telegram(os.path.join(here, "telegram", "ayu-mirage.tdesktop-theme"),
                   build_telegram(p), p.bg)


if __name__ == "__main__":
    main()
