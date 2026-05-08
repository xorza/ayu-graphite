#!/usr/bin/env python3
"""Read ../ayu-mirage.toml and emit ./ayu-mirage.colors (KDE Plasma).

Format is the standard KDE color scheme INI: one section per color set
(View / Window / Button / Selection / Tooltip / Header / Complementary)
plus [WM], [General], [KDE], [ColorEffects:*]. Each color set has 12
keys with `R,G,B` triples. Reference: KDE/breeze colors/BreezeDark.colors.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from palette import Palette, load_palette


def rgb(hex6: str) -> str:
    h = hex6.lstrip("#")
    return f"{int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)}"


def color_set(p: Palette, *, bg: str, alt: str, fg: str) -> dict[str, str]:
    """The 12-key block every Colors:* section uses. bg/alt/fg differ per
    section; the accent and semantic foregrounds are uniform."""
    return {
        "BackgroundAlternate": rgb(alt),
        "BackgroundNormal":    rgb(bg),
        "DecorationFocus":     rgb(p.accent),
        "DecorationHover":     rgb(p.accent),
        "ForegroundActive":    rgb(p.accent),
        "ForegroundInactive":  rgb(p.text_muted),
        "ForegroundLink":      rgb(p.accent),
        "ForegroundNegative":  rgb(p.error),
        "ForegroundNeutral":   rgb(p.warning),
        "ForegroundNormal":    rgb(fg),
        "ForegroundPositive":  rgb(p.success),
        "ForegroundVisited":   rgb(p.syn_number),
    }


def build_kde(p: Palette) -> dict[str, dict[str, str]]:
    return {
        "ColorEffects:Disabled": {
            "Color":           "56,56,56",
            "ColorAmount":     "0",
            "ColorEffect":     "0",
            "ContrastAmount":  "0.65",
            "ContrastEffect":  "1",
            "IntensityAmount": "0.1",
            "IntensityEffect": "2",
        },
        "ColorEffects:Inactive": {
            "ChangeSelectionColor": "true",
            "Color":           "112,111,110",
            "ColorAmount":     "0.025",
            "ColorEffect":     "2",
            "ContrastAmount":  "0.1",
            "ContrastEffect":  "2",
            "Enable":          "false",
            "IntensityAmount": "0",
            "IntensityEffect": "0",
        },
        "Colors:Button":        color_set(p, bg=p.elem,      alt=p.elem_hover, fg=p.text),
        "Colors:Complementary": color_set(p, bg=p.bg,        alt=p.surface,    fg=p.text),
        "Colors:Header":        color_set(p, bg=p.title_bar, alt=p.panel,      fg=p.text),
        "Colors:Header][Inactive": color_set(p, bg=p.title_bar_inactive, alt=p.panel, fg=p.text_muted),
        "Colors:Selection":     {**color_set(p, bg=p.accent, alt=p.elem_active, fg=p.bg),
                                 # Inside a selection, links/negatives/etc need to read on accent.
                                 "ForegroundActive":   rgb(p.bg),
                                 "ForegroundLink":     rgb(p.bg),
                                 "ForegroundVisited":  rgb(p.bg)},
        "Colors:Tooltip":       color_set(p, bg=p.panel,     alt=p.elem,       fg=p.text),
        "Colors:View":          color_set(p, bg=p.bg,        alt=p.surface,    fg=p.text),
        "Colors:Window":        color_set(p, bg=p.panel,     alt=p.elem,       fg=p.text),
        "General": {
            "ColorScheme":     "AyuMirageHighContrast",
            "Name":            "Ayu Mirage High Contrast",
            "shadeSortColumn": "true",
        },
        "KDE": {
            "contrast": "4",
        },
        "WM": {
            "activeBackground":   rgb(p.title_bar),
            "activeBlend":        rgb(p.text),
            "activeForeground":   rgb(p.text),
            "inactiveBackground": rgb(p.title_bar_inactive),
            "inactiveBlend":      rgb(p.text_muted),
            "inactiveForeground": rgb(p.text_muted),
        },
    }


def render(scheme: dict[str, dict[str, str]]) -> str:
    out = []
    for section, kvs in scheme.items():
        out.append(f"[{section}]")
        for k, v in kvs.items():
            out.append(f"{k}={v}")
        out.append("")
    return "\n".join(out)


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.dirname(here)
    p = load_palette(os.path.join(repo, "ayu-mirage.toml"))
    out = os.path.join(here, "ayu-mirage.colors")
    with open(out, "w") as f:
        f.write(render(build_kde(p)))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
