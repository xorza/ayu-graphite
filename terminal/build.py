#!/usr/bin/env python3
"""Read ../ayu-graphite.toml and emit ./ayu-graphite.terminal (macOS Terminal.app).

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
import emit
from palette import Palette, load_palette


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
    """Build NSKeyedArchiver-encoded NSColor (Device RGB) as a binary plist.

    NSColorSpace=2 = NSDeviceRGBColorSpace (sRGB-equivalent on modern Macs).
    Empirically Terminal.app renders NSColorSpace=1 (CalibratedRGB, gamma 1.8)
    backgrounds noticeably lighter than the same hex through sRGB — matching
    the format Apple's bundled profiles (e.g. Grass) use avoids that drift."""
    r, g, b = (c / 255 for c in emit.rgb_bytes(hex6))
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
                "NSColorSpace": 2,
            },
            {
                "$classname": "NSColor",
                "$classes": ["NSColor", "NSObject"],
            },
        ],
    }
    return plistlib.dumps(archive, fmt=plistlib.FMT_BINARY)


# The PostScript name, not the filename. Read it out of the font's `name`
# table (nameID 6) — a full name will not work.
FONT_NAME = "JetBrainsMonoNFM-Regular"
FONT_SIZE = 15


def build_terminal(p: Palette) -> dict[str, Any]:
    c = nscolor_archive
    return {
        "name": "Ayu Graphite",
        "type": "Window Settings",
        "ProfileCurrentVersion": 2.09,
        "Font": nsfont_archive(FONT_NAME, FONT_SIZE),
        "BackgroundColor": c(p.bg),
        "TextColor": c(p.text),
        "TextBoldColor": c(p.text),
        "CursorColor": c(p.accent),
        "SelectionColor": c(p.selection_bg),
        # ANSI 16 straight off the palette's ansi_* rows — same source the
        # Konsole and Zed terminals read, so a bright color is the same
        # bright color in all three.
        "ANSIBlackColor": c(p.ansi_black),
        "ANSIRedColor": c(p.ansi_red),
        "ANSIGreenColor": c(p.ansi_green),
        "ANSIYellowColor": c(p.ansi_yellow),
        "ANSIBlueColor": c(p.ansi_blue),
        "ANSIMagentaColor": c(p.ansi_magenta),
        "ANSICyanColor": c(p.ansi_cyan),
        "ANSIWhiteColor": c(p.ansi_white),
        "ANSIBrightBlackColor": c(p.ansi_bright_black),
        "ANSIBrightRedColor": c(p.ansi_bright_red),
        "ANSIBrightGreenColor": c(p.ansi_bright_green),
        "ANSIBrightYellowColor": c(p.ansi_bright_yellow),
        "ANSIBrightBlueColor": c(p.ansi_bright_blue),
        "ANSIBrightMagentaColor": c(p.ansi_bright_magenta),
        "ANSIBrightCyanColor": c(p.ansi_bright_cyan),
        "ANSIBrightWhiteColor": c(p.ansi_bright_white),
        # Window geometry + close behavior — match the user's preferred shell.
        "columnCount": 130,
        "rowCount": 30,
        "shellExitAction": 1,
        "warnOnShellCloseAction": 0,
    }


def main() -> None:
    emit.write_bytes(emit.beside(__file__, "ayu-graphite.terminal"),
                     plistlib.dumps(build_terminal(load_palette())))


if __name__ == "__main__":
    main()
