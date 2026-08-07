#!/usr/bin/env python3
"""Read ../ayu-graphite.toml and emit ./ayu-graphite.colorscheme (KDE Konsole).

Format mirrors KDE's official Breeze.colorscheme: an INI file with
[Background], [Foreground], [Color0]..[Color7] (each with Faint/Intense
siblings), and a [General] section. ANSI mapping matches terminal/build.py."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from palette import Palette, load_palette


def rgb(hex6: str) -> str:
    h = hex6.lstrip("#")
    return f"{int(h[0:2], 16)},{int(h[2:4], 16)},{int(h[4:6], 16)}"


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
        "Background":          {"Color": rgb(p.bg)},
        "BackgroundFaint":     {"Color": rgb(p.ansi_dim_black)},
        "BackgroundIntense":   {"Color": rgb(p.bg)},
        "Foreground":          {"Color": rgb(p.text)},
        "ForegroundFaint":     {"Color": rgb(p.ansi_dim_white)},
        "ForegroundIntense":   {"Color": rgb(p.ansi_bright_white)},
    }
    for i in range(8):
        sections[f"Color{i}"]        = {"Color": rgb(normal[i])}
        sections[f"Color{i}Faint"]   = {"Color": rgb(faint[i])}
        sections[f"Color{i}Intense"] = {"Color": rgb(intense[i])}

    sections["General"] = {
        "Description": "Ayu Graphite",
        "Opacity":     "1",
        "Wallpaper":   "",
    }
    return sections


def render(scheme: dict[str, dict[str, str]]) -> str:
    out = []
    for section, kvs in scheme.items():
        out.append(f"[{section}]")
        for k, v in kvs.items():
            out.append(f"{k}={v}")
        out.append("")
    return "\n".join(out)


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.dirname(here)
    p = load_palette(os.path.join(repo, "ayu-graphite.toml"))
    out = os.path.join(here, "ayu-graphite.colorscheme")
    with open(out, "w") as f:
        f.write(render(build_konsole(p)))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
