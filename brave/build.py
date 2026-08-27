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
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import emit
from palette import Palette, load_palette


def build_brave(p: Palette) -> dict:
    # The chrome descends toward the page: frame (title_bar) is the top layer,
    # toolbar sits one step under it, and the omnibox and new-tab page bottom
    # out at `bg` — the same role bg plays as an editor/list interior in every
    # other target. Reversing it (frame darkest) would put the active tab,
    # which always takes the toolbar color, *above* its own strip.
    colors = {
        "frame":                     emit.rgb_bytes(p.title_bar),
        "frame_inactive":            emit.rgb_bytes(p.title_bar_inactive),
        # Private windows step one rung darker than normal ones so the two
        # are distinguishable at a glance without a second hue.
        "frame_incognito":           emit.rgb_bytes(p.panel),
        "frame_incognito_inactive":  emit.rgb_bytes(p.bg),

        "toolbar":                   emit.rgb_bytes(p.panel),
        # Recessed input field, same trick as the KDE View-vs-Window split.
        "omnibox_background":        emit.rgb_bytes(p.bg),
        "omnibox_text":              emit.rgb_bytes(p.text),

        "tab_text":                                    emit.rgb_bytes(p.text),
        "tab_background_text":                         emit.rgb_bytes(p.text_muted),
        "tab_background_text_inactive":                emit.rgb_bytes(p.text_muted),
        "tab_background_text_incognito":               emit.rgb_bytes(p.text_muted),
        "tab_background_text_incognito_inactive":      emit.rgb_bytes(p.text_muted),

        "bookmark_text":             emit.rgb_bytes(p.text),
        "toolbar_button_icon":       emit.rgb_bytes(p.text),

        "ntp_background":            emit.rgb_bytes(p.bg),
        "ntp_text":                  emit.rgb_bytes(p.text),
        "ntp_link":                  emit.rgb_bytes(p.accent),
        "ntp_header":                emit.rgb_bytes(p.border),

        # Caption-button plate behind minimize/maximize/close. Chromium draws
        # its own hover fill on top, so the resting state stays transparent
        # and the frame color shows through.
        "button_background":         emit.rgb_bytes(p.overlay_black) + (0,),
    }
    return {
        "manifest_version": 3,
        "name": "Ayu Graphite",
        "version": "1.0",
        "description": "Higher-contrast Ayu Graphite for Brave.",
        "theme": {"colors": colors},
    }


def main() -> None:
    emit.write_json(emit.beside(__file__, "ayu-graphite/manifest.json"),
                    build_brave(load_palette()))


if __name__ == "__main__":
    main()
