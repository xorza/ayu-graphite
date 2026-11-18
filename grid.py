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

One tint is set and three are solved. Above a mid brightness a row's chroma
falls as it climbs, red first, because a light red is a pink. So `bright` is
the brightness where the syntax hues, held level, keep the most chroma among
those where every cell clears `MIN_INK` on every ground ink is written on. A
set value drifts off that point the first time anything under it moves.
`normal` sits midway between `dim` and `bright`, so the three rows climb in
two equal steps of L**. `light` is the lowest brightness above `normal` where
every cell clears an APCA floor as text, the row ANSI 1-6 are read in.

The bright row is where the inks would sit level, not where they sit. Each
syntax hue's ink takes the same rule the row does, alone: the most chroma at
or above the brightness where it clears `MIN_INK`, under one chroma line
drawn `ROW_SPREAD` above the weakest ink's best. A hue that holds that line
over a band of brightness sits in the middle of the band. So red sits low,
where it is still red and not a pink, and yellow sits high, where it is
still yellow and not a gold or an olive. An APCA floor then lifts the inks
that sit darkest, and the line drops to what the weakest holds there. The
inks stay level in chroma, not in brightness.

A terminal hue sits on every row, the bright one too, and sets no line: it
is drawn only by programs in a terminal, so it is held under the syntax
hues' chroma rather than dragging all of them down to its own.

Each scheme solves its own grid from the same hues. "Climbs" above reads for
the dark scheme, whose grounds sit at black; the light scheme's sit at white,
so its rows step down from `dim`, its inks are the darkest cells, and every
search runs the other way along L** (`Scheme`)."""
from collections.abc import Callable
from dataclasses import dataclass, replace
from enum import Enum
from math import atan2, cos, degrees, inf, radians, sin

from color import (apca, contrast, hex_from_linear, grey, hk_lightness_linear,
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


class Scheme(Enum):
    """Which end of the brightness axis the chrome sits at, the TOML table that
    holds the scheme's inputs. Every search that climbs away from the grounds
    runs from `near` toward `far`: up on a dark ground, down on a light one, as
    Material 3 takes a light scheme's roles from the dark end of the same tonal
    palettes its dark scheme takes from the light end."""
    DARK = "dark"
    LIGHT = "light"

    @property
    def near(self) -> float:
        """The L** of the end the grounds sit at."""
        return 0.0 if self is Scheme.DARK else 100.0

    @property
    def far(self) -> float:
        """The L** of the end the inks climb toward."""
        return 100.0 - self.near


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


def farther(a: float, b: float, far: float) -> float:
    """Whichever of L** `a` and `b` sits nearer `far`."""
    return min(a, b, key=lambda x: abs(far - x))


def summit(f: Callable[[float], float], floor: float, far: float) -> float:
    """Where `f`, with one peak, is highest between L** `floor` and `far`:
    the floor itself when `f` already falls from it toward `far`."""
    step = SOLVED if far > floor else -SOLVED
    if f(floor + step) <= f(floor):
        return floor
    return peak(f, min(floor, far), max(floor, far))


@dataclass(frozen=True)
class InkSpec:
    """What an ink is solved to clear: `MIN_INK` on each of `grounds`, APCA
    Lc `lc` on `editor`, climbing from the grounds toward L** `far`."""
    grounds: list[str]
    editor: str
    lc: float
    far: float


def bright(hues: dict[str, float], dim: float, spec: InkSpec) -> float:
    """The L** of the bright row: the most chroma between the brightness
    nearest the grounds where every cell clears `MIN_INK` on every ground,
    and the far end.

    Each hue's ceiling rises to its gamut cusp and falls past it, so their
    minimum has one peak, and on the brightnesses that clear the floor the
    best is the peak or, when the peak sits on the grounds' side of the
    floor, the floor."""
    def clears(target: float) -> bool:
        cells = row(hues, target, line_at(hues, target)).values()
        return all(contrast(ink, ground) >= MIN_INK
                   for ink in cells for ground in spec.grounds)

    assert clears(spec.far), (
        f"no bright row clears {MIN_INK}:1 on every ground: {spec.grounds}")
    floor = threshold(clears, spec.far, dim)
    top = summit(lambda target: line_at(hues, target), floor, spec.far)
    assert clears(top), (
        f"the bright row's chroma peaks at L** {top:.2f}, past the floor at "
        f"{floor:.2f}, yet does not clear {MIN_INK}:1 there")
    return top


def light(hues: dict[str, float], syntax: dict[str, float], lo: float,
          hi: float, ground: str, lc: float) -> float:
    """The L** of the light row: the brightness between `lo` and `hi` nearest
    `lo` where every cell clears APCA Lc `lc` on `ground`. The chroma line comes
    from the `syntax` hues, as on every row."""
    def clears(target: float) -> bool:
        cells = row(hues, target, line_at(syntax, target)).values()
        return all(abs(apca(ink, ground)) >= lc for ink in cells)

    assert clears(hi), f"no light row under L** {hi:.2f} clears Lc {lc}"
    return threshold(clears, hi, lo)


def ink_floor(hue: float, lo: float, spec: InkSpec) -> float:
    """The L** nearest `lo`, between it and the far end, where `hue`, at its
    own ceiling, clears `MIN_INK` on every ground and APCA Lc `lc` on
    `editor`. Less chroma at the same L** sits further from the grounds in
    luminance, so a cell cut to a line clears there too."""
    def clears(target: float) -> bool:
        ink = cell(hue, target, inf)
        return (all(contrast(ink, ground) >= MIN_INK
                    for ground in spec.grounds)
                and abs(apca(ink, spec.editor)) >= spec.lc)

    assert clears(spec.far), (
        f"hue {hue:.1f} clears {MIN_INK}:1 and Lc {spec.lc} nowhere: "
        f"{spec.grounds}")
    return threshold(clears, spec.far, lo)


@dataclass
class Reach:
    """Where each ink's floor sits, where it holds the most chroma at or
    above it, and the line `ROW_SPREAD` above the weakest of those bests."""
    floors: dict[str, float]
    bests: dict[str, float]
    line: float


def reach(hues: dict[str, float], lo: float, spec: InkSpec) -> Reach:
    floors = {name: ink_floor(hue, lo, spec) for name, hue in hues.items()}
    bests = {name: summit(lambda target, hue=hue: ceiling(hue, target),
                          floors[name], spec.far)
             for name, hue in hues.items()}
    line = min(ceiling(hues[name], best)
               for name, best in bests.items()) + ROW_SPREAD
    return Reach(floors, bests, line)


@dataclass
class Inks:
    """Each syntax hue's ink, and the chroma line they all sit under."""
    cells: dict[str, str]
    line: float


