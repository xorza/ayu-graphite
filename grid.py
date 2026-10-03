"""Derive the primitives: the base colors and three tints make the chromatic
cells, one ladder makes the greys, and the selection fill is solved apart.

A base color contributes its hue and nothing else. A tint is one perceived
brightness, Fairchild-Pirrotta L**, that every hue on the row lands on. Chroma
is as much as each hue holds at that brightness, in Oklab, up to a line drawn
`ROW_SPREAD` above the lowest ceiling on the row. sRGB is lopsided — red and
blue hold chroma when dark, yellow and green when light — so a row of bare
gamut maxima is level in L**, which already counts chroma as brightness, but
not in saturation: a hue with half again its neighbours' chroma stands out of
the row on its own. The line keeps every cell within the eye's threshold of
the row's chroma, so a row reads as one brightness and one saturation.

Each cell is solved, not looked up. At fixed hue and chroma, L** rises with
Oklab lightness, so a bisection lands the row's brightness to within rounding.
The chroma ceiling is a second bisection on top of the first: the largest
chroma at which that solve still lands inside the gamut.

One tint is set and two are solved. Above a mid brightness a row's chroma
falls as it climbs, red first, because a light red is a pink. So `bright` is
the brightness where the syntax hues, held level, keep the most chroma among
those where every cell clears `MIN_INK` on every ground ink is written on. A
set value drifts off that point the first time anything under it moves.
`normal` sits midway between `dim` and `bright`, so the three rows climb in
two equal steps of L**.

The bright row is where the inks would sit level, not where they sit. Each
syntax hue's ink takes the same rule the row does, alone: the most chroma at
or above the brightness where it clears `MIN_INK`, under one chroma line
drawn `ROW_SPREAD` above the weakest ink's best. A hue that holds that line
over a band of brightness sits in the middle of the band. So red sits low,
where it is still red and not a pink, and yellow sits high, where it is
still yellow and not a gold or an olive. The inks stay level in chroma, not
in brightness.

A terminal hue sits on every row, the bright one too, and sets no line: it
is drawn only by programs in a terminal, so it is held under the syntax
hues' chroma rather than dragging all of them down to its own."""
from collections.abc import Callable
from math import atan2, cos, degrees, inf, radians, sin

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


def line_at(hues: dict[str, float], target: float) -> float:
    """The chroma line of a row at L** `target`: the lowest ceiling among
    `hues`, plus `ROW_SPREAD`."""
    return min(ceiling(hue, target) for hue in hues.values()) + ROW_SPREAD


def cell(hue: float, target: float, line: float) -> str:
    """One hue at L** `target`, at its own chroma ceiling up to `line`."""
    chroma = min(ceiling(hue, target), line)
    rgb = solve(hue, chroma, target)
    assert rgb is not None, (
        f"no hue {hue:.1f} at chroma {chroma:.4f} reads as L** {target}, yet "
        f"that chroma is under the hue's ceiling")
    return hex_from_linear(rgb)


def row(hues: dict[str, float], target: float, line: float) -> dict[str, str]:
    """Every hue at L** `target`, each at its own chroma ceiling up to
    `line`."""
    return {name: cell(hue, target, line) for name, hue in hues.items()}


def threshold(holds: Callable[[float], bool], inside: float,
              outside: float) -> float:
    """Where `holds` stops holding between L** `inside`, where it holds, and
    `outside`, where it does not, to within `SOLVED`: the side that holds."""
    while abs(outside - inside) > SOLVED:
        mid = (inside + outside) / 2
        if holds(mid):
            inside = mid
        else:
            outside = mid
    return inside


def peak(f: Callable[[float], float], lo: float, hi: float) -> float:
    """Where `f` peaks on [lo, hi], to within `SOLVED`, for an `f` with one
    peak there: a golden-section search."""
    left, right = hi - GOLDEN * (hi - lo), lo + GOLDEN * (hi - lo)
    at_left, at_right = f(left), f(right)
    while hi - lo > SOLVED:
        if at_left < at_right:
            lo, left, at_left = left, right, at_right
            right = lo + GOLDEN * (hi - lo)
            at_right = f(right)
        else:
            hi, right, at_right = right, left, at_left
            left = hi - GOLDEN * (hi - lo)
            at_left = f(left)
    return (lo + hi) / 2


def summit(f: Callable[[float], float], floor: float) -> float:
    """Where `f`, with one peak, is highest at or above L** `floor`: the
    floor itself when `f` already falls there."""
    if f(floor + SOLVED) <= f(floor):
        return floor
    return peak(f, floor, 100.0)


