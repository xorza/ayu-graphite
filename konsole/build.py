#!/usr/bin/env python3
"""Read ../ayu-mirage.toml and emit ./ayu-mirage.colorscheme (KDE Konsole).

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
    # ANSI 0..7 (normal) + Intense (bright) mirror terminal/build.py.
    # Faint is a dimmed variant Konsole uses for SGR 2 — pick muted siblings.
    # Background uses p.bg (matches Zed's integrated terminal) instead of
    # p.terminal_bg (which is the darker macOS Terminal.app value).
    normal = [
        p.bg,             # 0 black
        p.error,          # 1 red
        p.success,        # 2 green
        p.warning,        # 3 yellow
        p.ansi_blue,      # 4 blue
        p.syn_number,     # 5 magenta
        p.ansi_cyan,      # 6 cyan
        p.text,           # 7 white
    ]
    intense = [
        p.text_disabled,  # 8  bright black
        p.error,          # 9  bright red
        p.success,        # 10 bright green
        p.syn_function,   # 11 bright yellow
        p.accent,         # 12 bright blue
        p.ansi_magenta,   # 13 bright magenta
        p.syn_string_regex, # 14 bright cyan
        p.ansi_bright_white,  # 15 bright white
    ]
    faint = [
        p.bg,
        p.deleted,
        p.created,
        p.syn_doc,
        p.syn_predictive,
        p.syn_keyword,
        p.syn_string_special,
        p.text_muted,
    ]

    sections: dict[str, dict[str, str]] = {
        "Background":          {"Color": rgb(p.bg)},
        "BackgroundFaint":     {"Color": rgb(p.terminal_bg)},
        "BackgroundIntense":   {"Color": rgb(p.bg)},
        "Foreground":          {"Color": rgb(p.text)},
        "ForegroundFaint":     {"Color": rgb(p.text_muted)},
        "ForegroundIntense":   {"Color": rgb(p.accent)},
    }
    for i in range(8):
        sections[f"Color{i}"]        = {"Color": rgb(normal[i])}
        sections[f"Color{i}Faint"]   = {"Color": rgb(faint[i])}
        sections[f"Color{i}Intense"] = {"Color": rgb(intense[i])}

    sections["General"] = {
        "Description": "Ayu Mirage High Contrast",
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
    p = load_palette(os.path.join(repo, "ayu-mirage.toml"))
    out = os.path.join(here, "ayu-mirage.colorscheme")
    with open(out, "w") as f:
        f.write(render(build_konsole(p)))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
