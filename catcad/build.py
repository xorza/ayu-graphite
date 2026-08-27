#!/usr/bin/env python3
"""Read ../ayu-graphite.toml and emit ./ayu-graphite.ron (CatCad's palette).

CatCad is a parametric CAD application. It names one colour per role it draws
with — a chip's three resting states, the ladder a sketch is coloured by as its
constraints pin it down, a plane's outline per world axis — and builds its whole
theme from the table this writes. Sizes are not here: a stroke width and the
side of a chip are facts about that interface, not about a palette.

Two transforms happen on the way out.

Neutrals lose their tint. This palette's ramp is not consistently anything —
gray_600 and gray_500 run cool, gray_300 and gray_200 run warm, and the four
darkest steps are flat — so a large surface picks up whichever way its own step
leans. Each neutral role is re-emitted at the grey of the same relative
luminance, which drops the chroma and leaves the ramp's spacing exactly where
tools/audit.py checks it.

One role has no step of its own. CatCad's dimmest ink wants the gap between the
step `elem_active` sits on and the step `line_number` sits on, so it is placed
evenly between those two rather than added to the palette, because nothing else
needs it. Both ends are read out of the palette, and each line of the table says
which two it landed between.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import color
import emit
from palette import Palette, load_source

# CatCad role -> the semantic role it is taken from. Split by what happens on
# the way: the first group is re-emitted grey, the second passes through.
#
# A hue says something in a drawing — how much freedom the constraints have
# left, which world axis a plane faces, that a relation is the spare one — so a
# hue that had been shifted would be saying it about a different colour.
NEUTRAL = {
    "ground": "bg",
    "pill": "panel",
    "pill_edge": "text",
    "rule": "text",
    "chip": "elem",
    "chip_lit": "elem_hover",
    "chip_active": "elem_active",
    "chip_held": "text",
    "on_held": "bg",
    "ink": "text_muted",
    "ink_lit": "text",
    "cube_low": "panel",
    "cube_high": "line_number",
    "focus": "text",
    "solid": "line_number_hover",
    "dormant": "text_muted",
    "ghost": "text",
    "sheet_datum": "line_number",
    "depth_arrow": "selection_fg",
}

HUE = {
    "determined": "syn_type",
    "partly": "warning",
    "free": "syn_keyword",
    "pinned": "error",
    "dormant_face": "info_bg",
    "face": "info_border",
    # The ANSI normal row is pinned to one luminance per hue by this palette's
    # own arithmetic, which is what a three-axis plane trio wants: three hues at
    # one weight, so no face of the world reads louder than another. No other
    # family here is luminance-matched across hues.
    "sheet_ground": "ansi_green",
    "sheet_front": "ansi_blue",
    "sheet_side": "ansi_red",
    "mark": "syn_number",
    "redundant": "ansi_bright_red",
    "hovered": "syn_string_special",
    "selected": "success",
    "goes": "success_border",
    "stops": "error_border",
    "doing": "info_border",
}

# The order the table is written in, and the headings it is written under.
SECTIONS = (
    ("Chrome — the surfaces and inks a control floating over the drawing wears.", (
        "ground", "pill", "pill_edge", "rule", "chip", "chip_lit", "chip_active",
        "chip_held", "on_held", "ink", "ink_lit", "ink_dim", "cube_low",
        "cube_high", "focus")),
    ("Drawing — what the geometry and the solids beside it are painted in.", (
        "solid", "determined", "partly", "free", "pinned", "dormant",
        "dormant_face", "face", "ghost", "sheet_ground", "sheet_front",
        "sheet_side", "sheet_datum", "mark", "redundant", "depth_arrow")),
    ("Lighting — what singling something out looks like.", (
        "hovered", "selected")),
    ("Form — the answers a prompt standing on the drawing offers.", (
        "goes", "stops", "doing")),
)


def neutralise(hex6: str) -> str:
    """The same colour with its tint taken off: the grey that emits as much
    light as it does."""
    return color.grey(color.luminance(hex6))


def between(dark: str, light: str, part: float) -> str:
    """A grey `part` of the way from `dark` to `light` in contrast ratio.

    Even in what the eye reads as a step, which is the spacing the rest of the
    ramp is built on — an average of the two luminances would land closer to
    the light end than to the dark one.
    """
    lo, hi = color.luminance(dark), color.luminance(light)
    ratio = ((hi + 0.05) / (lo + 0.05)) ** part
    return color.grey((lo + 0.05) * ratio - 0.05)


def entries(p: Palette, semantic: dict[str, str]) -> dict[str, emit.RonEntry]:
    """Every CatCad role, with the two columns of provenance behind it."""
    roles = p.as_dict()
    out = {role: emit.RonEntry(role, neutralise(roles[key]), key, semantic[key])
           for role, key in NEUTRAL.items()}
    out.update({role: emit.RonEntry(role, roles[key], key, semantic[key])
                for role, key in HUE.items()})
    # A third of the way up the ramp's one gap, which is where the step would
    # sit if the palette had one.
    out["ink_dim"] = emit.RonEntry(
        "ink_dim",
        between(neutralise(p.elem_active), neutralise(p.line_number), 1 / 3),
        "(the ramp's gap)",
        f"between {semantic['elem_active']} and {semantic['line_number']}")

    # A role left out of SECTIONS would be dropped from the file, and CatCad
    # would report it as a field its table is missing — true, and a long way
    # from the line that caused it.
    written = {role for _, roles in SECTIONS for role in roles}
    assert written == set(out), (
        f"SECTIONS and the mapping disagree: {written ^ set(out)}")
    return out


def build_catcad(p: Palette, semantic: dict[str, str]) -> str:
    table = entries(p, semantic)
    columns = emit.RonColumns.of(table.values())
    lines = [
        "// Ayu Graphite, for CatCad — generated. Do not edit by hand.",
        "//",
        "// Source:    ayu-graphite.toml",
        "// Generator: ayu-graphite/catcad/build.py",
        "//",
        "// Each entry names a role CatCad draws with, the role here it is taken",
        "// from, and the primitive that resolves to. Neutrals were re-emitted at",
        "// the grey of the same relative luminance. Hues passed through: a hue",
        "// says something in a drawing, and a shifted one would say it about a",
        "// different colour.",
        "(",
    ]
    for heading, roles in SECTIONS:
        lines.append(f"    // {heading}")
        lines += [columns.row(table[role]) for role in roles]
        lines.append("")
    lines[-1] = ")"
    return "\n".join(lines) + "\n"


def main() -> None:
    src = load_source()
    emit.write_text(emit.beside(__file__, "ayu-graphite.ron"),
                    build_catcad(src.palette, src.semantic))


if __name__ == "__main__":
    main()
