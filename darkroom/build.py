#!/usr/bin/env python3
"""Read ../ayu-graphite.toml and emit darkroom's two palettes,
./ayu-graphite-dark.ron and ./ayu-graphite-light.ron, one per scheme.

darkroom is a node-graph image editor. It names one colour per role it paints
with — the ground a graph is drawn on, a node's body and the band across its
head, the run status that head reports, the hue a wire takes from the type
flowing along it — and assembles its whole theme from the table this writes.
Sizes are not here: a port's radius and a card's corner are facts about that
interface, not about a palette.

Four things happen on the way out that a plain role lookup does not cover.

The surface ladder starts one rung out. darkroom stacks five surfaces in one
view — the graph ground, the surround that frames it, a node body, a hovered
control, a pressed control — and the graph ground has no step of the
palette's neutral ramp to take: it sits one step past `bg` toward the
grounds' end, below it on the dark scheme and above it on the light one,
because a tab that is open takes the graph's ground and has to stand apart
from the surround its strip sits on. It is placed one ramp step from `bg`
rather than added to the palette, because nothing else needs it, and the step
is measured off the five greys instead of assumed. The light scheme lifts a
node off that ground as white cards lift off a grey canvas in Fluent, macOS
and FigJam, so its ladder is not one walk: see LADDER.

Nothing here says what a port looks like under the pointer. Every port role
below is a resting colour, and all of them sit on `bright`, which is the far
end of the grid — there is no tint past it to lift into. darkroom lifts a port
by blending toward `lift`, the neutral at that far end, white on the dark
scheme and black on the light one, which is what it already does for a port
coloured by its type, so the two lift the same way and neither one is a colour
this file could have named.

The accent is palantir's dark lime on the dark scheme. It clears 1.1:1 on
white, so the light scheme keeps its hue and solves the brightness as an ink's:
see ACCENT.

Twelve wires want more hues than the grid has columns. Five named types take
inks of the grid; float and the six ramp slots take the hues halfway between
neighbouring base hues, each solved on a row that reads on a node's body as
one of the row's cells is, so no input is added and a moved base hue moves them too.
`check` holds every wire apart from the others and readable on a node's body.
On the head, a badge may sit beside any status, so no badge shares a colour
with a status, and the mark that says what kind of node it is takes the text
white.
"""
import dataclasses
from dataclasses import dataclass
import os
import sys
from math import dist, inf

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import color
import emit
import grid
from palette import Palette, Scheme, Source, load_source

# darkroom role -> the semantic role it is taken from.
ROLE = {
    # Surround. `surround_bg` takes `bg` and the graph ground goes below it:
    # see DERIVED.
    "surround_bg": "bg",
    "node_bg": "elem",
    "element_mid": "elem_hover",
    "element_strong": "elem_active",
    "canvas_dot": "border",
    # Ink. `port_label` keeps its own slot rather than reading `text_muted`
    # at the call site: a port row wants one strong element, and which ink
    # de-emphasizes the other two is the interface's decision to change.
    "text": "text",
    "text_muted": "text_muted",
    "port_label": "text_muted",
    # The info status keeps Ayu's blue, which the path wire shares; the accent
    # is palantir's (see LITERAL).
    "status_info": "accent",
    # Alarm. A cut wire, the scribble that cut it and a failed run are one
    # red on purpose — the editor has one way of saying stop.
    "wire_broken": "error",
    "breaker_stroke": "error",
    "status_error": "error",
    "badge_cache": "warning",
    "status_success": "success",
    "status_warning": "syn_keyword",
    # The mark a node's head wears to say what kind of node it is — a sink,
    # which runs for its effect, or one recomputed every run. A kind is not a
    # status, and every hue on the head is a status or another badge, so this
    # is the title's own white: a glyph beside the title, not a word in it.
    "badge_kind": "text",
    # Busy is the status with no colour of its own — nothing about work in
    # progress is red or green — and the one hue left, yellow, is
    # `badge_cache` on the same head. So busy is grey: no verdict yet.
    "status_busy": "text_muted",
    # Ports that carry no type: an untyped input, and an event. Neither is a
    # value of a type, so neither takes a hue a type or a status spends. An
    # event is a flow and takes the text white, as Unreal draws its
    # execution pins; an untyped input takes the muted grey, which darkroom
    # draws as a hollow ring, telling "any type" by shape as Blender 5 tells
    # a socket's structure.
    "input_port": "text_muted",
    "event_port": "text",
}

