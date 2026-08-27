#!/usr/bin/env python3
"""Read ../ayu-graphite.toml and emit ./ayu-graphite.json (Claude Code theme).

Claude Code's built-in themes (see tools/claude-builtin-themes/) use the
rgb(R,G,B) string form for color values. Hex overrides (#rrggbb) parse but
some renderers ignore them and fall through to the base theme — so we emit
rgb() to match the convention.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from palette import Palette, load_palette


def rgb(hex6: str) -> str:
    h = hex6.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgb({r},{g},{b})"


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

        "claude":         p.syn_keyword,
        "claudeShimmer":  p.syn_function,
        "claudeBlue_FOR_SYSTEM_SPINNER":        p.accent,
        "claudeBlueShimmer_FOR_SYSTEM_SPINNER": p.syn_type,

        "success":          p.success,
        "error":            p.error,
        "warning":          p.warning,
        "warningShimmer":   p.syn_function,

        "permission":         p.warning,
        "permissionShimmer":  p.syn_function,
        "planMode":           p.accent,
        "ide":                p.accent,
        "autoAccept":         p.success,
        "promptBorder":         p.accent,
        "promptBorderShimmer":  p.syn_type,
        "bashBorder":           p.syn_number,

        "diffAdded":          p.success_bg,
        "diffAddedDimmed":    p.success_bg,
        "diffAddedWord":      p.diff_word_plus,
        "diffRemoved":        p.error_bg,
        "diffRemovedDimmed":  p.error_bg,
        "diffRemovedWord":    p.diff_word_minus,

        "red_FOR_SUBAGENTS_ONLY":    p.error,
        "blue_FOR_SUBAGENTS_ONLY":   p.accent,
        "green_FOR_SUBAGENTS_ONLY":  p.success,
        "yellow_FOR_SUBAGENTS_ONLY": p.warning,
        "purple_FOR_SUBAGENTS_ONLY": p.syn_number,
        "orange_FOR_SUBAGENTS_ONLY": p.syn_keyword,
        "pink_FOR_SUBAGENTS_ONLY":   p.syn_operator,
        "cyan_FOR_SUBAGENTS_ONLY":   p.syn_string_regex,
        "professionalBlue":          p.accent,
    }
    overrides = {k: rgb(v) for k, v in raw.items()}
    # NOTE: Claude Code 2.1.x ignores `overrides` for diff line backgrounds
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
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.dirname(here)
    p = load_palette(os.path.join(repo, "ayu-graphite.toml"))
    out = os.path.join(here, "ayu-graphite.json")
    with open(out, "w") as f:
        json.dump(build_claude(p), f, indent=2)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
