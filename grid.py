"""Derive the primitives: five base colors and three tints make the fifteen
chromatic cells, and one ladder makes the greys.

A base color contributes its hue and nothing else. A tint is one perceived
brightness, Fairchild-Pirrotta L**, that every hue on the row lands on. Chroma
is as much as each hue holds at that brightness, in Oklab, up to a line drawn
`ROW_SPREAD` above the lowest ceiling on the row. sRGB is lopsided — red and
blue hold chroma when dark, yellow and green when light — so a row of bare
gamut maxima reads uneven: at a mid brightness red holds half again the
chroma yellow does, and the eye takes the surplus for brightness however the
model levels it. The line keeps every cell within the eye's threshold of the
row's chroma, so a row reads as one brightness and one saturation.

Each cell is solved, not looked up. At fixed hue and chroma, L** rises with
Oklab lightness, so a bisection lands the row's brightness to within rounding.
The chroma ceiling is a second bisection on top of the first: the largest
chroma at which that solve still lands inside the gamut.

One tint is set and two are solved. The bright row carries every ink,
and above a mid brightness its chroma falls as it climbs, red first, because a
light red is a pink. So `bright` is the brightness where the row holds the
most chroma among those where every cell clears `MIN_INK` on every ground ink
is written on. A set value drifts off that point the first time anything
under it moves. `normal` sits midway between `dim` and `bright`, so the three
rows climb in two equal steps of L**."""
from math import atan2, cos, degrees, radians, sin

from color import (contrast, hex_from_linear, grey, hk_lightness_linear,
                   oklab, oklab_to_linear)

# Below the gamut, some channel is negative: the color is too dark to hold the
# chroma asked of it. Above, some channel passes one. Inside, a cell is placed
# by its brightness alone.
EDGE = 1e-9
# Within rounding of the row: the first hex digit does not move at this.
LANDED = 1e-3
# Oklab chroma. How far above the row's lowest ceiling a hue may sit: the
# same 1.5 points the audit allows a row in L**.
ROW_SPREAD = 0.015
# WCAG contrast. What an ink must clear on every ground it is written on.
MIN_INK = 4.5
# L**. How close the bright row is solved: one 8-bit step moves a cell by more.
SOLVED = 0.01
# The golden ratio's inverse, the step of a golden-section search.
GOLDEN = (5 ** 0.5 - 1) / 2


def hue_of(hex6: str) -> float:
    """The Oklab hue angle of a base color, in degrees."""
    _, a, b = oklab(hex6)
    return degrees(atan2(b, a)) % 360


def solve(hue: float, chroma: float, target: float
          ) -> tuple[float, float, float] | None:
    """The linear color at this hue and chroma that reads as L** `target`, or
    None when no lightness inside the gamut gets there."""
    a, b = chroma * cos(radians(hue)), chroma * sin(radians(hue))
    lo, hi = 0.0, 1.0
    for _ in range(40):
        mid = (lo + hi) / 2
        rgb = oklab_to_linear(mid, a, b)
        if min(rgb) < 0:
            lo = mid
        elif max(rgb) > 1:
            hi = mid
        elif hk_lightness_linear(rgb) < target:
            lo = mid
        else:
            hi = mid
    rgb = oklab_to_linear((lo + hi) / 2, a, b)
    if min(rgb) < -EDGE or max(rgb) > 1 + EDGE:
        return None
    if abs(hk_lightness_linear(rgb) - target) > LANDED:
        return None
    return rgb


def ceiling(hue: float, target: float) -> float:
    """The most Oklab chroma this hue holds at L** `target` inside sRGB."""
    lo, hi = 0.0, 0.4
    for _ in range(30):
        mid = (lo + hi) / 2
        if solve(hue, mid, target) is None:
            hi = mid
        else:
            lo = mid
    return lo


def row(hues: dict[str, float], target: float) -> dict[str, str]:
    """Every hue at L** `target`, each at its own chroma ceiling up to the
    row's line."""
    ceilings = {name: ceiling(hue, target) for name, hue in hues.items()}
    line = min(ceilings.values()) + ROW_SPREAD
    cells = {}
    for name, hue in hues.items():
        chroma = min(ceilings[name], line)
        rgb = solve(hue, chroma, target)
        assert rgb is not None, (
            f"no {name} at chroma {chroma:.4f} reads as L** {target}, yet "
            f"that chroma is under the hue's ceiling")
        cells[name] = hex_from_linear(rgb)
    return cells


