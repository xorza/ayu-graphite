#!/usr/bin/env python3
"""Read ../ayu-mirage.toml and emit ./ayu-mirage.tdesktop-theme.

The output is a zip archive (the .tdesktop-theme extension is what Telegram
expects) containing colors.tdesktop-theme + a small solid-color background.png
to override Telegram's default Star Wars chat wallpaper.
"""
import os
import struct
import sys
import zipfile
import zlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from palette import Palette, load_palette


def build_telegram(p: Palette) -> str:
    """Emit a .tdesktop-theme palette text. Telegram falls back to defaults for
    any constant we don't define, so we cover the visible ~50 keys."""
    pairs = [
        ("windowBg",                  p.bg),
        ("windowBgOver",              p.elem_hover),
        ("windowBgRipple",            p.elem_active),
        ("windowBgActive",            p.accent),
        ("windowFg",                  p.text),
        ("windowFgOver",              p.text),
        ("windowSubTextFg",           p.text_muted),
        ("windowSubTextFgOver",       p.text_muted),
        ("windowBoldFg",              p.text),
        ("windowBoldFgOver",          p.text),
        ("windowFgActive",            p.bg),
        ("windowActiveTextFg",        p.accent),

        ("sideBarBg",                 p.panel),
        ("sideBarBgActive",           p.elem_active),
        ("topBarBg",                  p.title_bar),

        ("titleBg",                   p.title_bar_inactive),
        ("titleBgActive",             p.title_bar),
        ("titleFg",                   p.text_muted),
        ("titleFgActive",             p.text),
        ("titleShadow",               p.bg),
        ("titleButtonBg",             p.title_bar),
        ("titleButtonFg",             p.text),
        ("titleButtonBgOver",         p.elem_hover),
        ("titleButtonFgOver",         p.text),

        ("dialogsBg",                 p.panel),
        ("dialogsBgOver",             p.elem_hover),
        ("dialogsBgActive",           p.elem_active),
        ("dialogsNameFg",             p.text),
        ("dialogsNameFgActive",       p.text),
        ("dialogsTextFg",             p.text_muted),
        ("dialogsTextFgActive",       p.text),
        ("dialogsDateFg",             p.text_muted),
        ("dialogsDateFgActive",       p.text_muted),
        ("dialogsUnreadBg",           p.accent),
        ("dialogsUnreadBgMuted",      p.text_muted),
        ("dialogsUnreadFg",           p.bg),
        ("dialogsUnreadFgActive",     p.bg),

        ("msgInBg",                   p.surface),
        ("msgInBgSelected",           p.elem_active),
        ("msgOutBg",                  p.elem),
        ("msgOutBgSelected",          p.elem_active),
        ("msgInDateFg",               p.text_muted),
        ("msgOutDateFg",              p.text_muted),
        ("msgInServiceFg",            p.accent),
        ("msgOutServiceFg",           p.accent),
        ("msgInMonoFg",               p.syn_string),
        ("msgOutMonoFg",              p.syn_string),
        ("msgInReplyBarColor",        p.accent),
        ("msgOutReplyBarColor",       p.syn_function),
        ("msgServiceBg",              p.panel),
        ("msgServiceFg",              p.text_muted),

        # "Unread messages" divider in chat view — defaults render near-white.
        ("historyUnreadBarBg",        p.panel),
        ("historyUnreadBarBorder",    p.border),
        ("historyUnreadBarFg",        p.accent),

        ("activeButtonBg",            p.accent),
        ("activeButtonBgOver",        p.accent),
        ("activeButtonFg",            p.bg),
        ("activeButtonFgOver",        p.bg),
        ("activeButtonSecondaryFg",       p.bg),
        ("activeButtonSecondaryFgOver",   p.bg),
        ("lightButtonBg",             p.elem),
        ("lightButtonBgOver",         p.elem_hover),
        ("lightButtonFg",             p.accent),
        ("lightButtonFgOver",         p.accent),

        ("scrollBg",                  p.panel),
        ("scrollBgOver",              p.elem_hover),
        ("scrollBarBg",               p.text_muted),
        ("scrollBarBgOver",           p.text),

        ("boxTextFgGood",             p.success),

        # Outgoing message check ticks (✓ / ✓✓) — lock to palette green so
        # bubble + chat-list match each other and the terminal's ANSI green.
        ("historyOutIconFg",          p.success),
        ("historyOutIconFgSelected",  p.success),
        ("historySendingOutIconFg",   p.success),
        ("historyIconFgInverted",     p.success),
        ("dialogsSentIconFg",         p.success),
        ("dialogsSentIconFgOver",     p.success),
        ("dialogsSentIconFgActive",   p.success),
        ("boxTextFgError",            p.error),
        ("activeLineFgError",         p.error),
        ("attentionButtonFg",         p.warning),

        # Dividers / separators / shadows — Telegram defaults these bright in
        # popup menus when undefined. Keep them subtle and dark.
        ("shadowFg",                  p.panel),
        ("windowShadowFg",            p.panel),
        ("windowShadowFgFallback",    p.panel),
        ("boxDividerBg",              p.panel),
        ("boxDividerFg",              p.elem),
        ("menuBg",                    p.panel),
        ("menuBgOver",                p.elem_hover),
        ("menuBgRipple",              p.elem_active),
        ("menuFg",                    p.text),
        ("menuFgDisabled",            p.text_muted),
        ("menuIconFg",                p.text_muted),
        ("menuIconFgOver",            p.text),
        ("menuSubmenuArrowFg",        p.text_muted),
        ("menuSeparatorFg",           p.elem),

        ("mentionBg",                 p.elem),
        ("mentionFg",                 p.accent),
    ]
    lines = ["// Ayu Mirage High Contrast — Telegram Desktop palette", ""]
    lines += [f"{k}: {v};" for k, v in pairs]
    return "\n".join(lines) + "\n"


def solid_png(hex_color: str, size: int = 8) -> bytes:
    """Tiny solid-color PNG (no Pillow). Telegram tiles/scales it as wallpaper."""
    h = hex_color.lstrip("#")
    rgb = bytes((int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)))

    def chunk(typ: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + typ + data
                + struct.pack(">I", zlib.crc32(typ + data) & 0xffffffff))

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)  # 8-bit RGB
    raw = b"".join(b"\x00" + rgb * size for _ in range(size))  # filter byte + row
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


def write_telegram_zip(path: str, palette_text: str, bg_hex: str) -> None:
    # Fixed timestamp so identical inputs produce byte-identical archives —
    # otherwise zipfile stamps each entry with `now` and git sees a diff on
    # every build.
    epoch = (1980, 1, 1, 0, 0, 0)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in (("colors.tdesktop-theme", palette_text.encode()),
                           ("background.png",        solid_png(bg_hex))):
            info = zipfile.ZipInfo(name, date_time=epoch)
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data)
    print(f"wrote {path}")


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.dirname(here)
    p = load_palette(os.path.join(repo, "ayu-mirage.toml"))
    write_telegram_zip(os.path.join(here, "ayu-mirage.tdesktop-theme"),
                       build_telegram(p), p.bg)


if __name__ == "__main__":
    main()
