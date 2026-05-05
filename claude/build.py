#!/usr/bin/env python3
"""Read ../ayu-mirage.toml and emit ./ayu-mirage.json (Claude Code theme)."""
import json
import os
import tomllib
from dataclasses import dataclass


@dataclass
class Palette:
    """Mirrors the shape of ayu-mirage.toml. Defined in every target builder
    so each subdir is self-contained — no shared module to import across."""
    bg: str
    panel: str
    surface: str
    elem: str
    elem_hover: str
    elem_active: str
    elem_selected: str
    title_bar: str
    title_bar_inactive: str

    border: str
    border_focused: str

    text: str
    text_muted: str
    text_disabled: str

    accent: str
    success: str
    warning: str
    error: str

    info_bg: str
    info_border: str
    hint_bg: str
    hint_border: str
    success_bg: str
    success_border: str
    warning_bg: str
    warning_border: str
    error_bg: str
    error_border: str

    created: str
    created_bg: str
    deleted: str
    deleted_bg: str

    ansi_blue: str
    ansi_magenta: str
    ansi_cyan: str

    syn_keyword: str
    syn_function: str
    syn_string: str
    syn_string_regex: str
    syn_comment: str
    syn_number: str
    syn_type: str
    syn_operator: str
    syn_attribute: str
    syn_punctuation: str
    syn_doc: str
    syn_string_special: str
    syn_predictive: str


def load_palette(path: str) -> Palette:
    with open(path, "rb") as f:
        data = tomllib.load(f)
    flat = {k: v for section in data.values() for k, v in section.items()}
    return Palette(**flat)


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

        "diffAdded":             p.created_bg,
        "diffAddedDimmed":       p.created_bg,
        "diffAddedWord":         p.created,
        "diffAddedWordDimmed":   p.created,
        "diffRemoved":           p.deleted_bg,
        "diffRemovedDimmed":     p.deleted_bg,
        "diffRemovedWord":         p.deleted,
        "diffRemovedWordDimmed": p.deleted,

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