def cells(hues: dict[str, float], tint: str, target: float) -> dict[str, str]:
    """A row as primitives: `<hue>_<tint>`."""
    return {f"{name}_{tint}": cell for name, cell in row(hues, target).items()}


def row_chroma(hues: dict[str, float], target: float) -> float:
    """The chroma a row at L** `target` is levelled to: its lowest ceiling."""
    return min(ceiling(hue, target) for hue in hues.values())


def bright(hues: dict[str, float], dim: float, grounds: list[str]) -> float:
    """The L** of the bright row: the most chroma at or above the lowest
    brightness where every cell clears `MIN_INK` on every ground.

    Each hue's ceiling rises to its gamut cusp and falls past it, so their
    minimum has one peak, and on the brightnesses that clear the floor the
    best is the peak or, when the peak sits below the floor, the floor."""
    def clears(target: float) -> bool:
        return all(contrast(cell, ground) >= MIN_INK
                   for cell in row(hues, target).values() for ground in grounds)

    lo, hi = dim, 100.0
    assert clears(hi), (
        f"no bright row clears {MIN_INK}:1 on every ground: {grounds}")
    while hi - lo > SOLVED:
        mid = (lo + hi) / 2
        if clears(mid):
            hi = mid
        else:
            lo = mid
    floor = hi
    if row_chroma(hues, floor + SOLVED) <= row_chroma(hues, floor):
        return floor
    lo, hi = floor, 100.0
    left, right = hi - GOLDEN * (hi - lo), lo + GOLDEN * (hi - lo)
    at_left, at_right = row_chroma(hues, left), row_chroma(hues, right)
    while hi - lo > SOLVED:
        if at_left < at_right:
            lo, left, at_left = left, right, at_right
            right = lo + GOLDEN * (hi - lo)
            at_right = row_chroma(hues, right)
        else:
            hi, right, at_right = right, left, at_left
            left = hi - GOLDEN * (hi - lo)
            at_left = row_chroma(hues, left)
    peak = (lo + hi) / 2
    assert clears(peak), (
        f"the bright row's chroma peaks at L** {peak:.2f}, above the floor at "
        f"{floor:.2f}, yet does not clear {MIN_INK}:1 there")
    return peak


def neutrals(ladder: dict[str, float]) -> dict[str, str]:
    """`black`, `white`, and the greys in between, darkest first.

    Five rungs climb from `floor` by `step`, then `text_muted` and `text` sit
    above them. All in Oklab lightness, which for a neutral is the cube root
    of its linear value, so a rung's luminance is its lightness cubed."""
    lights = [ladder["floor"] + i * ladder["step"] for i in range(5)]
    lights += [ladder["text_muted"], ladder["text"]]
    assert lights == sorted(lights) and 0 < lights[0] and lights[-1] < 1, (
        f"the grey ladder is not a climb from black to white: {lights}")
    out = {"black": "#000000"}
    out.update({f"gray_{i + 1}": grey(light ** 3)
                for i, light in enumerate(lights)})
    out["white"] = "#ffffff"
    return out


def primitives(base: dict[str, str], dim: float, ladder: dict[str, float],
               grounds: list[str]) -> dict[str, str]:
    """Every primitive the semantic layer can name.

    `dim` is the one tint set. `bright` is solved to clear `MIN_INK` on each
    of `grounds`, primitives named off the bright and normal rows, and
    `normal` is the midpoint of the two."""
    hues = {name: hue_of(hex6) for name, hex6 in base.items()}
    out = neutrals(ladder)
    out.update(cells(hues, "dim", dim))
    missing = [name for name in grounds if name not in out]
    assert not missing, (
        f"an ink ground is not a primitive off the bright and normal rows: "
        f"{missing}")
    top = bright(hues, dim, [out[name] for name in grounds])
    out.update(cells(hues, "bright", top))
    out.update(cells(hues, "normal", (dim + top) / 2))
    return out
