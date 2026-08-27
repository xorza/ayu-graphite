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

Two pairs would land on one colour. The palette reaches magenta at exactly one
tint through its semantic layer, and darkroom asks for two violets that meet
on a node's head; it reaches teal at one tint, and asks for a tenth wire hue
after the obvious nine are spent. Both are resolved below, on the entries they
affect, against what the two roles are for rather than by moving one of them a
shade.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from palette import Palette, load_palette

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(os.path.dirname(HERE), "ayu-graphite.toml")
OUT = os.path.join(HERE, "ayu-graphite.ron")

# darkroom role -> the semantic role it is taken from.
ROLE = {
    # Chrome. `chrome_fill` takes `bg` and the graph ground goes below it:
    # see DERIVED. `tab_inactive` is the rung that stops an unselected tab
    # from reading as a bare label on the bar.
    "chrome_fill": "bg",
    "tab_inactive": "panel",
    "node_fill": "elem",
    "pal_elem_hover": "elem_hover",
    "header_fill": "elem_active",
    "pal_elem_active": "elem_active",
    "canvas_dot": "border",
    "pal_border_focused": "border_focused",
    # Ink. `port_label` keeps its own slot rather than reading `text_muted`
    # at the call site: a port row wants one strong element, and which ink
    # de-emphasizes the other two is the interface's decision to change.
    "pal_text": "text",
    "text_muted": "text_muted",
    "port_label": "text_muted",
    "pal_text_disabled": "text_disabled",
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
    # The violet a node's head wears to say it is never cached. It shares
    # the palette's one bright magenta with the `image` wire below, which is
    # the pair the palette can afford to collapse: a glyph on a head and a
    # line between two nodes are never the same mark.
    "badge_impure": "syn_number",
    # Busy is the status with no colour of its own — nothing about work in
    # progress is red or green — so it takes the one vivid hue the status
    # roster does not already spend. It cannot have the second magenta,
    # because there is no second magenta and `badge_impure` sits beside it
    # on the same head. It shares teal with the `int` wire instead, on the
    # same grounds the violet is shared.
    "status_busy": "syn_string_regex",
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
    "string": "syn_string_special",
    # `path` cannot have the magenta it reads best as — `image` has the
    # palette's only one — so it takes the blue, which is the hue no other
    # wire and no status is using.
    "path": "hint",
    # The dominant payload on this canvas earns a deliberate colour rather
    # than a hash pick, and this is the one it has always had.
    "image": "syn_number",
}
RAMP = ["syn_keyword", "success", "ansi_bright_yellow", "syn_punctuation"]

# Two wire hues closer than this in OKLab are one colour on a 2px line. The
# floor is what the ten actually achieve, less a margin — it catches a
# collapse without firing on drift.
WIRE_FLOOR = 0.06

# The chrome surfaces that stack in one view, darkest first. Each must be
# lighter than the one under it, or a control disappears into its ground.
LADDER = ("canvas_bg", "chrome_fill", "tab_inactive", "node_fill",
          "pal_elem_hover", "header_fill")

CHROME_GREYS = ("gray_24", "gray_29", "gray_34", "gray_39", "gray_44")

