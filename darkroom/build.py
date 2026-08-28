#!/usr/bin/env python3
"""Read ../ayu-graphite.toml and emit ./ayu-graphite.ron (darkroom's palette).

darkroom is a node-graph image editor. It names one colour per role it paints
with — the ground a graph is drawn on, a node's body and the band across its
head, the run status that head reports, the hue a wire takes from the type
flowing along it — and assembles its whole theme from the table this writes.
Sizes are not here: a port's radius and a card's corner are facts about that
interface, not about a palette.

Three things happen on the way out that a plain role lookup does not cover.

The chrome ladder is one rung short. darkroom stacks six surfaces in one view
— the graph ground, the bar of chrome around it, an inactive tab, a node body,
a hovered control, a pressed control — and the palette's neutral ramp holds
five. The graph ground is the one that has no step to take: it sits below
`bg`, because a tab that is open reads as continuous with the graph, so the
chrome around it has to be the lighter of the two. It is placed one ramp step
below `bg` rather than added to the palette, because nothing else needs it,
and the step is measured off the five greys instead of assumed.

Nothing here says what a port looks like under the pointer. Every port role
below is a resting colour, and most of them already sit on `vivid`, which is
the top of the grid — there is no tint above it to lift into. darkroom lifts a
port by blending toward white at the call site, which is what it already does
for a port coloured by its type, so the two now lift the same way and neither
one is a colour this file could have named.

Two pairs would land on one colour. The palette reaches pink at exactly one
tint through its semantic layer, and darkroom asks for it on a node's head and
on the wire most of the canvas is; of the two yellow tints that read as ink,
one is already a badge on that head, and darkroom asks for a busy status. Both
are resolved below, on the entries they affect, against what the two roles are
for rather than by moving one of them a shade.
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
    # Chrome. `chrome_fill` takes `bg` and the graph ground goes below it:
    # see DERIVED. `tab_inactive` is the rung that stops an unselected tab
    # from reading as a bare label on the bar.
    "chrome_fill": "bg",
    "tab_inactive": "panel",
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
    "text_disabled": "text_disabled",
    # Accent. One hue for the whole selection: the rubber band that sweeps
    # nodes up and the halo left on the ones it caught.
    "selection_rect": "accent",
    "badge_graph": "accent",
    "status_info": "accent",
    # Alarm. A cut wire, the scribble that cut it, a sink and a failed run
    # are one red on purpose — the editor has one way of saying stop.
    "connection_broken": "error",
    "breaker_stroke": "error",
    "badge_sink": "error",
    "status_error": "error",
    "badge_cache": "warning",
    "status_success": "success",
    "status_warning": "syn_keyword",
    # The pink a node's head wears to say it is never cached. It shares the
    # palette's one pink with the `image` wire below, which is the pair the
    # palette can afford to collapse: a glyph on a head and a line between
    # two nodes are never the same mark.
    "badge_impure": "syn_number",
    # Busy is the status with no colour of its own — nothing about work in
    # progress is red or green — so it takes the one hue the status roster
    # does not already spend. Yellow's vivid tint is `badge_cache` on the
    # same head, so busy takes the bright one, and shares it with a ramp
    # wire on the same grounds the pink is shared.
    "status_busy": "ansi_bright_yellow",
    # Ports that carry no type. Position is what these say, so they take the
    # two hues the editor already reads as a direction, and an event takes
    # the sink marker's red because a subscription pin sits beside one.
    # Shape is what keeps an event apart from a data port, not hue.
    "input_port": "success",
    "output_port": "syn_keyword",
    "event_port": "error",
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

# Roles that are not a palette colour. A card resting on this ground draws
# no outline: the shadow carries the edge, and the stroke is kept for the
# three things that claim it — selected, breaking, missing.
LITERAL = {"node_border": "#00000000"}

# A wire's hue is the type flowing along it. Six types are named; the rest
# are keyed onto RAMP by their type id, so two custom types stay two colours
# without either one being enumerated here.
TYPE = {
    "boolean": "error",
    "int": "syn_string_regex",
    "float": "syn_type",
    "string": "syn_string",
    # `path` is a reference, so it takes the blue the chrome links with.
    "path": "hint",
    # The dominant payload on this canvas earns a deliberate colour rather
    # than a hash pick: the number pink, which `badge_impure` shares.
    "image": "syn_number",
}
RAMP = ["syn_keyword", "warning", "ansi_bright_yellow", "syn_punctuation"]

# Two wire hues closer than this in OKLab are one colour on a 2px line. The
# floor is what the ten actually achieve, less a margin — it catches a
# collapse without firing on drift.
WIRE_FLOOR = 0.06

# The chrome surfaces that stack in one view, darkest first. Each must be
# lighter than the one under it, or a control disappears into its ground.
LADDER = ("canvas_bg", "chrome_fill", "tab_inactive", "node_fill",
          "elem_hover", "header_fill")

CHROME_GREYS = ("gray_24", "gray_29", "gray_34", "gray_39", "gray_44")

# The order the table is written in, and the headings it is written under.
SECTIONS = (
    ("Chrome — the surfaces the editor is built out of, and the inks on them.", (
        "canvas_bg", "canvas_dot", "chrome_fill", "tab_inactive", "node_fill",
        "node_border", "header_fill", "node_ambient_shadow", "text",
        "text_muted", "text_disabled", "elem_hover", "elem_active",
        "border_focused")),
    ("Graph — the wires, and the marks drawn over them.", (
        "selection_rect", "connection_broken", "breaker_stroke")),
    ("Ports — an untyped port's circle, and the ink beside it. A typed port\n"
     "takes its hue from the type table instead.", (
        "input_port", "output_port", "event_port", "port_label")),
    ("Badges — what a node's head says about itself.", (
        "badge_graph", "badge_sink", "badge_cache", "badge_impure")),
    ("Status — what a node's head says about its last run.", (
        "status_success", "status_info", "status_busy", "status_warning",
        "status_error")),
)


def ramp_step(primitives: dict[str, str]) -> float:
    """The mean Oklab lightness between adjacent chrome greys.

    Measured off the palette rather than written down here, so the rung this
    file adds keeps the ramp's spacing when the ramp is respaced.
    """
    lights = [color.oklab(primitives[name])[0] for name in CHROME_GREYS]
    return (lights[-1] - lights[0]) / (len(lights) - 1)


def resolve(palette: Palette, primitives: dict[str, str]) -> dict:
    """Every darkroom role, as a hex string, plus the nested type table."""
    roles = palette.as_dict()
    values = {role: roles[key] for role, key in ROLE.items()}
    values.update(LITERAL)
    for role, (key, alpha) in ALPHA.items():
        values[role] = f"{roles[key]}{alpha:02x}"

    step = ramp_step(primitives)
    for role, key in DERIVED.items():
        # A neutral's three channels are equal, so its Oklab lightness is the
        # cube root of its linear value and the step inverts in one line.
        values[role] = color.grey((color.oklab(roles[key])[0] - step) ** 3)

    values["type_colors"] = {field: roles[key] for field, key in TYPE.items()}
    values["type_colors"]["ramp"] = [roles[key] for key in RAMP]
    return values


def check(values: dict) -> None:
    """The two things a palette edit could quietly break here.

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


