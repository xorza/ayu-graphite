#!/usr/bin/env python3
"""Read ../ayu-graphite.toml and emit ./ayu-graphite.ron (darkroom's palette).

darkroom is a node-graph image editor. It names one colour per role it paints
with — the ground a graph is drawn on, a node's body and the band across its
head, the run status that head reports, the hue a wire takes from the type
flowing along it — and assembles its whole theme from the table this writes.
Sizes are not here: a port's radius and a card's corner are facts about that
interface, not about a palette.

Three things happen on the way out that a plain role lookup does not cover.

The surface ladder starts one rung low. darkroom stacks five surfaces in one
view — the graph ground, the surround that frames it, a node body, a hovered
control, a pressed control — and the graph ground has no step of the
palette's neutral ramp to take: it sits below `bg`, because a tab that is open
reads as continuous with the graph, so the surround has to be the lighter of
the two. It is placed one ramp step
below `bg` rather than added to the palette, because nothing else needs it,
and the step is measured off the five greys instead of assumed.

Nothing here says what a port looks like under the pointer. Every port role
below is a resting colour, and all of them sit on `bright`, which is the top
of the grid — there is no tint above it to lift into. darkroom lifts a port by
blending toward white at the call site, which is what it already does for a
port coloured by its type, so the two now lift the same way and neither one is
a colour this file could have named.

Five inks have to serve nine wires and the marks on a node's head. The wires
take the bright row and the `light` row, and `check` holds them apart from
each other and readable on a node's body. On the head, a badge may sit beside
any status, so no badge shares a colour with a status, and the mark that
says what kind of node it is takes the text white.
"""
import dataclasses
import os
import sys
from math import dist

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import color
import emit
from palette import Palette, load_source

# darkroom role -> the semantic role it is taken from.
ROLE = {
    # Surround. `surround_fill` takes `bg` and the graph ground goes below it:
    # see DERIVED.
    "surround_fill": "bg",
    "node_fill": "elem",
    "elem_hover": "elem_hover",
    "header_fill": "elem_active",
    "elem_active": "elem_active",
    "canvas_dot": "border",
    "border_focused": "border_focused",
    # Ink. `port_label` keeps its own slot rather than reading `text_muted`
    # at the call site: a port row wants one strong element, and which ink
    # de-emphasizes the other two is the interface's decision to change.
    "text": "text",
    "text_muted": "text_muted",
    "port_label": "text_muted",
    # Accent. One hue for the whole selection: the rubber band that sweeps
    # nodes up and the halo left on the ones it caught.
    "selection_rect": "accent",
    "badge_graph": "accent",
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

# One rung the ramp does not have. The value is the ramp's own step below
# `bg`, measured rather than assumed — see the module docstring.
DERIVED = {"canvas_bg": "bg"}

# Roles that are a palette colour at less than full alpha.
ALPHA = {
    # A near-black ground takes a lot of shadow before a shadow registers
    # at all. This is the one role whose alpha is the whole point of it.
    "node_ambient_shadow": ("overlay_black", 0x80),
}

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
    "text_disabled": ("text", 0x5D, "node_fill"),
}

# Roles that are not a palette colour. A card resting on this ground draws
# no outline: the shadow carries the edge, and the stroke is kept for the
# three things that claim it — selected, breaking, missing.
LITERAL = {"node_border": "#00000000"}

# A wire's hue is the type flowing along it. Six types are named; the rest
# are keyed onto RAMP by their type id.
TYPE = {
    "boolean": "error",
    # The two numbers are one hue at two tints: a family, told apart by
    # weight. The lighter is the `light` row's, the darkest yellow that
    # still reads on a node's body.
    "int": "ansi_bright_yellow",
    "float": "ansi_yellow",
    "string": "syn_string",
    # `path` is a reference, so it takes the blue the interface links with.
    "path": "hint",
    # The dominant payload on this canvas earns a deliberate colour rather
    # than a hash pick: the one warm ink no named type spends.
    "image": "syn_keyword",
}
# The hues the named types leave free that read on a node's body: purple and
# cyan from the bright row, green from the `light` row. The `normal` row and
# the greys are refused, the first too dark on a node and the second the
# inks a port's label is written in; `light` blue misses the APCA floor, and
# `light` orange sits a step from the image wire.
RAMP = ["ansi_bright_magenta", "ansi_bright_cyan", "ansi_green"]

# Two wire hues closer than this in OKLab are one colour on a 2px line. The
# floor is what the wires actually achieve, less a margin — it catches a
# collapse without firing on drift.
WIRE_FLOOR = 0.06

# What a port's circle and its wire must clear against a node's body to be
# seen at all: the WCAG 2.2 ratio for a graphic a user needs (SC 1.4.11,
# Non-text Contrast), and the APCA Lc the `light` row holds as ink on bg.
PORT_CONTRAST = 3.0
PORT_APCA = 40.0

# The surfaces that stack in one view, darkest first. Each must be
# lighter than the one under it, or a control disappears into its ground.
LADDER = ("canvas_bg", "surround_fill", "node_fill", "elem_hover",
          "header_fill")

SURFACE_GREYS = ("gray_1", "gray_2", "gray_3", "gray_4", "gray_5")

