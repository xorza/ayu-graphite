#!/usr/bin/env python3
"""Read ../ayu-mirage.toml and emit ./ayu-mirage.terminal (macOS Terminal.app).

A .terminal file is an XML plist. Each color is stored as bytes containing a
NSKeyedArchiver binary plist of an NSColor (sRGB). We hand-build that inner
archive — no Cocoa, just stdlib `plistlib`.
"""

import os
import plistlib
import sys
from plistlib import UID
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from palette import Palette, load_palette


def hex_to_rgb(hex6: str) -> tuple[float, float, float]:
    h = hex6.lstrip("#")
    return (int(h[0:2], 16) / 255.0, int(h[2:4], 16) / 255.0, int(h[4:6], 16) / 255.0)


def nsfont_archive(ps_name: str, size: float) -> bytes:
    """NSKeyedArchiver-encoded NSFont. ps_name is the PostScript name (e.g.
    'JetBrainsMonoNerdFontMono-Regular' — find it in
    `system_profiler SPFontsDataType`)."""
    archive: dict[str, Any] = {
        "$version": 100000,
        "$archiver": "NSKeyedArchiver",
        "$top": {"root": UID(1)},
        "$objects": [
            "$null",
            {
                "$class": UID(3),
                "NSName": UID(2),
                "NSSize": float(size),
                "NSfFlags": 16,
            },
            ps_name,
            {
                "$classname": "NSFont",
                "$classes": ["NSFont", "NSObject"],
            },
        ],
    }
    return plistlib.dumps(archive, fmt=plistlib.FMT_BINARY)


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


FONT_NAME = (
    "JetBrainsMonoNFM-Regular"  # PostScript name, not filename. Read it from the
)
# font's `name` table (nameID 6) — full names won't work.
FONT_SIZE = 15


def build_terminal(p: Palette) -> dict[str, Any]:
    c = nscolor_archive
    return {
        "name": "Ayu Mirage",
        "type": "Window Settings",
        "ProfileCurrentVersion": 2.09,
        "Font": nsfont_archive(FONT_NAME, FONT_SIZE),
        "BackgroundColor": c(p.bg),
        "TextColor": c(p.text),
        "TextBoldColor": c(p.text),
        "CursorColor": c(p.accent),
        "SelectionColor": c(p.elem_active),
        # Base ANSI 8 — semantic roles match our palette.
        "ANSIBlackColor": c(p.bg),
        "ANSIRedColor": c(p.error),
        "ANSIGreenColor": c(p.success),
        "ANSIYellowColor": c(p.warning),
        "ANSIBlueColor": c(p.ansi_blue),
        "ANSIMagentaColor": c(p.syn_number),  # purple
        "ANSICyanColor": c(p.ansi_cyan),
        "ANSIWhiteColor": c(p.text),
        # Bright variants — slightly punchier or accent-tinted siblings.
        "ANSIBrightBlackColor": c(p.text_disabled),
        "ANSIBrightRedColor": c(p.error),
        "ANSIBrightGreenColor": c(p.success),
        "ANSIBrightYellowColor": c(p.syn_function),  # lighter yellow
        "ANSIBrightBlueColor": c(p.accent),  # pastel sky blue
        "ANSIBrightMagentaColor": c(p.ansi_magenta),
        "ANSIBrightCyanColor": c(p.syn_string_regex),
        "ANSIBrightWhiteColor": c(p.ansi_bright_white),
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