# One rung the ramp does not have. The value is the ramp's own step from
# `bg` toward the grounds' end, measured rather than assumed — see the module
# docstring.
DERIVED = {"canvas_bg": "bg"}
# Which side of `bg` that step lands on, as the table's notes say it.
SIDE = {Scheme.DARK: "below", Scheme.LIGHT: "above"}

# Roles that are a palette colour at less than full alpha, per scheme.
ALPHA = {
    # A near-black ground takes a lot of shadow before a shadow registers
    # at all, and a light one very little: Fluent's light `shadow16` key is
    # black at 14 % (https://fluent2.microsoft.design/elevation), as
    # palantir's light palette casts. This is the one role whose alpha is the
    # whole point of it.
    "shadow": ("overlay_black", {Scheme.DARK: 0x80, Scheme.LIGHT: 0x24}),
}

# The neutral a hover blends a port toward: the far end of the grid, past
# every ink — see the module docstring.
LIFT = {Scheme.DARK: "white", Scheme.LIGHT: "black"}

# palantir's dark accent, which darkroom's widgets share. The dark scheme
# takes it as it is. The light scheme keeps its Oklab hue and sits where an
# ink of the grid would, solved as `grid.inks` places one: the most chroma
# from the brightness nearest the grounds where it clears 4.5:1 on each
# surface it is drawn on, as a link's text and a focus ring are, and the
# [ink] APCA floor on a node's body. Material keeps a scheme's primary hue and
# moves its tone the same way
# (https://m3.material.io/styles/color/roles).
ACCENT = "#d1ff02"
ACCENT_ON = ("canvas_bg", "surround_bg", "node_bg", "element_mid")

# Roles that are a palette colour at an alpha over a surface, written opaque.
COMPOSITE = {
    # A disabled row's ink, well under the muted one a menu's shortcut hint
    # is written in: the palette gives both one grey, so a menu whose rows
    # were all disabled read as live. The text ink at Fluent's
    # `TextFillColorDisabled` alpha (0x5D on white) over the menu's surface,
    # blended in encoded sRGB as Windows composes it. Opaque, because
    # darkroom blends in linear light, where the same alpha lands a step from
    # the muted grey. WCAG 2.2 SC 1.4.3 exempts an inactive control's text
    # from contrast.
    "text_disabled": ("text", 0x5D, "node_bg"),
}

# Accent. One hue for the whole selection: the rubber band that sweeps nodes
# up and the halo left on the ones it caught. A link, and the inspect button
# that opens the node's inspector, take it as well. See ACCENT.
ACCENT_ROLES = ("accent", "link")

# Roles that are not a palette colour, the same in every scheme. A card
# resting on its ground draws no outline: the shadow carries the edge, and
# the stroke is kept for the three things that claim it — selected,
# breaking, missing.
LITERAL = {
    "node_border": "#00000000",
    # The checker behind a transparent image is a transparency reference, not
    # a surface: two mid greys any image's colours read against, the same in
    # every theme, as image editors draw it.
    "checker_light": "#4d4d4d",
    "checker_dark": "#333333",
}

