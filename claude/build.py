#!/usr/bin/env python3
"""Read ../ayu-mirage.toml and emit ./ayu-mirage.json (Claude Code theme)."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from palette import Palette, load_palette


def build_claude(p: Palette) -> dict:
    overrides = {
        "background":                 p.bg,
        "userMessageBackground":      p.elem,
        "bashMessageBackgroundColor": p.elem,
        "memoryBackgroundColor":      p.elem,

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

        "diffAdded":             p.success_bg,
        "diffAddedDimmed":       p.success_bg,
        "diffAddedWord":         p.success,
        "diffAddedWordDimmed":   p.success,
        "diffRemoved":           p.error_bg,
        "diffRemovedDimmed":     p.error_bg,
        "diffRemovedWord":         p.error,
        "diffRemovedWordDimmed": p.error,

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
    return {"name": "Ayu Mirage", "base": "dark", "overrides": overrides}


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.dirname(here)
    p = load_palette(os.path.join(repo, "ayu-mirage.toml"))
    out = os.path.join(here, "ayu-mirage.json")
    with open(out, "w") as f:
        json.dump(build_claude(p), f, indent=2)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
