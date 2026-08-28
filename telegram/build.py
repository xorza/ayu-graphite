#!/usr/bin/env python3
"""Read ../ayu-graphite.toml and emit ./ayu-graphite.tdesktop-theme.

The output is a zip archive (the .tdesktop-theme extension is what Telegram
expects) containing colors.tdesktop-theme + a small solid-color background.png
to override Telegram's default Star Wars chat wallpaper.
"""
import io
import os
import struct
import sys
import zipfile
import zlib
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import emit
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
        # Ink for everything drawn on windowBgActive — the "Update Telegram"
        # button in the chat list is the loudest of them. Upstream pairs a
        # white fg with a mid-blue fill; our accent is a light blue, and the
        # inherited `text` sits on it at 1.28:1.
        ("windowFgActive",            p.on_accent),
        ("windowActiveTextFg",        p.accent),

        ("sideBarBg",                 p.panel),
        ("sideBarBgActive",           p.selection_bg),
        ("topBarBg",                  p.panel),

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
        ("dialogsBgActive",           p.selection_bg),
        ("dialogsNameFg",             p.text),
        ("dialogsNameFgActive",       p.selection_fg),
        ("dialogsTextFg",             p.text_muted),
        ("dialogsTextFgActive",       p.selection_fg),
        ("dialogsDateFg",             p.text_muted),
        ("dialogsDateFgActive",       p.text_muted),
        ("dialogsUnreadBg",           p.accent),
        ("dialogsUnreadBgOver",       p.accent),
        ("dialogsUnreadBgMuted",      p.text_muted),
        ("dialogsUnreadFg",           p.on_accent),
        # Upstream derives the badge fill on a selected row from
        # dialogsTextFgActive; left implicit that tracks whatever the row's
        # text colour happens to be, which is a light fill under light ink.
        ("dialogsUnreadBgActive",     p.accent),
        ("dialogsUnreadBgMutedActive", p.text_muted),
        ("dialogsUnreadFgActive",     p.on_accent),

        ("msgInBg",                   p.chat_msg_bg),
        ("msgInBgSelected",           p.selection_bg),
        ("msgOutBg",                  p.chat_msg_bg),
        ("msgOutBgSelected",          p.selection_bg),
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

        # Bubble drop-shadows — upstream night palette tints these greenish/blue.
        # Map all four to bg so any shadow that does render reads as neutral dark.
        ("msgInShadow",               p.bg),
        ("msgInShadowSelected",       p.bg),
        ("msgOutShadow",              p.bg),
        ("msgOutShadowSelected",      p.bg),

        # "Unread messages" divider in chat view — defaults render near-white.
        ("historyUnreadBarBg",        p.panel),
        ("historyUnreadBarBorder",    p.border),
        ("historyUnreadBarFg",        p.accent),

        # The filled primary button: accent fill, dark ink, matching the
        # constant's intent. A grey fill under accent text reads as a plain
        # surface on its own, and goes accent-on-accent wherever tdesktop
        # pairs activeButtonFg with a windowBgActive fill.
        ("activeButtonBg",            p.accent),
        ("activeButtonBgOver",        p.accent_hover),
        ("activeButtonBgRipple",      p.accent_active),
        ("activeButtonFg",            p.on_accent),
        ("activeButtonFgOver",        p.on_accent),
        ("activeButtonSecondaryFg",       p.on_accent_muted),
        ("activeButtonSecondaryFgOver",   p.on_accent_muted),
        ("lightButtonBg",             p.elem),
        ("lightButtonBgOver",         p.elem_hover),
        ("lightButtonBgRipple",       p.elem_active),
        ("lightButtonFg",             p.accent),
        ("lightButtonFgOver",         p.accent),

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
        # Destructive actions (log out, delete chat, leave group) — red like
        # every other target's `error`, not the yellow it had.
        ("attentionButtonFg",         p.error),
        ("attentionButtonFgOver",     p.error),

        # Dividers / separators / shadows — Telegram defaults these bright in
        # popup menus when undefined. Keep them subtle and dark.
        ("shadowFg",                  p.panel),
        ("windowShadowFg",            p.panel),
        ("windowShadowFgFallback",    p.panel),
        ("boxDividerBg",              p.panel),
        ("boxDividerFg",              p.border),
        ("menuBg",                    p.panel),
        ("menuBgOver",                p.elem_hover),
        ("menuBgRipple",              p.elem_active),
        ("menuFg",                    p.text),
        ("menuFgDisabled",            p.text_muted),
        ("menuIconFg",                p.text_muted),
        ("menuIconFgOver",            p.text),
        ("menuSubmenuArrowFg",        p.text_muted),
        ("menuSeparatorFg",           p.border),

        ("mentionBg",                 p.elem),
        ("mentionFg",                 p.accent),

        # Forward / compose / reply bar backgrounds — Telegram falls back to a
        # bluish-cyan night default for these when not set explicitly.
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

        # The arrow and the radial progress line drawn *inside* those accent
        # circles. Both default to #ffffff, which is 1.2:1 on our accent.
        ("historyFileInIconFg",               p.on_accent),
        ("historyFileInIconFgSelected",       p.on_accent),
        ("historyFileInRadialFg",             p.on_accent),
        ("historyFileInRadialFgSelected",     p.on_accent),
        ("historyFileOutIconFg",              p.on_accent),
        ("historyFileOutIconFgSelected",      p.on_accent),
        ("historyFileOutRadialFg",            p.on_accent),
        ("historyFileOutRadialFgSelected",    p.on_accent),

        # Shared-files-tab thumbnail parity (msgFile1..4 slots), in case the
        # user lands there. Upstream darkens the selected variant.
        ("msgFile1BgSelected",                "msgFile1Bg"),
        ("msgFile2BgSelected",                "msgFile2Bg"),
        ("msgFile3BgSelected",                "msgFile3Bg"),
        ("msgFile4BgSelected",                "msgFile4Bg"),

        # Audio player top panel — defaults to windowBg (#1f1e1d) which
        # blends into the chat list. Lift to panel grey for separation.
        ("mediaPlayerBg",                  p.panel),

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
    # Telegram reads one of the two values a repeated key carries, and does
    # not say which. A palette that states a colour twice is the bug.
    repeated = sorted(name for name, count in
                      Counter(name for name, _ in pairs).items() if count > 1)
    assert not repeated, (
        f"the palette assigns {', '.join(repeated)} more than once")

    lines = ["// Ayu Graphite — Telegram Desktop palette", ""]
    lines += [f"{k}: {v};" for k, v in pairs]
    return "\n".join(lines) + "\n"