def bright(hues: dict[str, float], dim: float, grounds: list[str]) -> float:
    """The L** of the bright row: the most chroma at or above the lowest
    brightness where every cell clears `MIN_INK` on every ground.

    Each hue's ceiling rises to its gamut cusp and falls past it, so their
    minimum has one peak, and on the brightnesses that clear the floor the
    best is the peak or, when the peak sits below the floor, the floor."""
    def clears(target: float) -> bool:
        cells = row(hues, target, line_at(hues, target)).values()
        return all(contrast(ink, ground) >= MIN_INK
                   for ink in cells for ground in grounds)

    assert clears(100.0), (
        f"no bright row clears {MIN_INK}:1 on every ground: {grounds}")
    floor = threshold(clears, 100.0, dim)
    top = summit(lambda target: line_at(hues, target), floor)
    assert clears(top), (
        f"the bright row's chroma peaks at L** {top:.2f}, above the floor at "
        f"{floor:.2f}, yet does not clear {MIN_INK}:1 there")
    return top


def ink_floor(hue: float, lo: float, grounds: list[str]) -> float:
    """The lowest L** at or above `lo` where `hue`, at its own ceiling,
    clears `MIN_INK` on every ground. Less chroma at the same L** carries
    more luminance, so a cell cut to a line clears there too."""
    def clears(target: float) -> bool:
        ink = cell(hue, target, inf)
        return all(contrast(ink, ground) >= MIN_INK for ground in grounds)

    assert clears(100.0), (
        f"hue {hue:.1f} clears {MIN_INK}:1 nowhere: {grounds}")
    return threshold(clears, 100.0, lo)


def inks(hues: dict[str, float], lo: float, grounds: list[str]
         ) -> dict[str, str]:
    """Each hue's ink: the most chroma at or above its own `MIN_INK` floor,
    under a line `ROW_SPREAD` above the weakest ink's best, and in the middle
    of the band of brightness that holds the line, for a hue that holds it
    over one."""
    floors = {name: ink_floor(hue, lo, grounds) for name, hue in hues.items()}
    bests = {name: summit(lambda target, hue=hue: ceiling(hue, target),
                          floors[name])
             for name, hue in hues.items()}
    line = min(ceiling(hues[name], best)
               for name, best in bests.items()) + ROW_SPREAD
    out = {}
    for name, hue in hues.items():
        floor, best = floors[name], bests[name]
        def holds(target: float, hue: float = hue) -> bool:
            return ceiling(hue, target) >= line

        if not holds(best):
            target = best
        else:
            low = floor if holds(floor) else threshold(holds, best, floor)
            target = (low + threshold(holds, best, 100.0)) / 2
        out[name] = cell(hue, target, line)
        assert all(contrast(out[name], ground) >= MIN_INK
                   for ground in grounds), (
            f"{name}'s ink at L** {target:.2f} does not clear {MIN_INK}:1")
    return out


def selection(hue: float, drawn: list[str]) -> str:
    """The lightest fill at `hue` on which every ink clears `MIN_INK`.

    Lighter reads more clearly as a selection, and every ink drawn over it
    loses contrast as it lightens, so the bisection lands where the weakest
    ink meets the floor."""
    def clears(target: float) -> bool:
        ground = cell(hue, target, inf)
        return all(contrast(ink, ground) >= MIN_INK for ink in drawn)

    assert clears(0.0), (
        f"an ink does not clear {MIN_INK}:1 even on black: {drawn}")
    return cell(hue, threshold(clears, 0.0, 100.0), inf)


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
               grounds: list[str], terminal: list[str], selection_hue: str,
               selection_inks: list[str]) -> dict[str, str]:
    """Every primitive the semantic layer can name.

    `dim` is the one tint set. `bright` is solved to clear `MIN_INK` on each
    of `grounds`, primitives named off the bright and normal rows, and
    `normal` is the midpoint of the two. A row's chroma line comes from every
    hue but the `terminal` ones, which sit on the row under that line. The
    syntax hues' bright cells are their inks, each solved alone. `selection`
    is the one primitive off the grid: a fill of the base hue
    `selection_hue`, solved from the primitives `selection_inks` drawn over
    it."""
    hues = {name: hue_of(hex6) for name, hex6 in base.items()}
    unknown = [name for name in terminal if name not in hues]
    assert not unknown, f"not a base hue: {unknown}"
    syntax = {name: hue for name, hue in hues.items() if name not in terminal}
    out = neutrals(ladder)

    def put(names: dict[str, float], tint: str, target: float,
            line: float) -> None:
        out.update({f"{name}_{tint}": hex6
                    for name, hex6 in row(names, target, line).items()})

    put(hues, "dim", dim, line_at(syntax, dim))
    missing = [name for name in grounds if name not in out]
    assert not missing, (
        f"an ink ground is not a primitive off the bright and normal rows: "
        f"{missing}")
    on = [out[name] for name in grounds]
    top = bright(syntax, dim, on)
    put({name: hues[name] for name in terminal}, "bright", top,
        line_at(syntax, top))
    out.update({f"{name}_bright": hex6
                for name, hex6 in inks(syntax, dim, on).items()})
    middle = (dim + top) / 2
    put(hues, "normal", middle, line_at(syntax, middle))
    missing = [name for name in selection_inks if name not in out]
    assert not missing, f"a selection ink is not a grid primitive: {missing}"
    out["selection"] = selection(hues[selection_hue],
                                 [out[name] for name in selection_inks])
    return out
