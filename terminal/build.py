#!/usr/bin/env python3
"""Read ../ayu-mirage.toml and emit ./ayu-mirage.terminal (macOS Terminal.app).

A .terminal file is an XML plist. Each color is stored as bytes containing a
NSKeyedArchiver binary plist of an NSColor (sRGB). We hand-build that inner
archive — no Cocoa, just stdlib `plistlib`.
"""
import os
import plistlib
import tomllib
from dataclasses import dataclass
from plistlib import UID
from typing import Any


@dataclass
class Palette:
    bg: str
    panel: str
    surface: str
    elem: str
    elem_hover: str
    elem_active: str
    elem_selected: str
    title_bar: str
    title_bar_inactive: str

    border: str
    border_focused: str

    text: str
    text_muted: str
    text_disabled: str

    accent: str
    success: str
    warning: str
    error: str

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

    created: str
    created_bg: str
    deleted: str
    deleted_bg: str

    ansi_blue: str
    ansi_magenta: str
    ansi_cyan: str

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


def load_palette(path: str) -> Palette:
    with open(path, "rb") as f:
        data = tomllib.load(f)
    flat = {k: v for section in data.values() for k, v in section.items()}
    return Palette(**flat)


def hex_to_rgb(hex6: str) -> tuple[float, float, float]:
    h = hex6.lstrip("#")
    return (int(h[0:2], 16) / 255.0,
            int(h[2:4], 16) / 255.0,
            int(h[4:6], 16) / 255.0)


def nscolor_archive(hex6: str) -> bytes:
    """Build NSKeyedArchiver-encoded NSColor (sRGB) as a binary plist.

    Mirrors the structure macOS Terminal.app emits — the color object stores
    `NSRGB` as a space-separated, null-terminated ASCII string of float
    components and `NSColorSpace` = 1 (sRGB)."""
    r, g, b = hex_to_rgb(hex6)
    rgb_str = f"{r} {g} {b}\x00".encode("ascii")
    archive: dict[str, Any] = {
        "$version": 100000,
        "$archiver": "NSKeyedArchiver",
        "$top": {"root": UID(1)},
        "$objects": [
            "$null",
            {
                "$class": UID(2),
                "NSRGB": rgb_str,
                "NSColorSpace": 1,
            },
            {
                "$classname": "NSColor",
                "$classes": ["NSColor", "NSObject"],
            },
        ],
    }
    return plistlib.dumps(archive, fmt=plistlib.FMT_BINARY)


def build_terminal(p: Palette) -> dict[str, Any]:
    c = nscolor_archive
    return {
        "name": "Ayu Mirage",
        "type": "Window Settings",
        "ProfileCurrentVersion": 2.09,

        "BackgroundColor": c(p.bg),
        "TextColor":       c(p.text),
        "TextBoldColor":   c(p.text),
        "CursorColor":     c(p.accent),
        "SelectionColor":  c(p.elem_selected),

        # Base ANSI 8 — semantic roles match our palette.
        "ANSIBlackColor":   c(p.bg),
        "ANSIRedColor":     c(p.error),
        "ANSIGreenColor":   c(p.success),
        "ANSIYellowColor":  c(p.warning),
        "ANSIBlueColor":    c(p.ansi_blue),
        "ANSIMagentaColor": c(p.syn_number),       # purple
        "ANSICyanColor":    c(p.ansi_cyan),
        "ANSIWhiteColor":   c(p.text),

        # Bright variants — slightly punchier or accent-tinted siblings.
        "ANSIBrightBlackColor":   c(p.text_disabled),
        "ANSIBrightRedColor":     c(p.error),
        "ANSIBrightGreenColor":   c(p.success),
        "ANSIBrightYellowColor":  c(p.syn_function),  # lighter yellow
        "ANSIBrightBlueColor":    c(p.accent),         # pastel sky blue
        "ANSIBrightMagentaColor": c(p.ansi_magenta),
        "ANSIBrightCyanColor":    c(p.syn_string_regex),
        "ANSIBrightWhiteColor":   c("#ffffff"),
    }


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.dirname(here)
    p = load_palette(os.path.join(repo, "ayu-mirage.toml"))
    out = os.path.join(here, "ayu-mirage.terminal")
    with open(out, "wb") as f:
        plistlib.dump(build_terminal(p), f)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
