"""Shared palette dataclass + TOML loader.

Single source of truth for the shape of ayu-graphite.toml. Every target builder
imports from here, so a new token is one edit instead of one per target."""
import dataclasses
import os
try:
    import tomllib  # py311+
except ModuleNotFoundError:
    import tomli as tomllib  # pip install -r requirements.txt
from dataclasses import dataclass

TOML = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    "ayu-graphite.toml")


@dataclass
class Palette:
    bg: str
    panel: str
    surface: str
    elem: str
    elem_hover: str
    elem_active: str
    elem_disabled: str
    title_bar: str
    title_bar_inactive: str
    overlay_black: str

    border: str
    border_focused: str

    text: str
    text_muted: str
    text_disabled: str

    accent: str
    accent_hover: str
    accent_active: str
    success: str
    warning: str
    error: str
    hint: str

    on_accent: str
    on_accent_muted: str

    selection_bg: str
    selection_fg: str

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
    diagnostic_muted_bg: str

    diff_term_plus: str
    diff_term_minus: str
    diff_word_plus: str
    diff_word_minus: str

    line_number: str
    line_number_active: str
    line_number_hover: str
    scrollbar_thumb: str
    drop_target: str
    search_highlight: str
    search_match_active: str

    ansi_black: str
    ansi_red: str
    ansi_green: str
    ansi_yellow: str
    ansi_blue: str
    ansi_magenta: str
    ansi_cyan: str
    ansi_white: str
    ansi_bright_black: str
    ansi_dim_black: str
    ansi_bright_red: str
    ansi_dim_red: str
    ansi_bright_green: str
    ansi_dim_green: str
    ansi_bright_yellow: str
    ansi_dim_yellow: str
    ansi_bright_blue: str
    ansi_dim_blue: str
    ansi_bright_magenta: str
    ansi_dim_magenta: str
    ansi_bright_cyan: str
    ansi_dim_cyan: str
    ansi_bright_white: str
    ansi_dim_white: str

    player_bg: str

    chat_check: str
    chat_msg_bg: str

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

    def as_dict(self) -> dict:
        return dataclasses.asdict(self)


@dataclass
class Source:
    """The whole file, for a reader that needs the names as well as the values:
    the audit checks the tint rows the primitives are named by, and the two RON
    targets print the ref each role resolved through."""
    primitives: dict[str, str]
    semantic: dict[str, str]
    palette: Palette


def load_source() -> Source:
    """Read ayu-graphite.toml and resolve [semantic] refs against [primitives].

    A semantic value is either a literal `#rrggbb` (escape hatch) or the name
    of a key in [primitives]. Anything that doesn't resolve is a hard error —
    we'd rather break the build than silently render a typo as a missing key
    fallback elsewhere."""
    with open(TOML, "rb") as f:
        data = tomllib.load(f)
    primitives = data["primitives"]
    semantic = data["semantic"]
    resolved = {}
    for key, value in semantic.items():
        if value.startswith("#"):
            resolved[key] = value
        elif value in primitives:
            resolved[key] = primitives[value]
        else:
            raise KeyError(
                f"semantic.{key} = {value!r} is neither a hex literal nor a "
                f"primitive name. Available primitives: {sorted(primitives)}"
            )
    return Source(primitives, semantic, Palette(**resolved))


def load_palette() -> Palette:
    """Just the roles, which is all a target builder reads."""
    return load_source().palette