# The order the table is written in, and the headings it is written under.
SECTIONS = (
    ("Chrome — the surfaces the editor is built out of, and the inks on them.", (
        "canvas_bg", "canvas_dot", "chrome_fill", "tab_inactive", "node_fill",
        "node_border", "header_fill", "node_ambient_shadow", "pal_text",
        "text_muted", "pal_text_disabled", "pal_elem_hover", "pal_elem_active",
        "pal_border_focused")),
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


def channels(hex6: str) -> list[float]:
    h = hex6.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def to_linear(c: float) -> float:
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def luminance(hex6: str) -> float:
    r, g, b = (to_linear(c) for c in channels(hex6))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def oklab(hex6: str) -> tuple[float, float, float]:
    r, g, b = (to_linear(c) for c in channels(hex6))
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s_ = l ** (1 / 3), m ** (1 / 3), s ** (1 / 3)
    return (
        0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
        1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
        0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_,
    )


def grey_at(lightness: float) -> str:
    """The grey of Oklab lightness `lightness`, as a hex triple.

    A neutral has all three channels equal, so its Oklab L is the cube root
    of its linear value and this inverts in one step.
    """
    linear = lightness ** 3
    v = (12.92 * linear if linear <= 0.0031308
         else 1.055 * linear ** (1 / 2.4) - 0.055)
    byte = max(0, min(255, round(v * 255)))
    return f"#{byte:02x}{byte:02x}{byte:02x}"


def ramp_step(primitives: dict[str, str]) -> float:
    """The mean Oklab lightness between adjacent chrome greys.

    Measured off the palette rather than written down here, so the rung this
    file adds keeps the ramp's spacing when the ramp is respaced.
    """
    lights = [oklab(primitives[name])[0] for name in CHROME_GREYS]
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
        values[role] = grey_at(oklab(roles[key])[0] - step)

    values["type_colors"] = {field: roles[key] for field, key in TYPE.items()}
    values["type_colors"]["ramp"] = [roles[key] for key in RAMP]
    return values


def check(values: dict) -> None:
    """The three things a palette edit could quietly break here.

    Each is a rule darkroom's own drawing depends on and cannot state: the
    file it reads is a table of colours, and a table cannot say that two of
    its entries have to differ.
    """
    lights = [luminance(values[role]) for role in LADDER]
    for lower, upper, under, over in zip(LADDER, LADDER[1:], lights, lights[1:]):
        assert under < over, (
            f"{lower} ({values[lower]}) is not darker than {upper} "
            f"({values[upper]}) — a surface that stacks on it disappears")

    wires = dict(values["type_colors"])
    ramp = wires.pop("ramp")
    wires.update({f"ramp[{i}]": hexstr for i, hexstr in enumerate(ramp)})
    names = sorted(wires)
    for i, one in enumerate(names):
        for other in names[i + 1:]:
            gap = sum((a - b) ** 2 for a, b in
                      zip(oklab(wires[one]), oklab(wires[other]))) ** 0.5
            assert gap >= WIRE_FLOOR, (
                f"the {one} and {other} wires are {gap:.3f} apart in OKLab "
                f"({wires[one]}, {wires[other]}) — under {WIRE_FLOOR}, a 2px "
                f"line reads as one colour")

    # A role left out of SECTIONS would be dropped from the file, and darkroom
    # would report it as a field its table is missing — true, and a long way
    # from the line that caused it.
    written = {role for _, roles in SECTIONS for role in roles}
    flat = {role for role in values if role != "type_colors"}
    assert written == flat, f"SECTIONS and the roles disagree: {written ^ flat}"


def sources(semantic: dict[str, str]) -> dict[str, tuple[str, str]]:
    """Per role, the role it came from and the primitive that resolved to —
    the two columns of provenance every line carries."""
    out = {role: (key, semantic[key]) for role, key in ROLE.items()}
    out.update({role: (key, semantic[key]) for role, (key, _) in ALPHA.items()})
    out.update({role: ("(the ramp's step)", f"below {semantic[key]}")
                for role, key in DERIVED.items()})
    out.update({role: ("(no outline)", "the shadow carries the edge")
                for role in LITERAL})
    return out


def build_darkroom(palette: Palette, semantic: dict[str, str],
                   primitives: dict[str, str]) -> str:
    values = resolve(palette, primitives)
    check(values)
    source = sources(semantic)

    # One set of column widths for the whole table, so provenance reads as
    # three columns rather than as a comment trailing each value.
    name_w = max(len(role) for role in source) + 2
    # +5: the two quotes, the comma, and the two spaces before the comment.
    value_w = max(len(values[role]) for role in source) + 5
    key_w = max(len(key) for key, _ in source.values()) + 2

    def entry(role: str) -> str:
        key, primitive = source[role]
        value = f'"{values[role]}",'
        return (f"    {role + ':':{name_w}}{value:{value_w}}"
                f"// {key:{key_w}}{primitive}")

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
        lines.extend(entry(role) for role in roles)
        lines.append("")

    lines.append("    // A wire's hue is the type flowing along it. `ramp` backs the")
    lines.append("    // open-ended custom and enum families, keyed by type id.")
    lines.append("    type_colors: (")
    field_w = max(len(field) for field in TYPE) + 2
    for field, key in TYPE.items():
        value = f'"{values["type_colors"][field]}",'
        lines.append(f'        {field + ":":{field_w}}{value:{value_w}}'
                     f"// {key:{key_w}}{semantic[key]}")
    lines.append("        ramp: [")
    for key, hexstr in zip(RAMP, values["type_colors"]["ramp"]):
        value = f'"{hexstr}",'
        lines.append(f"            {value:{value_w}}// {key:{key_w}}{semantic[key]}")
    lines.append("        ],")
    lines.append("    ),")
    lines.append(")")
    return "\n".join(lines) + "\n"


def main() -> None:
    with open(SOURCE, "rb") as f:
        data = tomllib.load(f)
    body = build_darkroom(load_palette(SOURCE), data["semantic"], data["primitives"])
    with open(OUT, "w") as f:
        f.write(body)
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