def inks(hues: dict[str, float], lo: float, spec: InkSpec) -> Inks:
    """Each hue's ink, under one chroma line.

    Where an ink sits comes from the plain `MIN_INK` floor: a hue that holds
    that floor's line over a band of brightness sits in the middle of the
    band, and any other sits at its best. Then the APCA floor `lc` moves any
    ink short of it out to it, and the line drops to what the weakest ink
    holds there. So on a dark scheme the floor brightens the dark inks, red,
    orange and blue, and costs every ink the same chroma, while green and
    yellow keep the brightness where each reads as itself."""
    plain = reach(hues, lo, replace(spec, lc=0.0))
    full = reach(hues, lo, spec)
    out = {}
    for name, hue in hues.items():
        def holds(target: float, hue: float = hue) -> bool:
            return ceiling(hue, target) >= plain.line

        floor, best = plain.floors[name], plain.bests[name]
        if holds(best):
            low = floor if holds(floor) else threshold(holds, best, floor)
            middle = (low + threshold(holds, best, spec.far)) / 2
            target = farther(middle, full.floors[name], spec.far)
        else:
            target = full.bests[name]
        out[name] = cell(hue, target, full.line)
        assert (all(contrast(out[name], ground) >= MIN_INK
                    for ground in spec.grounds)
                and abs(apca(out[name], spec.editor)) >= spec.lc), (
            f"{name}'s ink at L** {target:.2f} does not clear {MIN_INK}:1 "
            f"and Lc {spec.lc}")
    return Inks(out, full.line)


def selection(hue: float, drawn: list[str], scheme: Scheme) -> str:
    """The fill at `hue` furthest from the grounds on which every ink clears
    `MIN_INK`: the lightest on a dark scheme, the darkest on a light one.

    Further from the grounds reads more clearly as a selection, and every
    ink drawn over it loses contrast as it nears them, so the bisection lands
    where the weakest ink meets the floor."""
    def clears(target: float) -> bool:
        ground = cell(hue, target, inf)
        return all(contrast(ink, ground) >= MIN_INK for ink in drawn)

    assert clears(scheme.near), (
        f"an ink does not clear {MIN_INK}:1 even at the grounds' end: "
        f"{drawn}")
    return cell(hue, threshold(clears, scheme.near, scheme.far), inf)