# A wire's hue is the type flowing along it. Six types are named; the rest
# are keyed onto the ramp by their type id. Five take an ink of the grid, and
# float takes a hue between two (see FLOAT).
TYPE = {
    "boolean": "error",
    "int": "ansi_bright_yellow",
    "string": "syn_string",
    # `path` is a reference, so it takes the blue the interface links with.
    "path": "hint",
    # The dominant payload on this canvas earns a deliberate colour rather
    # than a hash pick: the one warm ink no named type spends.
    "image": "syn_keyword",
}
# The grid's cells that read on a dark scheme's node body are its bright and
# `light` rows, and of those two cells of one hue sit closer than a wire's floor, or
# miss a port's contrast: ten readable wires, two short of the named six and a
# ramp of six. So float and the ramp take the hues halfway between each pair
# of neighbouring base hues, seven, solved as cells of a row: no input is
# added, and a base hue that moves takes them along.
#
# Float sits between int's yellow and string's green, so the two numbers are
# a family told apart by hue, as a 2px wire cannot show a tint step. The
# ramp is the other six, in hue order from red.
FLOAT = ("yellow", "green")
# The type table's fields, in the order the file writes them.
FIELDS = ("boolean", "int", "float", "string", "path", "image")
# The ramp darkroom reads, a fixed-size array there.
RAMP_LEN = 6
# The rows a wire may sit on: every row, of which `readable` keeps those that
# read on a node's body — the bright and `light` rows on the dark scheme,
# where `normal` and `dim` are too dark, and the rows past `dim` on the light
# one. Each in-between hue takes the one, of those it reads on, that puts it
# farthest from the nearest named wire.
WIRE_ROWS = ("bright", "light", "normal", "dim")

# Two wire hues closer than this in OKLab are one colour on a 2px line. The
# floor is what the wires actually achieve, less a margin — it catches a
# collapse without firing on drift.
WIRE_FLOOR = 0.07

# What a port's circle and its wire must clear against a node's body to be
# seen at all: the WCAG 2.2 ratio for a graphic a user needs (SC 1.4.11,
# Non-text Contrast), and the APCA Lc the `light` row holds as ink on bg.
PORT_CONTRAST = 3.0
PORT_APCA = 40.0

# The surfaces that meet in one view, as (darker, lighter) pairs. Each must
# be darker than its partner by MIN_LAYER, or a control disappears into its
# ground. The dark scheme is one climb, ground to press. The light scheme
# lifts a node off its ground as a white card, and steps hover and press
# down past both grounds, as palantir rests a field and a button on the hover
# fill over the ground and the surround: the ground takes the lighter of the
# ground and the surround, as on the dark scheme it takes the darker, so an
# open tab stands apart from its strip either way.
LADDER = {
    Scheme.DARK: (("canvas_bg", "surround_bg"), ("surround_bg", "node_bg"),
                  ("node_bg", "element_mid"),
                  ("element_mid", "element_strong")),
    Scheme.LIGHT: (("surround_bg", "canvas_bg"), ("canvas_bg", "node_bg"),
                   ("element_mid", "surround_bg"),
                   ("element_strong", "element_mid")),
}
# WCAG contrast: about one step of the neutral ramp, as tools/audit.py holds
# the palette's own layers.
MIN_LAYER = 1.10

SURFACE_GREYS = ("gray_1", "gray_2", "gray_3", "gray_4", "gray_5")

# The order the table is written in, and the headings it is written under.
SECTIONS = (
    ("Surfaces — what the editor is built out of, and the inks on them.", (
        "canvas_bg", "canvas_dot", "surround_bg", "node_bg",
        "node_border", "shadow", "text", "text_muted", "text_disabled",
        "element_mid", "element_strong")),
    ("Graph — the wires, and the marks drawn over them, and the neutral a\n"
     "hovered port blends toward.", (
        "accent", "wire_broken", "breaker_stroke", "lift")),
    ("Viewer — the checker behind a transparent image.", (
        "checker_light", "checker_dark")),
    ("Ports — an untyped port's circle, and the ink beside it. A typed port\n"
     "takes its hue from the type table instead.", (
        "input_port", "event_port", "port_label")),
    ("Badges — what a node's head says about itself.", (
        "link", "badge_cache", "badge_kind")),
    ("Status — what a node's head says about its last run.", (
        "status_success", "status_info", "status_busy", "status_warning",
        "status_error")),
)


def ramp_step(primitives: dict[str, str]) -> float:
    """The mean Oklab lightness between adjacent surface greys, unsigned.

    Measured off the palette rather than written down here, so the rung this
    file adds keeps the ramp's spacing when the ramp is respaced.
    """
    lights = [color.oklab(primitives[name])[0] for name in SURFACE_GREYS]
    return abs(lights[-1] - lights[0]) / (len(lights) - 1)


@dataclass(frozen=True)
class Between:
    """A wire hue halfway between the neighbouring base hues `left` and
    `right`, solved as a cell of the tint row `row`."""
    left: str
    right: str
    row: str
    hexstr: str


