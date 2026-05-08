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
    elem_selected: str
    title_bar: str
    title_bar_inactive: str
    terminal_bg: str

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

    def as_dict(self) -> dict:
        return dataclasses.asdict(self)


def load_palette(path: str) -> Palette:
    with open(path, "rb") as f:
        data = tomllib.load(f)
    flat = {k: v for section in data.values() for k, v in section.items()}
    return Palette(**flat)