# The order the table is written in, and the headings it is written under.
SECTIONS = (
    ("Surfaces — what the editor is built out of, and the inks on them.", (
        "canvas_bg", "canvas_dot", "surround_fill", "node_fill",
        "node_border", "header_fill", "node_ambient_shadow", "text",
        "text_muted", "text_disabled", "elem_hover", "elem_active",
        "border_focused")),
    ("Graph — the wires, and the marks drawn over them.", (
        "selection_rect", "wire_broken", "breaker_stroke")),
    ("Ports — an untyped port's circle, and the ink beside it. A typed port\n"
     "takes its hue from the type table instead.", (
        "input_port", "event_port", "port_label")),
    ("Badges — what a node's head says about itself.", (
        "badge_graph", "badge_cache", "badge_kind")),
    ("Status — what a node's head says about its last run.", (
        "status_success", "status_info", "status_busy", "status_warning",
        "status_error")),
)


def ramp_step(primitives: dict[str, str]) -> float:
    """The mean Oklab lightness between adjacent surface greys.

    Measured off the palette rather than written down here, so the rung this
    file adds keeps the ramp's spacing when the ramp is respaced.
    """
    lights = [color.oklab(primitives[name])[0] for name in SURFACE_GREYS]
    return (lights[-1] - lights[0]) / (len(lights) - 1)


def resolve(palette: Palette, primitives: dict[str, str]) -> dict:
    """Every darkroom role, as a hex string, plus the nested type table."""
    roles = palette.as_dict()
    values = {role: roles[key] for role, key in ROLE.items()}
    values.update(LITERAL)
    for role, (key, alpha) in ALPHA.items():
        values[role] = f"{roles[key]}{alpha:02x}"

    for role, (key, alpha, ground) in COMPOSITE.items():
        values[role] = over(roles[key], alpha, values[ground])

    step = ramp_step(primitives)
    for role, key in DERIVED.items():
        # A neutral's three channels are equal, so its Oklab lightness is the
        # cube root of its linear value and the step inverts in one line.
        values[role] = color.grey((color.oklab(roles[key])[0] - step) ** 3)

    values["type_colors"] = {field: roles[key] for field, key in TYPE.items()}
    values["type_colors"]["ramp"] = [roles[key] for key in RAMP]
    return values


def over(ink: str, alpha: int, ground: str) -> str:
    """`ink` at `alpha` (of 255) over `ground`, blended in encoded sRGB."""
    a = alpha / 255
    mixed = [a * f + (1 - a) * g
             for f, g in zip(color.channels(ink), color.channels(ground))]
    return "#" + "".join(f"{round(c * 255):02x}" for c in mixed)


def check(values: dict) -> None:
    """The four things a palette edit could quietly break here.

    Each is a rule darkroom's own drawing depends on and cannot state: the
    file it reads is a table of colours, and a table cannot say that two of
    its entries have to differ.
    """
    lights = [color.luminance(values[role]) for role in LADDER]
    for lower, upper, under, over in zip(LADDER, LADDER[1:], lights, lights[1:]):
        assert under < over, (
            f"{lower} ({values[lower]}) is not darker than {upper} "
            f"({values[upper]}) — a surface that stacks on it disappears")

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

    body = values["node_fill"]
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


def entries(values: dict, semantic: dict[str, str]) -> dict[str, emit.RonEntry]:
    """Every flat role, with the two columns of provenance behind it."""
    def entry(role, key, note):
        return emit.RonEntry(role, values[role], key, note)

    out = {role: entry(role, key, semantic[key]) for role, key in ROLE.items()}
    out.update({role: entry(role, key, semantic[key])
                for role, (key, _) in ALPHA.items()})
    out.update({role: entry(role, key,
                            f"{semantic[key]} at {alpha:#04x} over {ground}")
                for role, (key, alpha, ground) in COMPOSITE.items()})
    out.update({role: entry(role, "(the ramp's step)", f"below {semantic[key]}")
                for role, key in DERIVED.items()})
    out.update({role: entry(role, "(no outline)", "the shadow carries the edge")
                for role in LITERAL})

    # A role left out of SECTIONS would be dropped from the file, and darkroom
    # would report it as a field its table is missing — true, and a long way
    # from the line that caused it.
    written = {role for _, roles in SECTIONS for role in roles}
    assert written == set(out), (
        f"SECTIONS and the roles disagree: {written ^ set(out)}")
    return out


def build_darkroom(palette: Palette, semantic: dict[str, str],
                   primitives: dict[str, str]) -> str:
    values = resolve(palette, primitives)
    check(values)
    table = entries(values, semantic)
    types = values["type_colors"]
    type_entries = [emit.RonEntry(field, types[field], key, semantic[key])
                    for field, key in TYPE.items()]
    ramp_entries = [emit.RonEntry("", hexstr, key, semantic[key])
                    for key, hexstr in zip(RAMP, types["ramp"])]
    # Measured over the type table too, so a long role there keeps its
    # comment column.
    columns = emit.RonColumns.of([*table.values(), *type_entries, *ramp_entries])

    lines = [
        "// Ayu Graphite, for darkroom — generated. Do not edit by hand.",
        "//",
        "// Source:    ayu-graphite.toml",
        "// Generator: ayu-graphite/darkroom/build.py",
        "//",
        "// Each entry names a role darkroom paints with, the role here it is",
        "// taken from, and the primitive that resolves to. Every color is a",
        "// resting one: a port lifts under the pointer by blending toward",
        "// white, because the palette's top tint has nothing above it.",
        "//",
        "// The graph ground is the one color with no step of its own. The",
        "// neutral ramp holds five surfaces and darkroom stacks six, so",
        "// the ground is placed one of that ramp's own steps below `bg`.",
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
        columns, name=max(len(field) for field in TYPE) + 2)
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
    src = load_source()
    emit.write_text(emit.beside(__file__, "ayu-graphite.ron"),
                    build_darkroom(src.palette, src.semantic, src.primitives))


if __name__ == "__main__":
    main()