def neighbours(hues: dict[str, float]) -> list[tuple[str, str, float]]:
    """Each pair of neighbouring base hues around the wheel, from the lowest
    angle, with the angle halfway between them."""
    order = sorted(hues, key=hues.__getitem__)
    out = []
    for left, right in zip(order, order[1:] + order[:1]):
        span = (hues[right] - hues[left]) % 360
        out.append((left, right, (hues[left] + span / 2) % 360))
    return out


def readable(hexstr: str, body: str) -> bool:
    """Whether a port of `hexstr` is seen on a node's `body`: see `check`."""
    return (color.contrast(hexstr, body) >= PORT_CONTRAST
            and abs(color.apca(hexstr, body)) >= PORT_APCA)


def betweens(src: Source, named: dict[str, str], body: str) -> list[Between]:
    """Each hue between two neighbouring base hues, on the row of WIRE_ROWS it
    reads on that puts it farthest from the nearest of the `named` wires."""
    named_points = [color.oklab(hexstr) for hexstr in named.values()]

    def clearance(hexstr: str) -> float:
        point = color.oklab(hexstr)
        return min(dist(point, other) for other in named_points)

    out = []
    for left, right, angle in neighbours(src.hues):
        cells = {row: grid.cell(angle, src.rows[row].target, src.rows[row].line)
                 for row in WIRE_ROWS}
        seen = {row: hexstr for row, hexstr in cells.items()
                if readable(hexstr, body)}
        assert seen, (
            f"the hue between {left} and {right} reads on no row of "
            f"{WIRE_ROWS}: {cells}")
        row = max(seen, key=lambda name: clearance(seen[name]))
        out.append(Between(left, right, row, seen[row]))
    return out


def accent(src: Source, values: dict) -> str:
    """The accent of `src`'s scheme: see ACCENT."""
    if src.scheme is Scheme.DARK:
        return ACCENT
    hue = grid.hue_of(ACCENT)
    spec = grid.InkSpec([values[role] for role in ACCENT_ON],
                        values["node_bg"], src.ink_lc, src.scheme.far)
    floor = grid.ink_floor(hue, src.scheme.near, spec)
    best = grid.summit(lambda target: grid.ceiling(hue, target), floor,
                       src.scheme.far)
    return grid.cell(hue, best, inf)


def resolve(src: Source, float_wire: Between, ramp: list[Between]) -> dict:
    """Every darkroom role, as a hex string, plus the nested type table."""
    roles = src.palette.as_dict()
    values = {role: roles[key] for role, key in ROLE.items()}
    values.update(LITERAL)
    for role, (key, alphas) in ALPHA.items():
        values[role] = f"{roles[key]}{alphas[src.scheme]:02x}"
    values["lift"] = src.primitives[LIFT[src.scheme]]

    for role, (key, alpha, ground) in COMPOSITE.items():
        values[role] = over(roles[key], alpha, values[ground])

    # Toward the grounds' end: down on the dark scheme, up on the light one.
    step = ramp_step(src.primitives) * (-1 if src.scheme is Scheme.DARK else 1)
    for role, key in DERIVED.items():
        # A neutral's three channels are equal, so its Oklab lightness is the
        # cube root of its linear value and the step inverts in one line.
        lightness = color.oklab(roles[key])[0] + step
        assert 0 < lightness <= 1, (
            f"{role}, one ramp step from {key}, falls off the axis at Oklab "
            f"lightness {lightness:.3f}")
        values[role] = color.grey(lightness ** 3)

    shared = accent(src, values)
    values.update({role: shared for role in ACCENT_ROLES})

    named = {field: roles[key] for field, key in TYPE.items()}
    values["type_colors"] = {field: named.get(field, float_wire.hexstr)
                             for field in FIELDS}
    values["type_colors"]["ramp"] = [wire.hexstr for wire in ramp]
    return values


def over(ink: str, alpha: int, ground: str) -> str:
    """`ink` at `alpha` (of 255) over `ground`, blended in encoded sRGB."""
    a = alpha / 255
    mixed = [a * f + (1 - a) * g
             for f, g in zip(color.channels(ink), color.channels(ground))]
    return "#" + "".join(f"{round(c * 255):02x}" for c in mixed)


