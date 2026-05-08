"""Render ayu-mirage.toml as a PNG swatch sheet grouped by section."""
import os
import sys
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOML = os.path.join(ROOT, "ayu-mirage.toml")
OUT = os.path.join(ROOT, "palette.png")

SWATCH_W = 220
SWATCH_H = 64
COLS = 4
PAD = 16
HEADER_H = 32
SHEET_BG = "#1f1e1d"
SHEET_FG = "#e2dfd3"
SHEET_DIM = "#878a8d"


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def luminance(rgb):
    def chan(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (chan(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ink_for(bg_hex):
    return "#000000" if luminance(hex_to_rgb(bg_hex)) > 0.45 else "#ffffff"


def load_font(size, bold=False):
    candidates = [
        "/System/Library/Fonts/SFNSMono.ttf",
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Supplemental/Menlo.ttc",
        "/Library/Fonts/Menlo.ttc",
    ]
    if bold:
        candidates = [
            "/System/Library/Fonts/SFNS.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
        ] + candidates
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                continue
    return ImageFont.load_default()


def main():
    with open(TOML, "rb") as f:
        data = tomllib.load(f)

    sections = [(name, list(items.items())) for name, items in data.items()]

    rows_per_section = [(len(items) + COLS - 1) // COLS for _, items in sections]
    total_rows = sum(rows_per_section)
    width = COLS * SWATCH_W + (COLS + 1) * PAD
    height = (
        PAD
        + sum(HEADER_H + rows * SWATCH_H + rows * PAD for rows in rows_per_section)
        + PAD
    )

    img = Image.new("RGB", (width, height), SHEET_BG)
    draw = ImageDraw.Draw(img)
    name_font = load_font(13)
    hex_font = load_font(12)
    header_font = load_font(16, bold=True)

    y = PAD
    for (section_name, items), n_rows in zip(sections, rows_per_section):
        draw.text((PAD, y + 6), section_name, fill=SHEET_FG, font=header_font)
        y += HEADER_H
        for idx, (token, color) in enumerate(items):
            col = idx % COLS
            row = idx // COLS
            x0 = PAD + col * (SWATCH_W + PAD)
            y0 = y + row * (SWATCH_H + PAD)
            draw.rectangle(
                [x0, y0, x0 + SWATCH_W, y0 + SWATCH_H],
                fill=color,
                outline="#000000",
            )
            ink = ink_for(color)
            draw.text((x0 + 8, y0 + 6), token, fill=ink, font=name_font)
            draw.text((x0 + 8, y0 + SWATCH_H - 22), color, fill=ink, font=hex_font)
        y += n_rows * SWATCH_H + n_rows * PAD

    img.save(OUT)
    print(f"wrote {OUT} ({width}x{height})")


if __name__ == "__main__":
    main()
