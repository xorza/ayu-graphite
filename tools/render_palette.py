"""Render ayu-graphite.toml as a PNG swatch sheet.

The primitives are drawn as the grid they are: one column per hue, one row per
tint. A row is one perceived brightness, so the number under each row label is
L**, not a luminance."""
import os
import re
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from color import contrast, hk_lightness
from palette import load_source

OUT = os.path.join(ROOT, "palette.png")

CELL_W = 148
CELL_H = 66
GUTTER = 96
PAD = 18
GAP = 6
HEADER_H = 40
LABEL_H = 22


def ink_for(bg_hex):
    """Whichever of black or white actually reads on this swatch. A fixed
    luminance threshold picks wrong on saturated colors, which look brighter
    than they measure."""
    return ("#000000" if contrast("#000000", bg_hex) > contrast("#ffffff", bg_hex)
            else "#ffffff")


def load_font(size, bold=False):
    candidates = [
        "/usr/share/fonts/TTF/JetBrainsMonoNerdFontMono-Regular.ttf",
        "/usr/share/fonts/TTF/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/System/Library/Fonts/SFNSMono.ttf",
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Supplemental/Menlo.ttc",
        "/Library/Fonts/Menlo.ttc",
    ]
    if bold:
        candidates = [
            "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
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


class Ladder:
    """The chromatic primitives arranged as hue x tint, plus the neutral ramp.

    Hue order follows the file. Tint order is derived from the colors, so a new
    tint slots itself in by brightness without touching this module."""

    def __init__(self, primitives):
        self.neutrals = [(k, v) for k, v in primitives.items()
                         if k in ("black", "white") or k.startswith("gray")]
        self.neutrals.sort(key=lambda kv: hk_lightness(kv[1]))
        self.cells = {}
        self.hues = []
        by_tint = {}
        for key, value in primitives.items():
            m = re.fullmatch(r"([a-z]+)_([a-z]+)", key)
            if not m:
                continue
            hue, tint = m.groups()
            if hue not in self.hues:
                self.hues.append(hue)
            self.cells[(hue, tint)] = value
            by_tint.setdefault(tint, []).append(hk_lightness(value))
        self.tints = sorted(by_tint, key=lambda t: -sum(by_tint[t]) / len(by_tint[t]))
        self.brightness = {t: sum(v) / len(v) for t, v in by_tint.items()}

    @property
    def width(self):
        return GUTTER + len(self.hues) * (CELL_W + GAP) - GAP + 2 * PAD

    @property
    def height(self):
        return (HEADER_H + LABEL_H + len(self.tints) * (CELL_H + GAP) - GAP
                + PAD + CELL_H + LABEL_H)


class Sheet:
    """The chrome the sheet itself is painted in, taken from the palette so
    there is no second definition of these colors."""

    def __init__(self, p):
        self.bg, self.fg, self.dim = p.bg, p.text, p.text_muted


def draw_cell(draw, box, color, token, fonts):
    x0, y0 = box
    draw.rectangle([x0, y0, x0 + CELL_W, y0 + CELL_H], fill=color,
                   outline="#000000")
    ink = ink_for(color)
    draw.text((x0 + 7, y0 + 6), token, fill=ink, font=fonts["name"])
    draw.text((x0 + 7, y0 + CELL_H - 20), color, fill=ink, font=fonts["hex"])


def draw_ladder(draw, ladder, sheet, top, fonts):
    draw.text((PAD, top + 8), "primitives — hue x tint", fill=sheet.fg,
              font=fonts["header"])
    y = top + HEADER_H
    for col, hue in enumerate(ladder.hues):
        x = PAD + GUTTER + col * (CELL_W + GAP)
        draw.text((x + 7, y + 4), hue, fill=sheet.dim, font=fonts["label"])
    y += LABEL_H
    for row, tint in enumerate(ladder.tints):
        cy = y + row * (CELL_H + GAP)
        draw.text((PAD, cy + 18), tint, fill=sheet.fg, font=fonts["label"])
        draw.text((PAD, cy + 36), f"L** {ladder.brightness[tint]:.1f}",
                  fill=sheet.dim, font=fonts["hex"])
        for col, hue in enumerate(ladder.hues):
            x = PAD + GUTTER + col * (CELL_W + GAP)
            draw_cell(draw, (x, cy), ladder.cells[(hue, tint)],
                      f"{hue}_{tint}", fonts)
    y += len(ladder.tints) * (CELL_H + GAP) - GAP + PAD
    draw.text((PAD, y + 4), "neutrals", fill=sheet.dim, font=fonts["label"])
    y += LABEL_H
    span = len(ladder.hues) * (CELL_W + GAP) - GAP
    step = span / len(ladder.neutrals)
    for i, (token, color) in enumerate(ladder.neutrals):
        x = PAD + GUTTER + i * step
        draw.rectangle([x, y, x + step - 2, y + CELL_H], fill=color,
                       outline="#000000")
        ink = ink_for(color)
        draw.text((x + 6, y + 6), token.replace("gray_", ""), fill=ink,
                  font=fonts["hex"])
        draw.text((x + 6, y + CELL_H - 18), color, fill=ink, font=fonts["hex"])
    return y + CELL_H


def draw_semantic(draw, items, sheet, top, cols, fonts):
    draw.text((PAD, top + 8), "semantic", fill=sheet.fg, font=fonts["header"])
    y = top + HEADER_H
    for idx, (token, color) in enumerate(items):
        x = PAD + (idx % cols) * (CELL_W + GAP)
        cy = y + (idx // cols) * (CELL_H + GAP)
        draw_cell(draw, (x, cy), color, token, fonts)
    rows = (len(items) + cols - 1) // cols
    return y + rows * (CELL_H + GAP) - GAP


def main():
    src = load_source()
    semantic = list(src.palette.as_dict().items())

    ladder = Ladder(src.primitives)
    sheet = Sheet(src.palette)
    width = ladder.width
    cols = max(1, (width - 2 * PAD + GAP) // (CELL_W + GAP))
    sem_rows = (len(semantic) + cols - 1) // cols
    height = (PAD + ladder.height + PAD * 2
              + HEADER_H + sem_rows * (CELL_H + GAP) - GAP + PAD)

    img = Image.new("RGB", (width, height), sheet.bg)
    draw = ImageDraw.Draw(img)
    fonts = {"name": load_font(12), "hex": load_font(11),
             "label": load_font(13), "header": load_font(17, bold=True)}

    y = draw_ladder(draw, ladder, sheet, PAD, fonts)
    draw_semantic(draw, semantic, sheet, y + PAD * 2, cols, fonts)

    img.save(OUT)
    print(f"wrote {OUT} ({width}x{height})")


if __name__ == "__main__":
    main()