def check(values: dict, scheme: Scheme) -> None:
    """The five things a palette edit could quietly break here.

    Each is a rule darkroom's own drawing depends on and cannot state: the
    file it reads is a table of colours, and a table cannot say that two of
    its entries have to differ.
    """
    for lower, upper in LADDER[scheme]:
        under, over_ = values[lower], values[upper]
        assert color.luminance(under) < color.luminance(over_), (
            f"{lower} ({under}) is not darker than {upper} ({over_}) — a "
            f"surface that stacks on it disappears")
        ratio = color.contrast(under, over_)
        assert ratio >= MIN_LAYER, (
            f"{lower} ({under}) and {upper} ({over_}) are {ratio:.3f}:1 — "
            f"under {MIN_LAYER}:1, one surface reads as the other")

    # The accent is a link's text and a focus ring on every surface it meets.
    for ground in ACCENT_ON:
        ratio = color.contrast(values["accent"], values[ground])
        assert ratio >= grid.MIN_INK, (
            f"the accent ({values['accent']}) is {ratio:.2f}:1 on {ground} "
            f"({values[ground]}) — under {grid.MIN_INK}:1, a link goes unread")

    wires = dict(values["type_colors"])
    ramp = wires.pop("ramp")
    wires.update({f"ramp[{i}]": hexstr for i, hexstr in enumerate(ramp)})
    points = {name: color.oklab(hexstr) for name, hexstr in wires.items()}
    names = sorted(wires)
    for i, one in enumerate(names):
        for other in names[i + 1:]:
            gap = dist(points[one], points[other])
            assert gap >= WIRE_FLOOR, (
                f"the {one} and {other} wires are {gap:.3f} apart in OKLab "
                f"({wires[one]}, {wires[other]}) — under {WIRE_FLOOR}, a 2px "
                f"line reads as one colour")

    body = values["node_bg"]
    ports = dict(wires, input_port=values["input_port"],
                 event_port=values["event_port"])
    for name, hexstr in sorted(ports.items()):
        ratio = color.contrast(hexstr, body)
        assert ratio >= PORT_CONTRAST, (
            f"the {name} port ({hexstr}) is {ratio:.2f}:1 on a node's body "
            f"({body}) — under {PORT_CONTRAST}:1, it goes unseen")
        lc = abs(color.apca(hexstr, body))
        assert lc >= PORT_APCA, (
            f"the {name} port ({hexstr}) is Lc {lc:.1f} on a node's body "
            f"({body}) — under Lc {PORT_APCA}, it goes unseen")

    # A disabled row must read dimmer than a live row's shortcut hint on the
    # menu it sits in, a node's body.
    disabled, muted = values["text_disabled"], values["text_muted"]
    assert color.contrast(disabled, body) < color.contrast(muted, body), (
        f"a disabled row ({disabled} on {body}) reads as strong as a "
        f"shortcut hint ({muted}) — the menu cannot say which rows are live")


def entries(values: dict, semantic: dict[str, str],
            scheme: Scheme) -> dict[str, emit.RonEntry]:
    """Every flat role, with the two columns of provenance behind it."""
    def entry(role, key, note):
        return emit.RonEntry(role, values[role], key, note)

    out = {role: entry(role, key, semantic[key]) for role, key in ROLE.items()}
    out.update({role: entry(role, key, f"{semantic[key]} at "
                            f"{alphas[scheme]:#04x}")
                for role, (key, alphas) in ALPHA.items()})
    out.update({role: entry(role, key,
                            f"{semantic[key]} at {alpha:#04x} over {ground}")
                for role, (key, alpha, ground) in COMPOSITE.items()})
    side = SIDE[scheme]
    out.update({role: entry(role, "(the ramp's step)",
                            f"{side} {semantic[key]}")
                for role, key in DERIVED.items()})
    literal_notes = {
        "node_border": ("(no outline)", "the shadow carries the edge"),
        "checker_light": ("(fixed)", "a transparency reference"),
        "checker_dark": ("(fixed)", "a transparency reference"),
    }
    out.update({role: entry(role, *literal_notes[role]) for role in LITERAL})
    accent_note = {
        Scheme.DARK: ("(fixed)", "palantir's dark accent"),
        Scheme.LIGHT: ("(solved)", "its hue, placed as an ink"),
    }[scheme]
    out.update({role: entry(role, *accent_note) for role in ACCENT_ROLES})
    out["lift"] = entry("lift", "(the far end)", LIFT[scheme])

    # A role left out of SECTIONS would be dropped from the file, and darkroom
    # would report it as a field its table is missing — true, and a long way
    # from the line that caused it.
    written = {role for _, roles in SECTIONS for role in roles}
    assert written == set(out), (
        f"SECTIONS and the roles disagree: {written ^ set(out)}")
    return out


