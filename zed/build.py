#!/usr/bin/env python3
"""Pure transformer: ../ayu-mirage.toml -> ./ayu-mirage-high-contrast.json.

No upstream JSON, no pipeline, no math beyond appending alpha hex digits.
Every Zed style key is mapped explicitly to a palette token (or a constant
where the role is purely structural like a transparent border).
"""
import json
import os
import tomllib
from dataclasses import dataclass


@dataclass
class Palette:
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


def opaque(hex6: str) -> str:
    """#rrggbb -> #rrggbbff."""
    return hex6 + "ff"


def alpha(hex6: str, aa: str) -> str:
    """#rrggbb + 'bf' -> #rrggbbbf."""
    return hex6 + aa


def syn(color: str, italic: bool = False, bold: bool = False) -> dict:
    return {
        "color": opaque(color),
        "font_style": "italic" if italic else None,
        "font_weight": 700 if bold else None,
    }


def build_zed(p: Palette) -> dict:
    style = {
        "background":              opaque(p.title_bar),
        "border":                  opaque(p.border),
        "border.disabled":         opaque(p.panel),
        "border.focused":          opaque(p.border_focused),
        "border.selected":         opaque(p.border_focused),
        "border.transparent":      "#00000000",
        "border.variant":          opaque(p.bg),

        "elevated_surface.background": opaque(p.surface),
        "surface.background":          opaque(p.surface),
        "element.background":          opaque(p.elem),
        "element.hover":               opaque(p.elem_hover),
        "element.active":              opaque(p.elem_active),
        "element.selected":            opaque(p.elem_selected),
        "element.disabled":            opaque("#353b4b"),
        "drop_target.background":      alpha("#a7a7a5", "80"),
        "ghost_element.background":    alpha("#121212", "00"),
        "ghost_element.hover":         opaque(p.elem_hover),
        "ghost_element.active":        opaque(p.elem_active),
        "ghost_element.selected":      opaque(p.elem_selected),
        "ghost_element.disabled":      opaque("#353b4b"),

        "text":             opaque(p.text),
        "text.muted":       opaque(p.text_muted),
        "text.placeholder": opaque(p.text_disabled),
        "text.disabled":    opaque(p.text_disabled),
        "text.accent":      opaque(p.accent),

        "icon":             opaque(p.text),
        "icon.muted":       opaque(p.text_muted),
        "icon.disabled":    opaque(p.text_disabled),
        "icon.placeholder": opaque(p.text_muted),
        "icon.accent":      opaque(p.ansi_blue),

        "status_bar.background":         opaque(p.title_bar),
        "title_bar.background":          opaque(p.title_bar),
        "title_bar.inactive_background": opaque(p.title_bar_inactive),
        "toolbar.background":            opaque(p.bg),
        "tab_bar.background":            opaque(p.panel),
        "tab.inactive_background":       opaque(p.panel),
        "tab.active_background":         opaque(p.bg),

        "search.match_background":        alpha("#7edeff", "66"),
        "search.active_match_background": alpha("#ff7d2d", "66"),

        "panel.background":      opaque(p.panel),
        "panel.focused_border":  None,   # upstream Ayu leaves these null —
        "pane.focused_border":   None,   # Zed falls back to its default.

        "scrollbar.thumb.background":       alpha("#a4a4a4", "4c"),
        "scrollbar.thumb.hover_background": opaque(p.elem_hover),
        "scrollbar.thumb.border":           opaque(p.border),
        "scrollbar.track.background":       alpha("#121212", "00"),
        "scrollbar.track.border":           opaque("#2e2e2e"),

        "editor.foreground":           opaque(p.text),
        "editor.background":           opaque(p.bg),
        "editor.gutter.background":    opaque(p.bg),
        "editor.subheader.background": opaque(p.panel),
        "editor.active_line.background":      alpha(p.panel, "bf"),
        "editor.highlighted_line.background": opaque(p.panel),
        "editor.line_number":          "#5c6279",
        "editor.active_line_number":   "#f5f7ff",
        "editor.hover_line_number":    "#c1c6df",
        "editor.invisible":            opaque("#83878a"),
        "editor.wrap_guide":           alpha(p.text, "0d"),
        "editor.active_wrap_guide":    alpha(p.text, "1a"),
        "editor.document_highlight.read_background":  alpha("#7ddeff", "1a"),
        "editor.document_highlight.write_background": alpha("#838587", "66"),

        "terminal.background":        opaque(p.bg),
        "terminal.foreground":        opaque(p.text),
        "terminal.bright_foreground": opaque(p.text),
        "terminal.dim_foreground":    opaque("#9e9d94"),
        "terminal.ansi.black":         opaque(p.bg),
        "terminal.ansi.bright_black":  opaque("#70747a"),
        "terminal.ansi.dim_black":     opaque("#404040"),
        "terminal.ansi.red":           opaque(p.error),
        "terminal.ansi.bright_red":    opaque("#8a302b"),
        "terminal.ansi.dim_red":       opaque("#b05043"),
        "terminal.ansi.green":         opaque(p.success),
        "terminal.ansi.bright_green":  opaque("#75a228"),
        "terminal.ansi.dim_green":     opaque("#97be42"),
        "terminal.ansi.yellow":        opaque(p.warning),
        "terminal.ansi.bright_yellow": opaque("#9d7222"),
        "terminal.ansi.dim_yellow":    opaque("#ba913b"),
        "terminal.ansi.blue":          opaque(p.ansi_blue),
        "terminal.ansi.bright_blue":   opaque("#1e6d96"),
        "terminal.ansi.dim_blue":      opaque("#3b91ba"),
        "terminal.ansi.magenta":       opaque(p.ansi_magenta),
        "terminal.ansi.bright_magenta":opaque("#177083"),
        "terminal.ansi.dim_magenta":   opaque("#2b94aa"),
        "terminal.ansi.cyan":          opaque(p.ansi_cyan),
        "terminal.ansi.bright_cyan":   opaque("#3f846e"),
        "terminal.ansi.dim_cyan":      opaque("#69b9a0"),
        "terminal.ansi.white":         opaque(p.text),
        "terminal.ansi.bright_white":  opaque("#ffffff"),
        "terminal.ansi.dim_white":     opaque("#9e9d94"),

        "link_text.hover": opaque(p.accent),

        # Status families. Diagnostic block tints (.background, .border) come
        # from the [status_bg] section of the palette.
        "conflict":             opaque(p.warning),
        "conflict.background":  opaque(p.warning_bg),
        "conflict.border":      opaque(p.warning_border),
        "created":              opaque(p.created),
        "created.background":   opaque(p.created_bg),
        "created.border":       opaque(p.success_border),
        "deleted":              opaque(p.deleted),
        "deleted.background":   opaque(p.deleted_bg),
        "deleted.border":       opaque(p.error_border),
        "error":                opaque(p.error),
        "error.background":     opaque(p.error_bg),
        "error.border":         opaque(p.error_border),
        "hidden":               opaque(p.text_disabled),
        "hidden.background":    opaque("#4c515a"),
        "hidden.border":        opaque(p.panel),
        "hint":                 opaque("#77adbc"),
        "hint.background":      opaque(p.hint_bg),
        "hint.border":          opaque(p.hint_border),
        "ignored":              opaque(p.text_disabled),
        "ignored.background":   opaque("#4c515a"),
        "ignored.border":       opaque(p.border),
        "info":                 opaque(p.ansi_blue),
        "info.background":      opaque(p.info_bg),
        "info.border":          opaque(p.info_border),
        "modified":             opaque(p.warning),
        "modified.background":  opaque(p.warning_bg),
        "modified.border":      opaque(p.warning_border),
        "predictive":           opaque(p.syn_predictive),
        "predictive.background":opaque(p.created_bg),
        "predictive.border":    opaque(p.success_border),
        "renamed":              opaque(p.ansi_blue),
        "renamed.background":   opaque(p.hint_bg),
        "renamed.border":       opaque(p.hint_border),
        "success":              opaque(p.success),
        "success.background":   opaque(p.success_bg),
        "success.border":       opaque(p.success_border),
        "unreachable":          opaque(p.text_muted),
        "unreachable.background": opaque("#4c515a"),
        "unreachable.border":   opaque(p.border),
        "warning":              opaque(p.warning),
        "warning.background":   opaque(p.warning_bg),
        "warning.border":       opaque(p.warning_border),

        "players": _build_players(p),
        "syntax":  _build_syntax(p),
    }
    return {
        "$schema": "https://zed.dev/schema/themes/v0.2.0.json",
        "name": "Ayu Mirage High Contrast",
        "author": "xxorza",
        "themes": [{
            "name": "Ayu Mirage High Contrast",
            "appearance": "dark",
            "style": style,
        }],
    }


