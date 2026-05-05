#!/usr/bin/env python3
"""Port the processed Zed theme to Claude Code.

Reads dist/ayu-mirage-high-contrast.json and writes dist/ayu-mirage.json
in Claude Code's custom-theme schema.

Includes the manual fixes settled on during tuning:
  - suggestion = warning yellow (highlighted slash-command picker row)
  - userMessageBackground = element.background (visible prompt block)
"""
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ZED_PATH = os.path.join(HERE, "dist", "ayu-mirage-high-contrast.json")
CLAUDE_PATH = os.path.join(HERE, "dist", "ayu-mirage.json")


def strip_alpha(c: str) -> str:
    """#rrggbbaa -> #rrggbb (Claude accepts only 6-digit hex)."""
    m = re.fullmatch(r"#([0-9a-fA-F]{6})([0-9a-fA-F]{2})?", c)
    return "#" + m.group(1).lower() if m else c


def main() -> None:
    src = json.load(open(ZED_PATH))
    style = src["themes"][0]["style"]
    syntax = style["syntax"]

    def s(key):
        return strip_alpha(style[key])

    def syn(key):
        return strip_alpha(syntax[key]["color"])

    overrides = {
        "background":              s("editor.background"),
        "userMessageBackground":   s("element.background"),
        "bashMessageBackgroundColor": s("element.background"),
        "memoryBackgroundColor":   s("element.background"),

        "text":         s("text"),
        "inverseText":  s("editor.background"),
        "inactive":     s("text.muted"),
        "subtle":       syn("comment"),
        "suggestion":   s("warning"),
        "remember":     syn("number"),

        "claude":         syn("keyword"),
        "claudeShimmer":  syn("function"),
        "claudeBlue_FOR_SYSTEM_SPINNER":        s("text.accent"),
        "claudeBlueShimmer_FOR_SYSTEM_SPINNER": syn("type"),

        "success":          s("success"),
        "error":            s("error"),
        "warning":          s("warning"),
        "warningShimmer":   syn("function"),

        "permission":         s("warning"),
        "permissionShimmer":  syn("function"),
        "planMode":           s("text.accent"),
        "ide":                s("text.accent"),
        "autoAccept":         s("success"),
        "promptBorder":         s("text.accent"),
        "promptBorderShimmer":  syn("type"),
        "bashBorder":           syn("number"),

        "diffAdded":           s("created.background"),
        "diffAddedDimmed":     s("created.background"),
        "diffAddedWord":       s("created"),
        "diffAddedWordDimmed": s("created"),
        "diffRemoved":         s("deleted.background"),
        "diffRemovedDimmed":   s("deleted.background"),
        "diffRemovedWord":     s("deleted"),
        "diffRemovedWordDimmed": s("deleted"),

        "red_FOR_SUBAGENTS_ONLY":    s("error"),
        "blue_FOR_SUBAGENTS_ONLY":   s("text.accent"),
        "green_FOR_SUBAGENTS_ONLY":  s("success"),
        "yellow_FOR_SUBAGENTS_ONLY": s("warning"),
        "purple_FOR_SUBAGENTS_ONLY": syn("number"),
        "orange_FOR_SUBAGENTS_ONLY": syn("keyword"),
        "pink_FOR_SUBAGENTS_ONLY":   syn("operator"),
        "cyan_FOR_SUBAGENTS_ONLY":   syn("string.regex"),
        "professionalBlue":          s("text.accent"),
    }

    out = {"name": "Ayu Mirage", "base": "dark", "overrides": overrides}
    with open(CLAUDE_PATH, "w") as f:
        json.dump(out, f, indent=2)
    print(f"wrote {CLAUDE_PATH}")


if __name__ == "__main__":
    main()