def solid_png(hex_color: str, size: int = 8) -> bytes:
    """Tiny solid-color PNG (no Pillow). Telegram tiles/scales it as wallpaper."""
    rgb = bytes(emit.rgb_bytes(hex_color))

    def chunk(typ: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + typ + data
                + struct.pack(">I", zlib.crc32(typ + data) & 0xffffffff))

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)  # 8-bit RGB
    raw = b"".join(b"\x00" + rgb * size for _ in range(size))  # filter byte + row
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(raw, 9))
            + chunk(b"IEND", b""))


def telegram_zip(palette_text: str, bg_hex: str) -> bytes:
    """The archive Telegram reads: the palette, plus a solid background."""
    # Fixed timestamp so identical inputs produce byte-identical archives —
    # otherwise zipfile stamps each entry with `now` and git sees a diff on
    # every build.
    epoch = (1980, 1, 1, 0, 0, 0)
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in (("colors.tdesktop-theme", palette_text.encode()),
                           ("background.png",        solid_png(bg_hex))):
            info = zipfile.ZipInfo(name, date_time=epoch)
            info.compress_type = zipfile.ZIP_DEFLATED
            z.writestr(info, data)
    return buffer.getvalue()


def main() -> None:
    p = load_palette()
    palette_text = build_telegram(p)
    emit.write_bytes(emit.beside(__file__, "ayu-graphite.tdesktop-theme"),
                     telegram_zip(palette_text, p.bg))
    # Mirror the same palette text uncompressed for easy inspection / grep.
    emit.write_text(emit.beside(__file__, "ayu-graphite.tdesktop-theme.txt"),
                    palette_text)


if __name__ == "__main__":
    main()