def _build_players(p: Palette) -> list:
    """8 collaboration cursors. Cursor hue rotates through accent + syntax;
    background is a fixed mid-gray (Zed's convention)."""
    cursors = [
        p.ansi_blue, p.ansi_magenta, p.syn_keyword, p.syn_number,
        p.ansi_cyan, p.error, p.warning, p.success,
    ]
    bg_grays = ["#868686", "#7c7c7c", "#808080", "#a4a4a4",
                "#949494", "#898989", "#868686", "#8c8c8c"]
    return [
        {
            "cursor":     opaque(c),
            "background": opaque(bg),
            "selection":  alpha(c, "3d"),
        }
        for c, bg in zip(cursors, bg_grays)
    ]


def _build_syntax(p: Palette) -> dict:
    return {
        "attribute":               syn(p.syn_attribute),
        "boolean":                 syn(p.syn_number),
        "comment":                 syn(p.syn_comment),
        "comment.doc":             syn(p.syn_doc),
        "constant":                syn(p.syn_number),
        "constructor":             syn(p.syn_attribute),
        "embedded":                syn(p.text),
        "emphasis":                syn(p.syn_attribute),
        "emphasis.strong":         syn(p.syn_attribute, bold=True),
        "enum":                    syn(p.syn_keyword),
        "function":                syn(p.syn_function),
        "hint":                    syn("#77adbc"),
        "keyword":                 syn(p.syn_keyword),
        "label":                   syn(p.syn_attribute),
        "link_text":               syn(p.syn_keyword, italic=True),
        "link_uri":                syn(p.syn_string),
        "namespace":               syn(p.text),
        "number":                  syn(p.syn_number),
        "operator":                syn(p.syn_operator),
        "predictive":              syn(p.syn_predictive, italic=True),
        "preproc":                 syn(p.syn_keyword),
        "primary":                 syn(p.text),
        "property":                syn(p.syn_attribute),
        "punctuation":             syn(p.syn_punctuation),
        "punctuation.bracket":     syn(p.syn_punctuation),
        "punctuation.delimiter":   syn(p.syn_punctuation),
        "punctuation.list_marker": syn(p.syn_punctuation),
        "punctuation.markup":      syn(p.syn_punctuation),
        "punctuation.special":     syn(p.syn_number),
        "selector":                syn(p.syn_number),
        "selector.pseudo":         syn(p.syn_attribute),
        "string":                  syn(p.syn_string),
        "string.escape":           syn(p.syn_doc),
        "string.regex":            syn(p.syn_string_regex),
        "string.special":          syn(p.syn_string_special),
        "string.special.symbol":   syn(p.syn_keyword),
        "tag":                     syn(p.syn_attribute),
        "text.literal":            syn(p.syn_keyword),
        "title":                   syn(p.text, bold=True),
        "type":                    syn(p.syn_type),
        "variable":                syn(p.text),
        "variant":                 syn(p.syn_attribute),
        "diff.plus":               syn("#b5ff10"),
        "diff.minus":              syn("#ff3b48"),
    }


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.dirname(here)
    p = load_palette(os.path.join(repo, "ayu-mirage.toml"))
    out = os.path.join(here, "ayu-mirage-high-contrast.json")
    with open(out, "w") as f:
        json.dump(build_zed(p), f, indent=2)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
