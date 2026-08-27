#!/usr/bin/env python3
"""Check ayu-graphite.toml against the contrast rules the targets depend on.

Exits non-zero on a violation so `make audit` fails the build. Every ratio it
prints carries an APCA Lc beside it — WCAG 2 overstates contrast at the dark
end, and a dark theme is all dark end. The gate stays WCAG, because that is
what the rules are written against.

Five rules:

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
  perceived every cell of a tint row must look equally bright. Luminance does
            not say that on its own: a saturated color reads brighter than a
            dull one at the same luminance, and the equal-luminance rows this
            palette replaced spread 22.6 points. Nothing else defends that
            property, so a hand-edit would break it silently.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)
from color import apca, contrast, hk_lightness, luminance
from palette import Palette, load_palette, load_primitives

# Separate enough to read as two layers. 1.10 is roughly one step of the
# neutral ramp — below that the eye merges them under any gamma.
MIN_LAYER = 1.10
MIN_INK = 4.5
# The widest floor a color can hold in both roles at once. 4.5 both ways is an
# empty band on this background; 3.0 leaves luminance 0.139 to 0.212 to aim at.
MIN_ANSI_DUAL = 3.0
# Room for the gamut search to round into. The rebuilt rows land inside 1.0,
# and the equal-luminance rows they replaced were out by 22.6.
MAX_PERCEIVED_SPREAD = 1.5

HUES = ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white")
CHROMATIC = HUES[1:7]
TINTS = ("vivid", "bright", "normal", "dim")


def both(fg: str, bg: str) -> str:
    """The pair as a violation line states it: WCAG ratio, then Lc."""
    return f"{contrast(fg, bg):.2f}:1 / Lc {abs(apca(fg, bg)):.0f}"


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
        f"layers: {a} vs {b} = {both(d[a], d[b])} (< {MIN_LAYER}:1)"
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
            if contrast(d[fg], d[s]) < MIN_INK:
                out.append(f"ink: {fg} on {s} = {both(d[fg], d[s])} "
                           f"(< {MIN_INK}:1)")
    for fill in FILLS:
        if contrast(p.on_accent, d[fill]) < MIN_INK:
            out.append(f"ink: on_accent on {fill} = "
                       f"{both(p.on_accent, d[fill])} (< {MIN_INK}:1)")
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
        bright = d[f"ansi_bright_{hue}"]
        if contrast(normal, p.bg) < MIN_ANSI_DUAL:
            out.append(f"roles: ansi_{hue} as ink on bg = "
                       f"{both(normal, p.bg)} (< {MIN_ANSI_DUAL}:1)")
        if contrast(p.text, normal) < MIN_ANSI_DUAL:
            out.append(f"roles: text on ansi_{hue} as fill = "
                       f"{both(p.text, normal)} (< {MIN_ANSI_DUAL}:1)")
        if contrast(bright, p.bg) < MIN_INK:
            out.append(f"roles: ansi_bright_{hue} as ink on bg = "
                       f"{both(bright, p.bg)} (< {MIN_INK}:1)")
    return out


def tint_rows(primitives: dict[str, str]) -> dict[str, dict[str, str]]:
    """The chromatic primitives regrouped as tint -> hue -> hex."""
    rows: dict[str, dict[str, str]] = {t: {} for t in TINTS}
    for key, value in primitives.items():
        hue, _, tint = key.rpartition("_")
        if hue and tint in rows:
            rows[tint][hue] = value
    return rows


def check_perceived(primitives: dict[str, str]) -> list[str]:
    out = []
    for tint, cells in tint_rows(primitives).items():
        if len(cells) < 2:
            continue
        lit = {h: hk_lightness(v) for h, v in cells.items()}
        low, high = min(lit, key=lit.get), max(lit, key=lit.get)
        spread = lit[high] - lit[low]
        if spread > MAX_PERCEIVED_SPREAD:
            out.append(f"perceived: {tint} row spreads {spread:.2f} points — "
                       f"{high} {lit[high]:.1f} vs {low} {lit[low]:.1f} "
                       f"(> {MAX_PERCEIVED_SPREAD})")
    return out


def report(p: Palette, primitives: dict[str, str]) -> None:
    """The pairs and rows worth seeing even when nothing is broken."""
    d = p.as_dict()
    print(f"  {'pair':34}{'WCAG':>9}{'APCA':>8}")
    rows = [("text on bg", p.text, p.bg),
            ("text_muted on bg", p.text_muted, p.bg),
            ("accent on bg", p.accent, p.bg),
            ("on_accent on accent", p.on_accent, p.accent)]
    for hue in CHROMATIC:
        rows.append((f"ansi_{hue} as ink on bg", d[f"ansi_{hue}"], p.bg))
        rows.append((f"text on ansi_{hue} as fill", p.text, d[f"ansi_{hue}"]))
    for label, fg, bg in rows:
        print(f"  {label:34}{contrast(fg, bg):8.2f}{abs(apca(fg, bg)):8.0f}")
    print(f"\n  {'tint row':34}{'L**':>9}{'spread':>8}")
    for tint, cells in tint_rows(primitives).items():
        lit = [hk_lightness(v) for v in cells.values()]
        print(f"  {tint:34}{sum(lit) / len(lit):9.1f}"
              f"{max(lit) - min(lit):8.2f}")


def main() -> None:
    path = os.path.join(os.path.dirname(HERE), "ayu-graphite.toml")
    p = load_palette(path)
    primitives = load_primitives(path)
    problems = (check_layers(p) + check_ink(p) + check_ansi(p)
                + check_ansi_roles(p) + check_perceived(primitives))
    for line in problems:
        print(line)
    if problems:
        print(f"\n{len(problems)} problem(s)")
        sys.exit(1)
    print("palette ok: layers, ink, ansi, roles, perceived")
    report(p, primitives)


if __name__ == "__main__":
    main()
