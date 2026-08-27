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


def check(profile: dict[str, Any], colors: dict[str, str]) -> None:
    """Every colour read back out of the archive it was written into.

    These are hand-built NSKeyedArchiver blobs, and nothing reads one until
    Terminal.app does. A wrong one is a window that comes up the wrong colour,
    with no error anywhere, so each one is decoded again here."""
    for key, hex6 in colors.items():
        stored = plistlib.loads(profile[key])["$objects"][1]["NSRGB"]
        back = "#{:02x}{:02x}{:02x}".format(
            *(round(float(c) * 255) for c in stored.rstrip(b"\x00").split()))
        assert back == hex6, f"{key} carries {back}, not {hex6}"


def build_terminal(p: Palette) -> dict[str, Any]:
    colors = {
        "BackgroundColor": p.bg,
        "TextColor": p.text,
        "TextBoldColor": p.text,
        "CursorColor": p.accent,
        "SelectionColor": p.selection_bg,
        # ANSI 16 straight off the palette's ansi_* rows — same source the
        # Konsole and Zed terminals read, so a bright color is the same
        # bright color in all three.
        "ANSIBlackColor": p.ansi_black,
        "ANSIRedColor": p.ansi_red,
        "ANSIGreenColor": p.ansi_green,
        "ANSIYellowColor": p.ansi_yellow,
        "ANSIBlueColor": p.ansi_blue,
        "ANSIMagentaColor": p.ansi_magenta,
        "ANSICyanColor": p.ansi_cyan,
        "ANSIWhiteColor": p.ansi_white,
        "ANSIBrightBlackColor": p.ansi_bright_black,
        "ANSIBrightRedColor": p.ansi_bright_red,
        "ANSIBrightGreenColor": p.ansi_bright_green,
        "ANSIBrightYellowColor": p.ansi_bright_yellow,
        "ANSIBrightBlueColor": p.ansi_bright_blue,
        "ANSIBrightMagentaColor": p.ansi_bright_magenta,
        "ANSIBrightCyanColor": p.ansi_bright_cyan,
        "ANSIBrightWhiteColor": p.ansi_bright_white,
    }
    profile: dict[str, Any] = {
        "name": "Ayu Graphite",
        "type": "Window Settings",
        "ProfileCurrentVersion": 2.09,
        "Font": nsfont_archive(FONT_NAME, FONT_SIZE),
        # Window geometry + close behavior — match the user's preferred shell.
        "columnCount": 130,
        "rowCount": 30,
        "shellExitAction": 1,
        "warnOnShellCloseAction": 0,
        **{key: nscolor_archive(value) for key, value in colors.items()},
    }
    check(profile, colors)
    return profile


def main() -> None:
    emit.write_bytes(emit.beside(__file__, "ayu-graphite.terminal"),
                     plistlib.dumps(build_terminal(load_palette())))


if __name__ == "__main__":
    main()
