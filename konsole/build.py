#!/usr/bin/env python3
"""Read ../ayu-graphite.toml and emit ./ayu-graphite.colorscheme (KDE Konsole).

Format mirrors KDE's official Breeze.colorscheme: an INI file with
[Background], [Foreground], [Color0]..[Color7] (each with Faint/Intense
siblings), and a [General] section. ANSI mapping matches terminal/build.py."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import emit
from palette import Palette, load_palette


def build_konsole(p: Palette) -> dict[str, dict[str, str]]:
    # Konsole's three rows are the palette's three ANSI rows verbatim:
    # Color<n> = normal, Color<n>Intense = bright (SGR 1), Color<n>Faint =
    # dim (SGR 2). Reading them straight off ansi_* is what keeps this in
    # step with terminal/build.py and Zed — the earlier hand-picked mix
    # reused `error`/`success` for both normal and intense (so bold red was
    # plain red) and borrowed syntax colors for Faint, which put grey in the
    # yellow slot and orange in the magenta slot.
    normal = [
        p.ansi_black, p.ansi_red, p.ansi_green, p.ansi_yellow,
        p.ansi_blue, p.ansi_magenta, p.ansi_cyan, p.ansi_white,
    ]
    intense = [
        p.ansi_bright_black, p.ansi_bright_red, p.ansi_bright_green,
        p.ansi_bright_yellow, p.ansi_bright_blue, p.ansi_bright_magenta,
        p.ansi_bright_cyan, p.ansi_bright_white,
    ]
    faint = [
        p.ansi_dim_black, p.ansi_dim_red, p.ansi_dim_green, p.ansi_dim_yellow,
        p.ansi_dim_blue, p.ansi_dim_magenta, p.ansi_dim_cyan, p.ansi_dim_white,
    ]

    sections: dict[str, dict[str, str]] = {
        "Background":          {"Color": emit.rgb_csv(p.bg)},
        "BackgroundFaint":     {"Color": emit.rgb_csv(p.ansi_dim_black)},
        "BackgroundIntense":   {"Color": emit.rgb_csv(p.bg)},
        "Foreground":          {"Color": emit.rgb_csv(p.text)},
        "ForegroundFaint":     {"Color": emit.rgb_csv(p.ansi_dim_white)},
        "ForegroundIntense":   {"Color": emit.rgb_csv(p.ansi_bright_white)},
    }
    for i in range(8):
        sections[f"Color{i}"]        = {"Color": emit.rgb_csv(normal[i])}
        sections[f"Color{i}Faint"]   = {"Color": emit.rgb_csv(faint[i])}
        sections[f"Color{i}Intense"] = {"Color": emit.rgb_csv(intense[i])}

    sections["General"] = {
        "Description": "Ayu Graphite",
        "Opacity":     "1",
        "Wallpaper":   "",
    }
    return sections


def main() -> None:
    emit.write_text(emit.beside(__file__, "ayu-graphite.colorscheme"),
                    emit.render_ini(build_konsole(load_palette())))


if __name__ == "__main__":
    main()
