#!/usr/bin/env python3
"""Check ayu-graphite.toml against the contrast rules the targets depend on.

Exits non-zero on a violation so `make audit` fails the build. Four rules:

  layers    chrome that stacks in one view must be visually separable — a
            button whose fill equals its panel disappears (that was the KDE
            bug), and a border that equals its panel draws nothing.
  ink       every foreground must clear 4.5:1 on the surfaces it lands on.
            The `on_accent` family exists because `text` on `accent` is 1.28.
  ansi      per hue, dim < normal < bright in luminance, and no two of the
            16 share a value — a terminal that renders bright red as normal
            red has thrown away half its palette.
  roles     a program picks any slot as a foreground (SGR 30-37, 90-97) or as
            a background (SGR 40-47, 100-107) and the theme cannot tell which.
            On this bg nothing clears 4.5:1 in both roles — ink needs
            luminance >= 0.234, a fill needs <= 0.125 — so the rows divide the
            work. Normal 1-6 hold 3:1 each way, which is what keeps `text`
            legible on an SGR 4x fill. Bright 1-6 are foreground-first and
            carry the full 4.5:1 instead. Slots 0 and 7 sit out: black is the
            background itself and white is the text.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from palette import Palette, load_palette

# Separate enough to read as two layers. 1.10 is roughly one step of the
# neutral ramp — below that the eye merges them under any gamma.
MIN_LAYER = 1.10
MIN_INK = 4.5
# The widest floor a color can hold in both roles at once. 4.5 both ways is an
# empty band on this background; 3.0 leaves luminance 0.139 to 0.212 to aim at.
MIN_ANSI_DUAL = 3.0

HUES = ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white")
CHROMATIC = HUES[1:7]


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
        ("success_bg", "diff_word_plus"), ("error_bg", "diff_word_minus"),
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
    # The word-level diff fills are backgrounds, and the ink Claude Code draws
    # on them is its own near-white syntax foreground, not `text`.
    "ansi_bright_white": ["diff_word_plus", "diff_word_minus"],
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


def check_ansi_roles(p: Palette) -> list[str]:
    d = p.as_dict()
    out = []
    for hue in CHROMATIC:
        normal = d[f"ansi_{hue}"]
        as_ink = contrast(normal, p.bg)
        as_fill = contrast(p.text, normal)
        if as_ink < MIN_ANSI_DUAL:
            out.append(f"roles: ansi_{hue} as ink on bg = {as_ink:.2f} "
                       f"(< {MIN_ANSI_DUAL})")
        if as_fill < MIN_ANSI_DUAL:
            out.append(f"roles: text on ansi_{hue} as fill = {as_fill:.2f} "
                       f"(< {MIN_ANSI_DUAL})")
        bright = contrast(d[f"ansi_bright_{hue}"], p.bg)
        if bright < MIN_INK:
            out.append(f"roles: ansi_bright_{hue} as ink on bg = {bright:.2f} "
                       f"(< {MIN_INK})")
    return out


def main() -> None:
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    p = load_palette(os.path.join(repo, "ayu-graphite.toml"))
    problems = (check_layers(p) + check_ink(p) + check_ansi(p)
                + check_ansi_roles(p))
    for line in problems:
        print(line)
    if problems:
        print(f"\n{len(problems)} problem(s)")
        sys.exit(1)
    print("palette ok: layers, ink, ansi, roles")


if __name__ == "__main__":
    main()
