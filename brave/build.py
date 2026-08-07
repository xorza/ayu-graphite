#!/usr/bin/env python3
"""Read ../ayu-graphite.toml and emit ./ayu-graphite/manifest.json (Brave).

Brave is Chromium, so a theme is an extension whose manifest carries nothing
but a `theme` block — no background page, no permissions. Chromium takes
colors as `[R, G, B]` (or `[R, G, B, A]` with a 0..1 float alpha) and derives
everything it isn't given: the inactive-tab fill is blended from `frame` and
`toolbar`, separators and shadows come off the same pair. That's why only the
~19 keys Chromium actually reads are here — an unknown key is dropped
silently, so inventing names buys nothing.

Output is an unpacked extension directory: Brave loads it via
brave://extensions → Developer mode → "Load unpacked". A zip won't install
(Chromium only accepts signed .crx outside of dev mode), so there's nothing
to gain from packaging it here.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from palette import Palette, load_palette


def rgb(hex6: str) -> list[int]:
    h = hex6.lstrip("#")
    return [int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)]


def rgba(hex6: str, a: float) -> list:
    return rgb(hex6) + [a]


def build_brave(p: Palette) -> dict:
    # The chrome descends toward the page: frame (title_bar) is the top layer,
    # toolbar sits one step under it, and the omnibox and new-tab page bottom
    # out at `bg` — the same role bg plays as an editor/list interior in every
    # other target. Reversing it (frame darkest) would put the active tab,
    # which always takes the toolbar color, *above* its own strip.
    colors = {
        "frame":                     rgb(p.title_bar),
        "frame_inactive":            rgb(p.title_bar_inactive),
        # Private windows step one rung darker than normal ones so the two
        # are distinguishable at a glance without a second hue.
        "frame_incognito":           rgb(p.panel),
        "frame_incognito_inactive":  rgb(p.bg),

        "toolbar":                   rgb(p.panel),
        # Recessed input field, same trick as the KDE View-vs-Window split.
        "omnibox_background":        rgb(p.bg),
        "omnibox_text":              rgb(p.text),

        "tab_text":                                    rgb(p.text),
        "tab_background_text":                         rgb(p.text_muted),
        "tab_background_text_inactive":                rgb(p.text_muted),
        "tab_background_text_incognito":               rgb(p.text_muted),
        "tab_background_text_incognito_inactive":      rgb(p.text_muted),

        "bookmark_text":             rgb(p.text),
        "toolbar_button_icon":       rgb(p.text),

        "ntp_background":            rgb(p.bg),
        "ntp_text":                  rgb(p.text),
        "ntp_link":                  rgb(p.accent),
        "ntp_header":                rgb(p.border),

        # Caption-button plate behind minimize/maximize/close. Chromium draws
        # its own hover fill on top, so the resting state stays transparent
        # and the frame color shows through.
        "button_background":         rgba(p.overlay_black, 0),
    }
    return {
        "manifest_version": 3,
        "name": "Ayu Graphite",
        "version": "1.0",
        "description": "Higher-contrast Ayu Graphite for Brave.",
        "theme": {"colors": colors},
    }


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.dirname(here)
    p = load_palette(os.path.join(repo, "ayu-graphite.toml"))
    out_dir = os.path.join(here, "ayu-graphite")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, "manifest.json")
    with open(out, "w") as f:
        json.dump(build_brave(p), f, indent=2)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