def neutrals(ladder: dict[str, float], scheme: Scheme) -> dict[str, str]:
    """`black`, `white`, and the greys in between, nearest the grounds first.

    Five rungs step from `floor` by `step` away from the grounds' end, then
    `text_muted` and `text` sit beyond them. All in Oklab lightness, which
    for a neutral is the cube root of its linear value, so a rung's luminance
    is its lightness cubed."""
    sign = 1 if scheme is Scheme.DARK else -1
    lights = [ladder["floor"] + sign * i * ladder["step"] for i in range(5)]
    lights += [ladder["text_muted"], ladder["text"]]
    climb = lights if scheme is Scheme.DARK else lights[::-1]
    assert climb == sorted(set(climb)) and 0 < climb[0] and climb[-1] <= 1, (
        f"the grey ladder is not a strict walk away from the {scheme.value} "
        f"grounds' end: {lights}")
    out = {"black": "#000000"}
    out.update({f"gray_{i + 1}": grey(light ** 3)
                for i, light in enumerate(lights)})
    out["white"] = "#ffffff"
    return out


@dataclass(frozen=True)
class Row:
    """A tint row as the grid draws it: the L** its cells land on, and the
    chroma line they stop at."""
    target: float
    line: float


@dataclass
class Grid:
    """The primitives, with what solved them: each base hue's angle, and each
    tint row, so a target can solve a hue the grid has no column for as one
    of the row's cells, with `cell`. `bright` is the row the terminal hues
    sit on, under the inks' line, as the syntax hues' inks are solved alone."""
    cells: dict[str, str]
    hues: dict[str, float]
    rows: dict[str, Row]


@dataclass(frozen=True)
class Inputs:
    """Everything one scheme's grid is solved from, each a primitive's name
    where it names a color.

    `dim` is the one tint set. `bright` is solved to clear `MIN_INK` on each
    of `grounds`, primitives named off the solved rows, and `normal` is the
    midpoint of the two. `light` is the row between `normal` and `bright`
    nearest `normal` where every cell clears APCA Lc `terminal_lc` on
    `terminal_on`. A row's chroma line comes from every hue but the
    `terminal` ones, which sit on the row under that line. The syntax hues'
    bright cells are their inks, each solved alone, and each clears APCA Lc
    `lc` on `editor`, a ground among `grounds`. `selection` is the one
    primitive off the grid: a fill of the base hue `selection_hue`, solved
    from the primitives `selection_inks` drawn over it. `scheme` says which
    end of the brightness axis the grounds sit at."""
    base: dict[str, str]
    dim: float
    ladder: dict[str, float]
    grounds: list[str]
    editor: str
    lc: float
    terminal_lc: float
    terminal_on: str
    terminal: list[str]
    selection_hue: str
    selection_inks: list[str]
    scheme: Scheme


def primitives(inputs: Inputs) -> Grid:
    """Every primitive the semantic layer can name, and the rows behind them:
    see `Inputs` for what solves each."""
    base, dim, terminal = inputs.base, inputs.dim, inputs.terminal
    hues = {name: hue_of(hex6) for name, hex6 in base.items()}
    unknown = [name for name in terminal if name not in hues]
    assert not unknown, f"not a base hue: {unknown}"
    syntax = {name: hue for name, hue in hues.items() if name not in terminal}
    out = neutrals(inputs.ladder, inputs.scheme)
    rows: dict[str, Row] = {}

    def put(names: dict[str, float], tint: str, at: Row) -> None:
        rows[tint] = at
        out.update({f"{name}_{tint}": hex6
                    for name, hex6 in row(names, at.target, at.line).items()})

    put(hues, "dim", Row(dim, line_at(syntax, dim)))
    missing = [name for name in inputs.grounds if name not in out]
    assert not missing, (
        f"an ink ground is not a primitive off the solved rows: "
        f"{missing}")
    spec = InkSpec([out[name] for name in inputs.grounds],
                   out[inputs.editor], inputs.lc, inputs.scheme.far)
    top = bright(syntax, dim, spec)
    ink = inks(syntax, dim, spec)
    out.update({f"{name}_bright": hex6 for name, hex6 in ink.cells.items()})
    put({name: hues[name] for name in terminal}, "bright",
        Row(top, min(line_at(syntax, top), ink.line)))
    middle = (dim + top) / 2
    put(hues, "normal", Row(middle, line_at(syntax, middle)))
    lit = light(hues, syntax, middle, top, out[inputs.terminal_on],
                inputs.terminal_lc)
    put(hues, "light", Row(lit, line_at(syntax, lit)))
    missing = [name for name in inputs.selection_inks if name not in out]
    assert not missing, f"a selection ink is not a grid primitive: {missing}"
    out["selection"] = selection(hues[inputs.selection_hue],
                                 [out[name] for name in inputs.selection_inks],
                                 inputs.scheme)
    return Grid(out, hues, rows)