def entries(values: dict, semantic: dict[str, str]) -> dict[str, emit.RonEntry]:
    """Every flat role, with the two columns of provenance behind it."""
    def entry(role, key, note):
        return emit.RonEntry(role, values[role], key, note)

    out = {role: entry(role, key, semantic[key]) for role, key in ROLE.items()}
    out.update({role: entry(role, key, semantic[key])
                for role, (key, _) in ALPHA.items()})
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
    columns = emit.RonColumns.of(table.values())

    lines = [
        "// Ayu Graphite, for darkroom — generated. Do not edit by hand.",
        "//",
        "// Source:    ayu-graphite.toml",
        "// Generator: ayu-graphite/darkroom/build.py",
        "//",
        "// Each entry names a role darkroom paints with, the role here it is",
        "// taken from, and the primitive that resolves to. Every colour is a",
        "// resting one: a port lifts under the pointer by blending toward",
        "// white, because the palette's top tint has nothing above it.",
        "//",
        "// The graph ground is the one colour with no step of its own. The",
        "// neutral ramp holds five chrome surfaces and darkroom stacks six, so",
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
    types = values["type_colors"]
    lines += [nested.row(emit.RonEntry(field, types[field], key, semantic[key]),
                         indent=8)
              for field, key in TYPE.items()]
    # A RON tuple, not a list: `ramp` is a fixed-size array on the other side,
    # and serde reads one of those as a tuple.
    lines.append("        ramp: (")
    lines += [nested.row(emit.RonEntry("", hexstr, key, semantic[key]), indent=12)
              for key, hexstr in zip(RAMP, types["ramp"])]
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
