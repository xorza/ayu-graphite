#!/usr/bin/env python3
"""Pure transformer: ../ayu-mirage.toml -> ./ayu-mirage-high-contrast.json.

No upstream JSON, no pipeline, no math beyond appending alpha hex digits.
Every Zed style key is mapped explicitly to a palette token (or a constant
where the role is purely structural like a transparent border).
"""
import json
import os
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from palette import Palette, load_palette


def opaque(hex6: str) -> str:
    """#rrggbb -> #rrggbbff."""
    return hex6 + "ff"


def alpha(hex6: str, aa: str) -> str:
    """#rrggbb + 'bf' -> #rrggbbbf."""
    return hex6 + aa


def syn(color: str, italic: bool = False, bold: bool = False) -> dict[str, Any]:
    return {
        "color": opaque(color),
        "font_style": "italic" if italic else None,
        "font_weight": 700 if bold else None,
    }


def build_zed(p: Palette) -> dict[str, Any]:
    # Every color routes through the palette. New visual roles get a token in
    # ayu-mirage.toml first, then a reference here — no inline hex literals.
    style: dict[str, Any] = {
        "background":              opaque(p.title_bar),
        "border":                  opaque(p.border),
        "border.disabled":         opaque(p.panel),
        "border.focused":          opaque(p.border_focused),
        "border.selected":         opaque(p.border_focused),
        "border.transparent":      alpha(p.overlay_black, "00"),
        "border.variant":          opaque(p.bg),

        "elevated_surface.background": opaque(p.surface),
        "surface.background":          opaque(p.surface),
        "element.background":          opaque(p.elem),
        "element.hover":               opaque(p.elem_hover),
        "element.active":              opaque(p.elem_active),
        "element.selected":            opaque(p.elem_selected),
        "element.disabled":            opaque(p.elem_disabled),
        "drop_target.background":      alpha(p.drop_target, "80"),
        "ghost_element.background":    alpha(p.bg, "00"),
        "ghost_element.hover":         opaque(p.elem_hover),
        "ghost_element.active":        opaque(p.elem_active),
        "ghost_element.selected":      opaque(p.elem_selected),
        "ghost_element.disabled":      opaque(p.elem_disabled),

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

        "search.match_background":        alpha(p.search_highlight, "66"),
        "search.active_match_background": alpha(p.search_match_active, "66"),

        "panel.background":      opaque(p.panel),
        "panel.focused_border":  None,   # upstream Ayu leaves these null —
        "pane.focused_border":   None,   # Zed falls back to its default.

        "scrollbar.thumb.background":       alpha(p.scrollbar_thumb, "4c"),
        "scrollbar.thumb.hover_background": opaque(p.elem_hover),
        "scrollbar.thumb.border":           opaque(p.border),
        "scrollbar.track.background":       alpha(p.bg, "00"),
        "scrollbar.track.border":           opaque(p.elem_hover),

        "editor.foreground":           opaque(p.text),
        "editor.background":           opaque(p.bg),
        "editor.gutter.background":    opaque(p.bg),
        "editor.subheader.background": opaque(p.panel),
        "editor.active_line.background":      alpha(p.panel, "bf"),
        "editor.highlighted_line.background": opaque(p.panel),
        "editor.line_number":          p.line_number,
        "editor.active_line_number":   p.line_number_active,
        "editor.hover_line_number":    p.line_number_hover,
        "editor.invisible":            opaque(p.text_disabled),
        "editor.wrap_guide":           alpha(p.text, "0d"),
        "editor.active_wrap_guide":    alpha(p.text, "1a"),
        "editor.document_highlight.read_background":  alpha(p.search_highlight, "1a"),
        "editor.document_highlight.write_background": alpha(p.text_disabled, "66"),

        "terminal.background":        opaque(p.bg),
        "terminal.foreground":        opaque(p.text),
        "terminal.bright_foreground": opaque(p.text),
        "terminal.dim_foreground":    opaque(p.ansi_dim_white),
        "terminal.ansi.black":         opaque(p.bg),
        "terminal.ansi.bright_black":  opaque(p.ansi_bright_black),
        "terminal.ansi.dim_black":     opaque(p.ansi_dim_black),
        "terminal.ansi.red":           opaque(p.error),
        "terminal.ansi.bright_red":    opaque(p.ansi_bright_red),
        "terminal.ansi.dim_red":       opaque(p.ansi_dim_red),
        "terminal.ansi.green":         opaque(p.success),
        "terminal.ansi.bright_green":  opaque(p.ansi_bright_green),
        "terminal.ansi.dim_green":     opaque(p.ansi_dim_green),
        "terminal.ansi.yellow":        opaque(p.warning),
        "terminal.ansi.bright_yellow": opaque(p.ansi_bright_yellow),
        "terminal.ansi.dim_yellow":    opaque(p.ansi_dim_yellow),
        "terminal.ansi.blue":          opaque(p.ansi_blue),
        "terminal.ansi.bright_blue":   opaque(p.ansi_bright_blue),
        "terminal.ansi.dim_blue":      opaque(p.ansi_dim_blue),
        "terminal.ansi.magenta":       opaque(p.ansi_magenta),
        "terminal.ansi.bright_magenta":opaque(p.ansi_bright_magenta),
        "terminal.ansi.dim_magenta":   opaque(p.ansi_dim_magenta),
        "terminal.ansi.cyan":          opaque(p.ansi_cyan),
        "terminal.ansi.bright_cyan":   opaque(p.ansi_bright_cyan),
        "terminal.ansi.dim_cyan":      opaque(p.ansi_dim_cyan),
        "terminal.ansi.white":         opaque(p.text),
        "terminal.ansi.bright_white":  opaque(p.ansi_bright_white),
        "terminal.ansi.dim_white":     opaque(p.ansi_dim_white),

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
        "hidden.background":    opaque(p.diagnostic_muted_bg),
        "hidden.border":        opaque(p.panel),
        "hint":                 opaque(p.hint),
        "hint.background":      opaque(p.hint_bg),
        "hint.border":          opaque(p.hint_border),
        "ignored":              opaque(p.text_disabled),
        "ignored.background":   opaque(p.diagnostic_muted_bg),
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
        "unreachable.background": opaque(p.diagnostic_muted_bg),
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
    bg_grays = [p.player_bg_1, p.player_bg_2, p.player_bg_3, p.player_bg_4,
                p.player_bg_5, p.player_bg_6, p.player_bg_7, p.player_bg_8]
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
        "hint":                    syn(p.hint),
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
        "diff.plus":               syn(p.diff_term_plus),
        "diff.minus":              syn(p.diff_term_minus),
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
