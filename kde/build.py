#!/usr/bin/env python3
"""Read ../ayu-graphite.toml and emit ./ayu-graphite.colors (KDE Plasma).

Format is the standard KDE color scheme INI: one section per color set
(View / Window / Button / Selection / Tooltip / Header / Complementary)
plus [WM], [General], [KDE], [ColorEffects:*]. Each color set has 12
keys with `R,G,B` triples. Reference: KDE/breeze colors/BreezeDark.colors.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import emit
from palette import Palette, load_palette


def color_set(p: Palette, *, bg: str, alt: str, fg: str) -> dict[str, str]:
    """The 12-key block every Colors:* section uses. bg/alt/fg differ per
    section; the accent and semantic foregrounds are uniform."""
    return {
        "BackgroundAlternate": emit.rgb_csv(alt),
        "BackgroundNormal":    emit.rgb_csv(bg),
        "DecorationFocus":     emit.rgb_csv(p.accent),
        "DecorationHover":     emit.rgb_csv(p.accent),
        "ForegroundActive":    emit.rgb_csv(p.accent),
        "ForegroundInactive":  emit.rgb_csv(p.text_muted),
        "ForegroundLink":      emit.rgb_csv(p.accent),
        "ForegroundNegative":  emit.rgb_csv(p.error),
        "ForegroundNeutral":   emit.rgb_csv(p.warning),
        "ForegroundNormal":    emit.rgb_csv(fg),
        "ForegroundPositive":  emit.rgb_csv(p.success),
        "ForegroundVisited":   emit.rgb_csv(p.ansi_bright_magenta),
    }


def build_kde(p: Palette) -> dict[str, dict[str, str]]:
    return {
        "ColorEffects:Disabled": {
            "Color":           emit.rgb_csv(p.elem_disabled),
            "ColorAmount":     "0",
            "ColorEffect":     "0",
            "ContrastAmount":  "0.65",
            "ContrastEffect":  "1",
            "IntensityAmount": "0.1",
            "IntensityEffect": "2",
        },
        "ColorEffects:Inactive": {
            "ChangeSelectionColor": "true",
            "Color":           emit.rgb_csv(p.text_disabled),
            "ColorAmount":     "0.025",
            "ColorEffect":     "2",
            "ContrastAmount":  "0.1",
            "ContrastEffect":  "2",
            "Enable":          "false",
            "IntensityAmount": "0",
            "IntensityEffect": "0",
        },
        # Each set's bg is one ramp step above the surface it sits on, so a
        # button reads as a button against its window and a tooltip lifts off
        # whatever is behind it. When panel/elem/surface shared a value these
        # three sections were the same grey and every control vanished.
        "Colors:Button":        color_set(p, bg=p.elem,      alt=p.elem_hover, fg=p.text),
        "Colors:Complementary": color_set(p, bg=p.bg,        alt=p.panel,      fg=p.text),
        "Colors:Header":        color_set(p, bg=p.title_bar, alt=p.panel,      fg=p.text),
        "Colors:Header][Inactive": color_set(p, bg=p.title_bar_inactive, alt=p.panel, fg=p.text_muted),
        # A dark-tinted selection rather than an accent-filled one. Accent is
        # light enough (#59d4ff) that everything Plasma draws inside a
        # selection — muted text, positive/negative/neutral labels — landed
        # between 1.2:1 and 2:1 on it. On the dark tint they keep their
        # normal values and stay legible; only negative needs the brighter
        # red step to clear 4.5:1.
        "Colors:Selection":     {**color_set(p, bg=p.selection_bg, alt=p.elem_active,
                                             fg=p.selection_fg),
                                 "ForegroundNegative": emit.rgb_csv(p.ansi_bright_red)},
        "Colors:Tooltip":       color_set(p, bg=p.surface,   alt=p.elem_hover, fg=p.text),
        "Colors:View":          color_set(p, bg=p.bg,        alt=p.panel,      fg=p.text),
        "Colors:Window":        color_set(p, bg=p.panel,     alt=p.elem,       fg=p.text),
        "General": {
            # Plasma 6 recolors controls from the wallpaper unless told not
            # to, which silently overrides our accent everywhere.
            "accentColorFromWallpaper": "false",
            "ColorScheme":     "AyuGraphite",
            "Name":            "Ayu Graphite",
            "shadeSortColumn": "true",
        },
        "KDE": {
            "contrast": "4",
        },
        "WM": {
            "activeBackground":   emit.rgb_csv(p.title_bar),
            "activeBlend":        emit.rgb_csv(p.text),
            "activeForeground":   emit.rgb_csv(p.text),
            "inactiveBackground": emit.rgb_csv(p.title_bar_inactive),
            "inactiveBlend":      emit.rgb_csv(p.text_muted),
            "inactiveForeground": emit.rgb_csv(p.text_muted),
        },
    }


def main() -> None:
    emit.write_text(emit.beside(__file__, "ayu-graphite.colors"),
                    emit.render_ini(build_kde(load_palette())))


if __name__ == "__main__":
    main()
