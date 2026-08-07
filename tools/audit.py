#!/usr/bin/env python3
"""Check ayu-graphite.toml against the contrast rules the targets depend on.

Exits non-zero on a violation so `make audit` fails the build. Three rules:

  layers    chrome that stacks in one view must be visually separable — a
            button whose fill equals its panel disappears (that was the KDE
            bug), and a border that equals its panel draws nothing.
  ink       every foreground must clear 4.5:1 on the surfaces it lands on.
            The `on_accent` family exists because `text` on `accent` is 1.28.
  ansi      per hue, dim < normal < bright in luminance, and no two of the
            16 share a value — a terminal that renders bright red as normal
            red has thrown away half its palette.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from palette import Palette, load_palette

# Separate enough to read as two layers. 1.10 is roughly one step of the
# neutral ramp — below that the eye merges them under any gamma.
MIN_LAYER = 1.10
MIN_INK = 4.5

HUES = ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white")


def luminance(hex6: str) -> float:
    h = hex6.lstrip("#")
    ch = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    ch = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in ch]
    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]


def contrast(a: str, b: str) -> float:
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def check_layers(p: Palette) -> list[str]:
    pairs = [
        ("bg", "panel"), ("panel", "elem"), ("elem", "elem_hover"),
        ("elem_hover", "elem_active"), ("panel", "surface"),
        ("elem", "elem_disabled"), ("panel", "border"), ("elem", "border"),
        ("bg", "chat_msg_bg"), ("bg", "selection_bg"),
    ]
    d = p.as_dict()
    return [
        f"layers: {a} vs {b} = {contrast(d[a], d[b]):.2f} (< {MIN_LAYER})"
        for a, b in pairs
        if contrast(d[a], d[b]) < MIN_LAYER
    ]


# Each foreground against the surfaces it is actually painted on. Hover and
# press fills carry body text only — status colors and labels never land
# there — so widening any row to elem_hover/elem_active would be checking a
# pairing no target emits. text_disabled is absent on purpose: WCAG excludes
# disabled controls and dimming is the whole point of the role.
CHROME = ["bg", "panel", "surface", "elem", "title_bar", "chat_msg_bg"]
INK = {
    "text":         CHROME + ["elem_hover", "elem_active", "selection_bg"],
    "text_muted":   CHROME + ["selection_bg"],
    "selection_fg": ["selection_bg"],
    "accent":       CHROME + ["selection_bg"],
    "success":      CHROME + ["selection_bg"],
    "warning":      CHROME + ["selection_bg"],
    "error":        CHROME,
    "hint":         CHROME,
    # Inside a selection the plain red loses too much against the blue fill;
    # KDE's Colors:Selection reaches for the bright step instead.
    "ansi_bright_red": ["selection_bg"],
}
# Bright fills are only ever written on with on_accent.
FILLS = ["accent", "accent_hover", "accent_active", "success", "warning",
         "error"]


def check_ink(p: Palette) -> list[str]:
    d = p.as_dict()
    out = []
    for fg, surfaces in INK.items():
        for s in surfaces:
            r = contrast(d[fg], d[s])
            if r < MIN_INK:
                out.append(f"ink: {fg} on {s} = {r:.2f} (< {MIN_INK})")
    for fill in FILLS:
        r = contrast(p.on_accent, d[fill])
        if r < MIN_INK:
            out.append(f"ink: on_accent on {fill} = {r:.2f} (< {MIN_INK})")
    return out


def check_ansi(p: Palette) -> list[str]:
    d = p.as_dict()
    out = []
    for hue in HUES:
        dim, normal, bright = (d[f"ansi_dim_{hue}"], d[f"ansi_{hue}"],
                               d[f"ansi_bright_{hue}"])
        ld, ln, lb = luminance(dim), luminance(normal), luminance(bright)
        if not (ld < ln < lb):
            out.append(f"ansi: {hue} not dim<normal<bright "
                       f"({dim} {ld:.3f} / {normal} {ln:.3f} / {bright} {lb:.3f})")
    seen: dict[str, str] = {}
    for prefix in ("ansi_", "ansi_bright_"):
        for hue in HUES:
            key = f"{prefix}{hue}"
            if d[key] in seen:
                out.append(f"ansi: {key} duplicates {seen[d[key]]} ({d[key]})")
            seen[d[key]] = key
    return out


def main() -> None:
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = load_palette(os.path.join(repo, "ayu-graphite.toml"))
    problems = check_layers(p) + check_ink(p) + check_ansi(p)
    for line in problems:
        print(line)
    if problems:
        print(f"\n{len(problems)} problem(s)")
        sys.exit(1)
    print("palette ok: layers, ink, ansi")


if __name__ == "__main__":
    main()
