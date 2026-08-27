"""Color math the tools share: WCAG contrast, APCA Lc, and perceived lightness.

Three models, because each answers a question the others cannot. WCAG relative
luminance is what the theme's rules are written against. APCA Lc is what those
ratios actually mean on a self-lit dark display. Fairchild-Pirrotta L** is how
bright a color looks once its chroma is folded in, which is the axis the
palette's rows are level on."""
from math import atan2, degrees, hypot, radians, sin


def channels(hex6: str) -> list[float]:
    h = hex6.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def luminance(hex6: str) -> float:
    ch = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
          for c in channels(hex6)]
    return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]


def contrast(a: str, b: str) -> float:
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


# APCA 0.1.9 W3 constants. Its transfer curve is a plain 2.4 power, not the
# WCAG piecewise one, and its luminance coefficients carry more digits — so it
# needs its own luminance rather than reusing the one above. For scale: Lc 30
# is the floor for any text at all, 45 for headline weight, 60 for non-body
# content text, 75-90 for columns of body text.
APCA_COEF = (0.2126729, 0.7151522, 0.0721750)
APCA_TEXT, APCA_BG = 0.57, 0.56
APCA_REV_TEXT, APCA_REV_BG = 0.62, 0.65
APCA_BLACK_CLIP, APCA_BLACK_THRESHOLD = 1.414, 0.022
APCA_SCALE, APCA_OFFSET, APCA_CLAMP = 1.14, 0.027, 0.1


def apca_luminance(hex6: str) -> float:
    y = sum(c * v ** 2.4 for c, v in zip(APCA_COEF, channels(hex6)))
    if y < APCA_BLACK_THRESHOLD:
        return y + (APCA_BLACK_THRESHOLD - y) ** APCA_BLACK_CLIP
    return y


def apca(fg: str, bg: str) -> float:
    """Lc for this pair. The sign is polarity; the reports take the magnitude."""
    yt, yb = apca_luminance(fg), apca_luminance(bg)
    if yb > yt:
        s = (yb ** APCA_BG - yt ** APCA_TEXT) * APCA_SCALE
    else:
        s = (yb ** APCA_REV_BG - yt ** APCA_REV_TEXT) * APCA_SCALE
    if abs(s) < APCA_CLAMP:
        return 0.0
    return (s - APCA_OFFSET) * 100 if s > 0 else (s + APCA_OFFSET) * 100


D65 = (0.95047, 1.0, 1.08883)


def lch(hex6: str) -> tuple[float, float, float]:
    """CIELAB lightness, chroma and hue angle under D65."""
    r, g, b = (c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
               for c in channels(hex6))
    xyz = (0.4124564 * r + 0.3575761 * g + 0.1804375 * b,
           0.2126729 * r + 0.7151522 * g + 0.0721750 * b,
           0.0193339 * r + 0.1191920 * g + 0.9503041 * b)

    def f(t):
        return t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116

    fx, fy, fz = (f(v / w) for v, w in zip(xyz, D65))
    a, bb = 500 * (fx - fy), 200 * (fy - fz)
    return 116 * fy - 16, hypot(a, bb), degrees(atan2(bb, a)) % 360


def hk_lightness(hex6: str) -> float:
    """How bright the color looks, not how much light it emits.

    Fairchild-Pirrotta. At one luminance a saturated color reads brighter than
    a dull one — the Helmholtz-Kohlrausch effect — so CIELAB L* alone predicts
    a level row that the eye sees as uneven."""
    lightness, chroma, hue = lch(hex6)
    gain = 0.116 * abs(sin(radians((hue - 90) / 2))) + 0.085
    return lightness + (2.5 - 0.025 * lightness) * gain * chroma
