"""Color math the repo shares: WCAG contrast, APCA Lc, Oklab, and perceived
lightness.

Four models, because each answers a question the others cannot. WCAG relative
luminance is what the theme's rules are written against. APCA Lc is what those
ratios actually mean on a self-lit dark display. Oklab is where two colors are
compared for how far apart they look. Fairchild-Pirrotta L** is how bright a
color looks once its chroma is folded in, which is the axis the palette's rows
are level on."""
from math import atan2, degrees, hypot, radians, sin


def channels(hex6: str) -> list[float]:
    h = hex6.lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def to_linear(c: float) -> float:
    """One sRGB channel, decoded. WCAG puts the knee at 0.03928 and the sRGB
    standard at 0.04045; no 8-bit channel value falls between the two, so one
    function serves every model here."""
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def linear(hex6: str) -> tuple[float, float, float]:
    r, g, b = (to_linear(c) for c in channels(hex6))
    return r, g, b


def luminance(hex6: str) -> float:
    r, g, b = linear(hex6)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a: str, b: str) -> float:
    la, lb = luminance(a), luminance(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def encode(c: float) -> float:
    """One linear channel, sRGB-encoded. The inverse of `to_linear`."""
    return 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055


def hex_from_linear(rgb: tuple[float, float, float]) -> str:
    """The nearest 8-bit triple. A channel a hair outside the gamut is clamped
    onto its edge first, so a solver that lands on the boundary still rounds."""
    return "#%02x%02x%02x" % tuple(
        max(0, min(255, round(encode(max(0.0, min(1.0, c))) * 255)))
        for c in rgb)


def grey(value: float) -> str:
    """The neutral of linear value `value`, as a hex triple. A neutral's three
    channels are equal, so its relative luminance is that same number."""
    return hex_from_linear((value, value, value))


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
    return lch_linear(linear(hex6))


def lch_linear(rgb: tuple[float, float, float]) -> tuple[float, float, float]:
    r, g, b = rgb
    xyz = (0.4124564 * r + 0.3575761 * g + 0.1804375 * b,
           0.2126729 * r + 0.7151522 * g + 0.0721750 * b,
           0.0193339 * r + 0.1191920 * g + 0.9503041 * b)

    def f(t):
        return t ** (1 / 3) if t > 216 / 24389 else (24389 / 27 * t + 16) / 116

    fx, fy, fz = (f(v / w) for v, w in zip(xyz, D65))
    a, bb = 500 * (fx - fy), 200 * (fy - fz)
    return 116 * fy - 16, hypot(a, bb), degrees(atan2(bb, a)) % 360


def oklab(hex6: str) -> tuple[float, float, float]:
    """Oklab lightness and the two opponent axes. Euclidean distance here is
    about as close to perceived difference as three numbers get."""
    r, g, b = linear(hex6)
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_, m_, s_ = l ** (1 / 3), m ** (1 / 3), s ** (1 / 3)
    return (
        0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
        1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
        0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_,
    )


def oklab_to_linear(lightness: float, a: float, b: float
                    ) -> tuple[float, float, float]:
    """The inverse of `oklab`, unclamped: a channel outside 0..1 says the color
    is outside the gamut, which is what a gamut search reads off it."""
    l_ = lightness + 0.3963377774 * a + 0.2158037573 * b
    m_ = lightness - 0.1055613458 * a - 0.0638541728 * b
    s_ = lightness - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    return (
        4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
        -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
        -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s,
    )


def oklch(hex6: str) -> tuple[float, float, float]:
    """Oklab lightness, chroma and hue angle in degrees."""
    lightness, a, b = oklab(hex6)
    return lightness, hypot(a, b), degrees(atan2(b, a)) % 360


def hk_lightness(hex6: str) -> float:
    """How bright the color looks, not how much light it emits.

    Fairchild-Pirrotta. At one luminance a saturated color reads brighter than
    a dull one — the Helmholtz-Kohlrausch effect — so CIELAB L* alone predicts
    a level row that the eye sees as uneven."""
    return hk_lightness_linear(linear(hex6))


def hk_lightness_linear(rgb: tuple[float, float, float]) -> float:
    lightness, chroma, hue = lch_linear(rgb)
    gain = 0.116 * abs(sin(radians((hue - 90) / 2))) + 0.085
    return lightness + (2.5 - 0.025 * lightness) * gain * chroma
