#!/usr/bin/env python3
"""Read ../ayu-graphite.toml and emit ./ayu-graphite.json (Claude Code theme).

Claude Code's built-in themes (see tools/claude-builtin-themes/) use the
rgb(R,G,B) string form for color values. Hex overrides (#rrggbb) parse but
some renderers ignore them and fall through to the base theme — so we emit
rgb() to match the convention.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import emit
from palette import Palette, load_palette


def rgb(hex6: str) -> str:
    return "rgb({},{},{})".format(*emit.rgb_bytes(hex6))


def build_claude(p: Palette) -> dict:
    raw = {
        "background":                 p.bg,
        "userMessageBackground":      p.elem_active,
        "bashMessageBackgroundColor": p.elem_active,
        "memoryBackgroundColor":      p.elem_active,

        "text":         p.text,
        "inverseText":  p.bg,
        "inactive":     p.text_muted,
        "subtle":       p.syn_comment,
        "suggestion":   p.warning,
        "remember":     p.syn_number,

        # A shimmer is a lighter band swept over its base. The grid has no
        # tint above `bright`, so the band is `text`, the one ink lighter
        # than every base it sweeps.
        "claude":         p.syn_keyword,
        "claudeShimmer":  p.syn_function,
        "claudeBlue_FOR_SYSTEM_SPINNER":        p.accent,
        "claudeBlueShimmer_FOR_SYSTEM_SPINNER": p.text,

        "success":          p.success,
        "error":            p.error,
        "warning":          p.warning,
        "warningShimmer":   p.text,

        "permission":         p.warning,
        "permissionShimmer":  p.text,
        "planMode":           p.accent,
        "ide":                p.accent,
        "autoAccept":         p.success,
        "promptBorder":         p.accent,
        "promptBorderShimmer":  p.text,
        "bashBorder":           p.ansi_magenta,

        "diffAdded":          p.success_bg,
        "diffAddedDimmed":    p.success_bg,
        "diffAddedWord":      p.diff_word_plus,
        "diffRemoved":        p.error_bg,
        "diffRemovedDimmed":  p.error_bg,
        "diffRemovedWord":    p.diff_word_minus,

        # Eight names, five hues. The five with a hue of their own take its
        # bright cell. Pink, purple and cyan take the normal cell of the
        # nearest hue — red, blue, green — a full tint below its bright, so
        # every pair stays a step apart.
        "red_FOR_SUBAGENTS_ONLY":    p.error,
        "blue_FOR_SUBAGENTS_ONLY":   p.accent,
        "green_FOR_SUBAGENTS_ONLY":  p.success,
        "yellow_FOR_SUBAGENTS_ONLY": p.warning,
        "purple_FOR_SUBAGENTS_ONLY": p.ansi_blue,
        "orange_FOR_SUBAGENTS_ONLY": p.syn_keyword,
        "pink_FOR_SUBAGENTS_ONLY":   p.ansi_red,
        "cyan_FOR_SUBAGENTS_ONLY":   p.ansi_green,
        "professionalBlue":          p.accent,
    }
    # Two subagents in one color read as one subagent. The roles the eight
    # borrow may share a cell — keyword and operator do — so the mapping, not
    # the palette, has to hold them apart.
    by_color: dict[str, list[str]] = {}
    for key, value in raw.items():
        if key.endswith("_FOR_SUBAGENTS_ONLY"):
            by_color.setdefault(value, []).append(key)
    shared = [names for names in by_color.values() if len(names) > 1]
    assert not shared, f"subagent colors collide: {shared}"
    overrides = {k: rgb(v) for k, v in raw.items()}
    # Claude Code 2.1.x ignores `overrides` for diff line backgrounds
    # (`diffAdded`/`diffRemoved`/`*Dimmed`); they come from the chosen `base`.
    # `dark` paints the muted dark green/red from the binary's hardcoded
    # palette — closest hue to our success_bg/error_bg, so we use it. The
    # `dark-ansi` route doesn't help: the renderer drops `ansi:green` for
    # backgrounds entirely. The `*Word` overrides DO apply — and they are
    # backgrounds for the changed word, drawn on with the base theme's
    # near-white syntax ink, which is why they read diff_word_* and not
    # success/error.
    return {"name": "Ayu Graphite", "base": "dark", "overrides": overrides}


def main() -> None:
    emit.write_json(emit.beside(__file__, "ayu-graphite.json"),
                    build_claude(load_palette()))


if __name__ == "__main__":
    main()
