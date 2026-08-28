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
chroma at which that solve still lands inside the gamut."""
from math import atan2, cos, degrees, radians, sin

from color import (hex_from_linear, grey, hk_lightness_linear, oklab,
                   oklab_to_linear)

# Below the gamut, some channel is negative: the color is too dark to hold the
# chroma asked of it. Above, some channel passes one. Inside, a cell is placed
# by its brightness alone.
EDGE = 1e-9
# Within rounding of the row: the first hex digit does not move at this.
LANDED = 1e-3
# Oklab chroma. How far above the row's lowest ceiling a hue may sit: the
# same 1.5 points the audit allows a row in L**.
ROW_SPREAD = 0.015


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


def chromatic(base: dict[str, str], tints: dict[str, float]) -> dict[str, str]:
    """`<hue>_<tint>` for every base color and every tint."""
    hues = {name: hue_of(hex6) for name, hex6 in base.items()}
    cells = {}
    for tint, target in tints.items():
        ceilings = {name: ceiling(hue, target) for name, hue in hues.items()}
        line = min(ceilings.values()) + ROW_SPREAD
        for name, hue in hues.items():
            chroma = min(ceilings[name], line)
            rgb = solve(hue, chroma, target)
            assert rgb is not None, (
                f"{name}_{tint}: no {name} at chroma {chroma:.4f} reads as "
                f"L** {target}, yet that chroma is under the hue's ceiling")
            cells[f"{name}_{tint}"] = hex_from_linear(rgb)
    return cells


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


def primitives(base: dict[str, str], tints: dict[str, float],
               ladder: dict[str, float]) -> dict[str, str]:
    """Every primitive the semantic layer can name."""
    return {**neutrals(ladder), **chromatic(base, tints)}
