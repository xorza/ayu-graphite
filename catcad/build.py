#!/usr/bin/env python3
"""Read ../ayu-graphite.toml and emit ./ayu-graphite.ron (CatCad's palette).

CatCad is a parametric CAD application. It names one colour per role it draws
with — a chip's three resting states, the ladder a sketch is coloured by as its
constraints pin it down, a plane's outline per world axis — and builds its whole
theme from the table this writes. Sizes are not here: a stroke width and the
side of a chip are facts about that interface, not about a palette.

Two transforms happen on the way out.

Neutrals lose their tint. A CAD viewport is mostly one large flat surface, and
a cast that hides on a toolbar reads across a whole window, so this target
states neutrality rather than inheriting it. Each neutral role is re-emitted at
the grey of the same relative luminance, which drops any chroma and leaves the
ramp's spacing exactly where tools/audit.py checks it. The ramp is neutral as
it stands, so the transform moves nothing today — it is what holds this target
neutral when those greys next move.

One role has no step of its own. The ramp climbs in steps of about 1.2:1 and
opens one wide gap, and CatCad's dimmest ink wants to sit in that gap. The gap
is measured off the ramp rather than named here, and the ink lands a third of
the way up it, so the ink follows the ramp when the ramp is respaced. Each line
of the table says which two steps a colour came from, this one included.
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


def ramp_gap(primitives: dict[str, str]) -> tuple[str, str]:
    """The two neutral steps with the most room between them.

    Which pair brackets the ramp's one gap is measured rather than written
    down, so the rung this file adds stays inside the gap when the ramp is
    respaced."""
    ramp = sorted((name for name in primitives if name.startswith("gray_")),
                  key=lambda name: color.luminance(primitives[name]))
    return max(zip(ramp, ramp[1:]),
               key=lambda ends: color.contrast(primitives[ends[0]],
                                               primitives[ends[1]]))


def entries(p: Palette, semantic: dict[str, str],
            primitives: dict[str, str]) -> dict[str, emit.RonEntry]:
    """Every CatCad role, with the two columns of provenance behind it."""
    roles = p.as_dict()
    out = {role: emit.RonEntry(role, neutralise(roles[key]), key, semantic[key])
           for role, key in NEUTRAL.items()}
    out.update({role: emit.RonEntry(role, roles[key], key, semantic[key])
                for role, key in HUE.items()})
    # A third of the way up the ramp's one gap, which is where the step would
    # sit if the palette had one.
    dark, light = ramp_gap(primitives)
    dim = between(primitives[dark], primitives[light], 1 / 3)
    assert (color.luminance(primitives[dark]) < color.luminance(dim)
            < color.luminance(primitives[light])), (
        f"ink_dim landed on {dim}, outside the {dark} to {light} step — the "
        f"ramp has no gap left to hold it")
    out["ink_dim"] = emit.RonEntry("ink_dim", dim, "(the ramp's gap)",
                                   f"between {dark} and {light}")

    # A role left out of SECTIONS would be dropped from the file, and CatCad
    # would report it as a field its table is missing — true, and a long way
    # from the line that caused it.
    written = {role for _, roles in SECTIONS for role in roles}
    assert written == set(out), (
        f"SECTIONS and the mapping disagree: {written ^ set(out)}")
    return out


def build_catcad(p: Palette, semantic: dict[str, str],
                 primitives: dict[str, str]) -> str:
    table = entries(p, semantic, primitives)
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
                    build_catcad(src.palette, src.semantic, src.primitives))


if __name__ == "__main__":
    main()