def build_darkroom(src: Source) -> str:
    palette, semantic = src.palette, src.semantic
    roles = palette.as_dict()
    named = {field: roles[key] for field, key in TYPE.items()}
    wires = betweens(src, named, roles[ROLE["node_bg"]])
    float_wire = next(wire for wire in wires if (wire.left, wire.right) == FLOAT)
    ramp = [wire for wire in wires if wire is not float_wire]
    assert len(ramp) == RAMP_LEN, (
        f"{len(ramp)} hues for the ramp, which darkroom reads as {RAMP_LEN}: "
        f"a base hue more or fewer changes darkroom's `TypeColors::ramp` too")
    values = resolve(src, float_wire, ramp)
    check(values, src.scheme)
    table = entries(values, semantic, src.scheme)

    def between_entry(field: str, wire: Between) -> emit.RonEntry:
        return emit.RonEntry(field, wire.hexstr,
                             f"(between {wire.left} and {wire.right})",
                             f"{wire.row} row")

    type_entries = [between_entry(field, float_wire) if field == "float"
                    else emit.RonEntry(field, named[field], TYPE[field],
                                       semantic[TYPE[field]])
                    for field in FIELDS]
    ramp_entries = [between_entry("", wire) for wire in ramp]
    # Measured over the type table too, so a long role there keeps its
    # comment column.
    columns = emit.RonColumns.of([*table.values(), *type_entries, *ramp_entries])

    side = SIDE[src.scheme]
    lines = [
        f"// Ayu Graphite {src.scheme.value}, for darkroom — generated. Do not "
        "edit by hand.",
        "//",
        "// Source:    ayu-graphite.toml",
        "// Generator: ayu-graphite/darkroom/build.py",
        "//",
        "// Each entry names a role darkroom paints with, the role here it is",
        "// taken from, and the primitive that resolves to. Every color is a",
        "// resting one: a port lifts under the pointer by blending toward",
        "// `lift`, because the palette's far tint has nothing past it.",
        "//",
        "// The graph ground is the one color with no step of its own. darkroom",
        "// stacks five surfaces and starts them one rung out from the neutral",
        f"// ramp, so the ground is placed one of that ramp's own steps {side} "
        "`bg`.",
        "(",
    ]
    for heading, roles in SECTIONS:
        lines.extend(f"    // {line}" for line in heading.split("\n"))
        lines += [columns.row(table[role]) for role in roles]
        lines.append("")

    lines.append("    // A wire's hue is the type flowing along it. `ramp` backs the")
    lines.append("    // open-ended custom and enum families, keyed by type id.")
    lines.append("    type_colors: (")
    # The nested block keeps the table's value and comment columns; only its
    # names are narrower.
    nested = dataclasses.replace(
        columns, name=max(len(field) for field in FIELDS) + 2)
    lines += [nested.row(entry, indent=8) for entry in type_entries]
    # A RON tuple, not a list: `ramp` is a fixed-size array on the other side,
    # and serde reads one of those as a tuple.
    lines.append("        ramp: (")
    lines += [nested.row(entry, indent=12) for entry in ramp_entries]
    lines.append("        ),")
    lines.append("    ),")
    lines.append(")")
    return "\n".join(lines) + "\n"


def main() -> None:
    for scheme in Scheme:
        emit.write_text(emit.beside(__file__, f"ayu-graphite-{scheme.value}.ron"),
                        build_darkroom(load_source(scheme)))


if __name__ == "__main__":
    main()
