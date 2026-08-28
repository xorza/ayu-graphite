#!/usr/bin/env python3
"""Check ayu-graphite.toml against the contrast rules the targets depend on.

Exits non-zero on a violation so `make audit` fails the build. Every ratio it
prints carries an APCA Lc beside it — WCAG 2 overstates contrast at the dark
end, and a dark theme is all dark end. The gate stays WCAG, because that is
what the rules are written against.

Six rules:

  layers    chrome that stacks in one view must be visually separable — a
            button whose fill equals its panel disappears (that was the KDE
            bug), and a border that equals its panel draws nothing.
  ink       every foreground must clear 4.5:1 on the surfaces it lands on.
            The `on_accent` family exists because `text` on `accent` is 1.28.
            Red is the one exception: a red that reads as red sits at the
            luminance where 4.5:1 holds on `bg` alone, so above `bg` it is
            held to 3:1, the floor for large text and controls.
  ansi      per hue, dim < normal in luminance, and no two slots of one row
            share a value. The grid has one ink tint, so the normal row is
            the bright row again for every hue but black and white, and the
            cyan row is the blue row again: both are checked to be exactly
            that, rather than counted as duplicates.
  roles     a program picks any slot as a foreground (SGR 30-37, 90-97) or as
            a background (SGR 40-47, 100-107) and the theme cannot tell which.
            On this bg nothing clears 4.5:1 in both roles — ink needs
            luminance >= 0.234, a fill needs <= 0.146 — and with one ink
            tint the palette takes the foreground side: slots 1-6 carry the
            full 4.5:1 as ink, and `text` on one as a fill reads about 2:1.
            Slots 0 and 7 sit out: black is the background itself and white
            is the text.
  perceived every cell of a level tint row must look equally bright, and
            every cell of a per-hue tint must land on its own brightness.
            Luminance does not say that on its own: a saturated color reads
            brighter than a dull one at the same luminance, and the
            equal-luminance rows this palette replaced spread 22.6 points.
  chroma    every cell of a level tint row must be about equally saturated,
            in Oklab. A row of gamut maxima is not: red holds half again
            what yellow does at a mid brightness, and the eye takes the
            surplus for brightness however the row is levelled.

The last two are what grid.py solves for. The checks stay because the solver
rounds each cell to 8 bits, and because a change to the solver should fail
here, on the row it moved, and not in a theme.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import grid
from color import apca, contrast, hk_lightness, luminance, oklch
from palette import Palette, load_source

# Separate enough to read as two layers. 1.10 is roughly one step of the
# neutral ramp — below that the eye merges them under any gamma.
MIN_LAYER = 1.10
MIN_INK = 4.5
# WCAG's floor for large text and for a control against its ground.
MIN_INK_LARGE = 3.0
# Room for the gamut search to round into. The rebuilt rows land inside 1.0,
# and the equal-luminance rows they replaced were out by 22.6.
MAX_PERCEIVED_SPREAD = 1.5
# Oklab chroma, times 100: the spread the grid allows a row, plus what one
# 8-bit step moves a cell by.
MAX_CHROMA_SPREAD = grid.ROW_SPREAD * 100 + 0.3

HUES = ("black", "red", "green", "yellow", "blue", "magenta", "cyan", "white")
# The slot that is another slot's row again. It is held equal to its source
# rather than counted as a duplicate, and sits out of the per-hue reports.
ALIAS = {"cyan": "blue"}
CHROMATIC = tuple(hue for hue in HUES[1:7] if hue not in ALIAS)
TINTS = ("bright", "dim")


def both(fg: str, bg: str) -> str:
    """The pair as a violation line states it: WCAG ratio, then Lc."""
    return f"{contrast(fg, bg):.2f}:1 / Lc {abs(apca(fg, bg)):.0f}"


def check_layers(p: Palette) -> list[str]:
    pairs = [
        ("bg", "panel"), ("panel", "elem"), ("elem", "elem_hover"),
        ("elem_hover", "elem_active"), ("panel", "surface"),
        ("elem", "elem_disabled"), ("panel", "border"), ("elem", "border"),
        ("bg", "chat_msg_bg"), ("bg", "selection_bg"),
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
    "error":        ["bg"],
    "hint":         CHROME,
    # The word-level diff fills are backgrounds, and the ink Claude Code draws
    # on them is its own near-white syntax foreground, not `text`.
    "ansi_bright_white": ["diff_word_plus", "diff_word_minus"],
}
# The pairings held to 3:1. Red reads as red only at a luminance where 4.5:1
# holds on `bg` and nowhere lighter, so on every other chrome layer, and on
# a selection — which KDE's Colors:Selection paints its negative in — it is
# held to the large-text floor instead.
INK_LARGE = {
    "error": [s for s in CHROME if s != "bg"],
    "ansi_bright_red": ["selection_bg"],
}
# Bright fills are only ever written on with on_accent. accent_active is not
# among them: its one consumer is Telegram's button ripple, which carries no
# ink, and holding it to 4.5:1 under black would pin the whole normal row.
FILLS = ["accent", "accent_hover", "success", "warning", "error"]


def check_ink(p: Palette) -> list[str]:
    d = p.as_dict()
    out = []
    for fg, surfaces in INK.items():
        for s in surfaces:
            if contrast(d[fg], d[s]) < MIN_INK:
                out.append(f"ink: {fg} on {s} = {both(d[fg], d[s])} "
                           f"(< {MIN_INK}:1)")
    for fg, surfaces in INK_LARGE.items():
        for s in surfaces:
            if contrast(d[fg], d[s]) < MIN_INK_LARGE:
                out.append(f"ink: {fg} on {s} = {both(d[fg], d[s])} "
                           f"(< {MIN_INK_LARGE}:1)")
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
        if hue in ("black", "white"):
            if not (ld < ln < lb):
                out.append(f"ansi: {hue} not dim<normal<bright ({dim} "
                           f"{ld:.3f} / {normal} {ln:.3f} / {bright} {lb:.3f})")
            continue
        if not ld < ln:
            out.append(f"ansi: {hue} not dim<normal "
                       f"({dim} {ld:.3f} / {normal} {ln:.3f})")
        if normal != bright:
            out.append(f"ansi: ansi_{hue} is {normal}, not ansi_bright_{hue} "
                       f"({bright})")
    for prefix in ("ansi_", "ansi_bright_", "ansi_dim_"):
        seen: dict[str, str] = {}
        for hue in HUES:
            if hue in ALIAS:
                continue
            key = f"{prefix}{hue}"
            if d[key] in seen:
                out.append(f"ansi: {key} duplicates {seen[d[key]]} ({d[key]})")
            seen[d[key]] = key
    for hue, source in ALIAS.items():
        for prefix in ("ansi_", "ansi_bright_", "ansi_dim_"):
            own, theirs = d[f"{prefix}{hue}"], d[f"{prefix}{source}"]
            if own != theirs:
                out.append(f"ansi: {prefix}{hue} is {own}, not "
                           f"{prefix}{source} ({theirs})")
    return out


def check_ansi_roles(p: Palette) -> list[str]:
    d = p.as_dict()
    out = []
    for hue in CHROMATIC:
        bright = d[f"ansi_bright_{hue}"]
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


def check_perceived(primitives: dict[str, str], tints: dict) -> list[str]:
    out = []
    for tint, cells in tint_rows(primitives).items():
        if len(cells) < 2:
            continue
        lit = {h: hk_lightness(v) for h, v in cells.items()}
        if not grid.level(tints[tint]):
            for hue, target in tints[tint].items():
                if abs(lit[hue] - target) > MAX_PERCEIVED_SPREAD:
                    out.append(f"perceived: {hue}_{tint} reads {lit[hue]:.1f}, "
                               f"not {target} (off by > "
                               f"{MAX_PERCEIVED_SPREAD})")
            continue
        low, high = min(lit, key=lit.get), max(lit, key=lit.get)
        spread = lit[high] - lit[low]
        if spread > MAX_PERCEIVED_SPREAD:
            out.append(f"perceived: {tint} row spreads {spread:.2f} points — "
                       f"{high} {lit[high]:.1f} vs {low} {lit[low]:.1f} "
                       f"(> {MAX_PERCEIVED_SPREAD})")
    return out


def check_chroma(primitives: dict[str, str], tints: dict) -> list[str]:
    out = []
    for tint, cells in tint_rows(primitives).items():
        if len(cells) < 2 or not grid.level(tints[tint]):
            continue
        chroma = {h: oklch(v)[1] * 100 for h, v in cells.items()}
        low, high = min(chroma, key=chroma.get), max(chroma, key=chroma.get)
        spread = chroma[high] - chroma[low]
        if spread > MAX_CHROMA_SPREAD:
            out.append(f"chroma: {tint} row spreads {spread:.2f} points — "
                       f"{high} {chroma[high]:.1f} vs {low} {chroma[low]:.1f} "
                       f"(> {MAX_CHROMA_SPREAD})")
    return out


def report(p: Palette, primitives: dict[str, str], tints: dict) -> None:
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
    print(f"\n  {'tint row':34}{'L**':>9}{'spread':>8}{'chroma':>8}{'spread':>8}")
    for tint, cells in tint_rows(primitives).items():
        lit = [hk_lightness(v) for v in cells.values()]
        chroma = [oklch(v)[1] * 100 for v in cells.values()]
        lightness = (f"{sum(lit) / len(lit):9.1f}" if grid.level(tints[tint])
                     else f"{min(lit):4.0f}-{max(lit):.0f}".rjust(9))
        print(f"  {tint:34}{lightness}"
              f"{max(lit) - min(lit):8.2f}"
              f"{sum(chroma) / len(chroma):8.1f}"
              f"{max(chroma) - min(chroma):8.2f}")


def main() -> None:
    src = load_source()
    p, primitives, tints = src.palette, src.primitives, src.tints
    problems = (check_layers(p) + check_ink(p) + check_ansi(p)
                + check_ansi_roles(p) + check_perceived(primitives, tints)
                + check_chroma(primitives, tints))
    for line in problems:
        print(line)
    if problems:
        print(f"\n{len(problems)} problem(s)")
        sys.exit(1)
    print("palette ok: layers, ink, ansi, roles, perceived, chroma")
    report(p, primitives, tints)


if __name__ == "__main__":
    main()
