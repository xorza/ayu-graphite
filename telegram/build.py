#!/usr/bin/env python3
"""Read ../ayu-graphite.toml and emit ./ayu-graphite.tdesktop-theme.

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
        # Drives toggled-ON switch tracks, slider active bars, and other
        # "active" fills. Upstream night uses the accent blue here; routing
        # through panel made on/off states indistinguishable.
        ("windowBgActive",            p.accent),
        # Unchecked checkbox/radio/switch frame. Default #4f6276 reads cool-
        # blue against our warm greys; map to a neutral text-muted instead.
        ("checkboxFg",                p.text_muted),
        ("windowFg",                  p.text),
        ("windowFgOver",              p.text),
        ("windowSubTextFg",           p.text_muted),
        ("windowSubTextFgOver",       p.text_muted),
        ("windowBoldFg",              p.text),
        ("windowBoldFgOver",          p.text),
        ("windowFgActive",            p.text),
        ("windowActiveTextFg",        p.ansi_cyan),

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
        ("dialogsUnreadBg",           p.ansi_cyan),
        ("dialogsUnreadBgMuted",      p.text_muted),
        ("dialogsUnreadFg",           p.bg),
        ("dialogsUnreadFgActive",     p.bg),

        ("msgInBg",                   p.chat_msg_bg),
        ("msgInBgSelected",           p.elem_active),
        ("msgOutBg",                  p.chat_msg_bg),
        ("msgOutBgSelected",          p.elem_active),
        ("msgInDateFg",               p.text_muted),
        ("msgOutDateFg",              p.text_muted),
        ("msgInServiceFg",            p.ansi_cyan),
        ("msgOutServiceFg",           p.ansi_cyan),
        ("msgInMonoFg",               p.syn_string),
        ("msgOutMonoFg",              p.syn_string),
        ("msgInReplyBarColor",        p.ansi_cyan),
        ("msgOutReplyBarColor",       p.syn_function),
        ("msgServiceBg",              p.panel),
        ("msgServiceFg",              p.text_muted),

        # Bubble drop-shadows — upstream night palette tints these greenish/blue.
        # Map all four to bg so any shadow that does render reads as neutral dark.
        ("msgInShadow",               p.elem_active),
        ("msgInShadowSelected",       p.elem_active),
        ("msgOutShadow",              p.elem_active),
        ("msgOutShadowSelected",      p.elem_active),

        # "Unread messages" divider in chat view — defaults render near-white.
        ("historyUnreadBarBg",        p.panel),
        ("historyUnreadBarBorder",    p.border),
        ("historyUnreadBarFg",        p.ansi_cyan),

        ("activeButtonBg",            p.elem_active),
        ("activeButtonBgOver",        p.ansi_dim_black),
        ("activeButtonFg",            p.accent),
        ("activeButtonFgOver",        p.accent),
        ("activeButtonSecondaryFg",       p.accent),
        ("activeButtonSecondaryFgOver",   p.accent),
        ("lightButtonBg",             p.elem),
        ("lightButtonBgOver",         p.elem_hover),
        ("lightButtonFg",             p.ansi_cyan),
        ("lightButtonFgOver",         p.ansi_cyan),

        ("scrollBg",                  p.panel),
        ("scrollBgOver",              p.elem_hover),
        ("scrollBarBg",               p.text_muted),
        ("scrollBarBgOver",           p.text),

        ("boxTextFgGood",             p.success),

        # Outgoing message check ticks (✓ / ✓✓) — warm yellow pops more than
        # green against the bubble bg without competing with status colors.
        ("historyOutIconFg",          p.chat_check),
        ("historyOutIconFgSelected",  p.chat_check),
        ("historySendingOutIconFg",   p.chat_check),
        ("historyIconFgInverted",     p.chat_check),
        ("dialogsSentIconFg",         p.chat_check),
        ("dialogsSentIconFgOver",     p.chat_check),
        ("dialogsSentIconFgActive",   p.chat_check),
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
        ("mentionFg",                 p.ansi_cyan),

        # Forward / compose / reply bar backgrounds — Telegram falls back to a
        # bluish-cyan night default for these when not set explicitly.
        ("topBarBg",                          p.panel),
        ("historyComposeAreaBg",              p.panel),
        ("historyComposeAreaFg",              p.text),
        ("historyComposeAreaFgService",       p.text_muted),
        ("historyReplyBg",                    p.panel),
        ("historyComposeButtonBg",            p.elem),
        ("historyComposeButtonBgOver",        p.elem_hover),
        ("historyComposeButtonBgRipple",      p.elem_active),
        ("dialogsForwardBg",                  p.panel),
        ("dialogsForwardFg",                  p.text),
        ("historyForwardChooseBg",            p.panel),
        ("historyForwardChooseFg",            p.text),
        ("searchedBarBg",                     p.panel),
        ("searchedBarFg",                     p.text_muted),
        ("reportSpamBg",                      p.panel),
        ("reportSpamFg",                      p.text),

        # In-bubble file download-circle bg. The msgFile{1..4}* slots only
        # drive the shared-Files-tab thumbnails; in-chat file circles route
        # through msgFile{In,Out}Bg{,Over,Selected} (verified against
        # tdesktop's history_view_document.cpp). Without these the chat falls
        # back to upstream blue defaults. Selected variants alias to the
        # non-selected so multi-select doesn't shift the color.
        ("msgFileInBg",                       p.accent),
        ("msgFileInBgOver",                   p.accent),
        ("msgFileInBgSelected",               "msgFileInBg"),
        ("msgFileOutBg",                      p.accent),
        ("msgFileOutBgOver",                  p.accent),
        ("msgFileOutBgSelected",              "msgFileOutBg"),

        # Shared-files-tab thumbnail parity (msgFile1..4 slots), in case the
        # user lands there. Upstream darkens the selected variant.
        ("msgFile1BgSelected",                "msgFile1Bg"),
        ("msgFile2BgSelected",                "msgFile2Bg"),
        ("msgFile3BgSelected",                "msgFile3Bg"),
        ("msgFile4BgSelected",                "msgFile4Bg"),

        # Voice-message waveform — upstream tints incoming/outgoing different
        # blues. Match outgoing to incoming so direction doesn't shift hue.
        ("msgWaveformInActive",            p.accent),
        ("msgWaveformInActiveSelected",    p.text),
        ("msgWaveformInInactive",          p.text_muted),
        ("msgWaveformInInactiveSelected",  p.text),
        ("msgWaveformOutActive",           "msgWaveformInActive"),
        ("msgWaveformOutActiveSelected",   "msgWaveformInActiveSelected"),
        ("msgWaveformOutInactive",         "msgWaveformInInactive"),
        ("msgWaveformOutInactiveSelected", "msgWaveformInInactiveSelected"),

        # Selection overlays — translucent blue layers Telegram composites on
        # top of selected media. Zeroed so colors don't shift on selection.
        ("msgSelectOverlay",                  "#00000000"),
        ("msgStickerOverlay",                 "#00000000"),
        ("overviewPhotoSelectOverlay",        "#00000000"),
    ]
    lines = ["// Ayu Graphite — Telegram Desktop palette", ""]
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
    p = load_palette(os.path.join(repo, "ayu-graphite.toml"))
    palette_text = build_telegram(p)
    write_telegram_zip(os.path.join(here, "ayu-graphite.tdesktop-theme"),
                       palette_text, p.bg)
    # Mirror the same palette text uncompressed for easy inspection / grep.
    plain = os.path.join(here, "ayu-graphite.tdesktop-theme.txt")
    with open(plain, "w") as f:
        f.write(palette_text)


if __name__ == "__main__":
    main()
