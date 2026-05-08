"""Shared palette dataclass + TOML loader.

Single source of truth for the shape of ayu-mirage.toml. Every target builder
imports from here so adding a token is a one-file edit instead of a five-file
ritual."""
import dataclasses
try:
    import tomllib  # py311+
except ModuleNotFoundError:
    import tomli as tomllib  # pip install -r requirements.txt
from dataclasses import dataclass


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
    success: str
    warning: str
    error: str
    hint: str

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

    line_number: str
    line_number_active: str
    line_number_hover: str
    scrollbar_thumb: str
    drop_target: str
    search_highlight: str
    search_match_active: str

    ansi_blue: str
    ansi_magenta: str
    ansi_cyan: str
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


def load_palette(path: str) -> Palette:
    """Resolve [semantic] string refs against [primitives] hex values.

    A semantic value is either a literal `#rrggbb` (escape hatch) or the name
    of a key in [primitives]. Anything that doesn't resolve is a hard error —
    we'd rather break the build than silently render a typo as a missing key
    fallback elsewhere."""
    with open(path, "rb") as f:
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
    return Palette(**resolved)
