#!/usr/bin/env python3
"""Read ../ayu-graphite.toml and emit ./ayu-graphite.tgios-theme (Telegram iOS).

Format reverse-engineered from a known-working canonical sample
(aznotas/rose-pine-telegram-ios) and confirmed against
PresentationThemeCoder.swift in the official Telegram-iOS repo:

  - YAML-nested, 2-space indent (the underscore-flat form some community
    themes use — e.g. Dracula's — is non-canonical and silently falls back
    to `basedOn` defaults for unrecognized keys).
  - Hex colors are lowercase with no `#`.
  - Alpha is a *prefix* (AARRGGBB), not a suffix. `7fffffff` = 50% white.
  - `clear` is a literal sentinel for fully transparent.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from palette import Palette, load_palette


def h(color: str) -> str:
    """#rrggbb -> rrggbb (lowercase, no #)."""
    return color.lstrip("#").lower()


def a(aa: str, color: str) -> str:
    """Alpha-prefixed ARGB. aa is two hex digits; color is #rrggbb."""
    return aa + h(color)


def build_ios(p: Palette) -> dict:
    accent = p.accent
    # Desktop reserves `accent` (bright cyan_500) for filled UI fg
    # (activeButton, msgFile circles) and uses `ansi_cyan` (softer cyan_300)
    # for inline text accents — unread bg, mentions, reply bars, service text,
    # light-button fg. Mirror that split here so both targets read the same.
    inline_accent = p.ansi_cyan
    incoming_bubble = p.chat_msg_bg
    outgoing_bubble = p.chat_msg_bg
    return {
        "name": "Ayu Graphite",
        "basedOn": "night",
        "dark": True,
        "intro": {
            "statusBar": "white",
            "primaryText": h(p.text),
            "accentText": h(accent),
            "disabledText": h(p.text_disabled),
            "startButton": h(accent),
            "dot": h(p.text_muted),
        },
        "passcode": {
            "bg": {"top": h(p.bg), "bottom": h(p.bg)},
            "button": h(p.elem),
        },
        "root": {
            "statusBar": "white",
            "tabBar": {
                "background": h(p.title_bar),
                "separator": h(p.border),
                "icon": h(p.text_muted),
                "selectedIcon": h(accent),
                "text": h(p.text_muted),
                "selectedText": h(accent),
                "badgeBackground": h(p.error),
                "badgeStroke": h(p.title_bar),
                "badgeText": h(p.text),
            },
            "navBar": {
                "button": h(accent),
                "disabledButton": h(p.text_disabled),
                "primaryText": h(p.text),
                "secondaryText": h(p.text_muted),
                "control": h(p.text_muted),
                "accentText": h(accent),
                "background": h(p.title_bar),
                "opaqueBackground": h(p.title_bar),
                "separator": h(p.border),
                "badgeFill": h(p.error),
                "badgeStroke": h(p.title_bar),
                "badgeText": h(p.text),
                "segmentedBg": h(p.elem),
                "segmentedFg": h(p.elem_active),
                "segmentedText": h(p.text),
                "segmentedDivider": h(p.border),
            },
            "searchBar": {
                "background": h(p.panel),
                "accent": h(accent),
                "inputFill": h(p.elem),
                "inputText": h(p.text),
                "inputPlaceholderText": h(p.text_muted),
                "inputIcon": h(p.text_muted),
                "inputClearButton": h(p.text_muted),
                "separator": h(p.border),
            },
            "keyboard": "dark",
        },
        "list": {
            "blocksBg": h(p.bg),
            "plainBg": h(p.bg),
            "primaryText": h(p.text),
            "secondaryText": h(p.text_muted),
            "disabledText": h(p.text_disabled),
            "accent": h(accent),
            "highlighted": h(p.success),
            "destructive": h(p.error),
            "placeholderText": h(p.text_disabled),
            "itemBlocksBg": h(p.panel),
            "itemHighlightedBg": h(p.elem_hover),
            "blocksSeparator": h(p.border),
            "plainSeparator": h(p.border),
            "disclosureArrow": a("7f", p.text_muted),
            "sectionHeaderText": h(p.text_muted),
            "freeText": h(p.text_muted),
            "freeTextError": h(p.error),
            "freeTextSuccess": h(p.success),
            "freeMonoIcon": h(p.text_muted),
            "switch": {
                "frame": h(p.border),
                "handle": h(p.text),
                "content": h(accent),
                "positive": h(p.success),
                "negative": h(p.error),
            },
            "disclosureActions": {
                "neutral1":     {"bg": h(p.elem),    "fg": h(p.text)},
                "neutral2":     {"bg": h(p.warning), "fg": h(p.bg)},
                "destructive":  {"bg": h(p.error),   "fg": h(p.text)},
                "constructive": {"bg": h(p.success), "fg": h(p.bg)},
                "accent":       {"bg": h(accent),    "fg": h(p.bg)},
                "warning":      {"bg": h(p.warning), "fg": h(p.bg)},
                "inactive":     {"bg": h(p.elem),    "fg": h(p.text_muted)},
            },
            "check": {
                "bg": h(accent),
                "stroke": h(p.text_muted),
                "fg": h(p.bg),
            },
            "controlSecondary": h(p.text_muted),
            "freeInputField": {
                "bg": h(p.elem),
                "stroke": h(p.border),
                "placeholder": h(p.text_disabled),
                "primary": h(p.text),
                "control": h(p.text_muted),
            },
            "mediaPlaceholder": h(p.elem),
            "scrollIndicator": a("7f", p.text_muted),
            "pageIndicatorInactive": a("66", p.text_muted),
            "inputClearButton": h(p.text_muted),
            "itemBarChart": {
                "color1": h(accent),
                "color2": h(p.text_muted),
                "color3": h(p.elem),
            },
            "itemInputField": {
                "bg": h(p.elem),
                "stroke": h(p.border),
                "placeholder": h(p.text_disabled),
                "primary": h(p.text),
                "control": h(p.text_muted),
            },
        },
        "chatList": {
            "bg": h(p.bg),
            "itemSeparator": h(p.border),
            "itemBg": h(p.bg),
            "pinnedItemBg": h(p.panel),
            "itemHighlightedBg": h(p.elem_hover),
            "itemSelectedBg": h(p.elem_active),
            "title": h(p.text),
            "secretTitle": h(p.success),
            "dateText": h(p.text_muted),
            "authorName": h(p.text),
            "messageText": h(p.text_muted),
            "messageHighlightedText": h(p.text),
            "messageDraftText": h(p.warning),
            "checkmark": h(p.chat_check),
            "pendingIndicator": h(p.text_muted),
            "failedFill": h(p.error),
            "failedFg": h(p.text),
            "muteIcon": h(p.text_muted),
            "unreadBadgeActiveBg": h(p.ansi_cyan),
            "unreadBadgeActiveText": h(p.bg),
            "unreadBadgeInactiveBg": h(p.text_muted),
            "unreadBadgeInactiveText": h(p.bg),
            "reactionBadgeActiveBg": h(p.ansi_cyan),
            "pinnedBadge": h(p.text_muted),
            "pinnedSearchBar": h(p.elem),
            "regularSearchBar": h(p.elem),
            "sectionHeaderBg": h(p.panel),
            "sectionHeaderText": h(p.text_muted),
            "verifiedIconBg": h(accent),
            "verifiedIconFg": h(p.bg),
            "secretIcon": h(p.success),
            "pinnedArchiveAvatar": {
                "background": {"top": h(accent), "bottom": h(accent)},
                "foreground": h(p.bg),
            },
            "unpinnedArchiveAvatar": {
                "background": {"top": h(p.elem), "bottom": h(p.elem)},
                "foreground": h(p.text_muted),
            },
            "onlineDot": h(p.success),
        },
        "chat": {
            "defaultWallpaper": f"ff{h(p.bg)}",
            "animateMessageColors": False,
            "message": {
                "incoming":  _bubble_side(p, incoming_bubble, inline_accent, outgoing=False),
                "outgoing":  _bubble_side(p, outgoing_bubble, inline_accent, outgoing=True),
                "freeform": {
                    "withWp":    _freeform(p),
                    "withoutWp": _freeform(p),
                },
                "infoPrimaryText": h(p.text),
                "infoLinkText": h(inline_accent),
                "outgoingCheck": h(p.chat_check),
                "mediaDateAndStatusBg": a("7f", p.overlay_black),
                "mediaDateAndStatusText": h(p.text),
                "shareButtonBg":     {"withWp": a("7f", p.panel), "withoutWp": a("7f", p.panel)},
                "shareButtonStroke": {"withWp": a("26", p.text_muted), "withoutWp": a("26", p.text_muted)},
                "shareButtonFg":     {"withWp": h(p.text_muted), "withoutWp": h(p.text_muted)},
                "mediaOverlayControl": {"bg": a("99", p.overlay_black), "fg": h(p.text)},
                "selectionControl":   {"bg": h(accent), "stroke": h(p.text), "fg": h(p.bg)},
                "deliveryFailed":     {"bg": h(p.error), "fg": h(p.text)},
                "mediaHighlightOverlay": a("99", p.text),
                "stickerPlaceholder":        {"withWp": a("7f", p.elem), "withoutWp": a("7f", p.elem)},
                "stickerPlaceholderShimmer": {"withWp": a("0c", p.text), "withoutWp": a("0c", p.text)},
            },
            "serviceMessage": {
                "components": {
                    "withDefaultWp": _service_components(p),
                    "withCustomWp":  _service_components(p),
                },
                "unreadBarBg": h(p.panel),
                "unreadBarStroke": h(p.border),
                "unreadBarText": h(p.text),
                "dateText": {"withWp": h(p.text_muted), "withoutWp": h(p.text_muted)},
            },
            "inputPanel": {
                "panelBg": h(p.title_bar),
                "panelSeparator": h(p.border),
                "panelControlAccent": h(accent),
                "panelControl": h(p.text_muted),
                "panelControlDisabled": h(p.text_disabled),
                "panelControlDestructive": h(p.error),
                "inputBg": h(p.elem),
                "inputStroke": h(p.border),
                "inputPlaceholder": h(p.text_muted),
                "inputText": h(p.text),
                "inputControl": h(p.text_muted),
                "actionControlBg": h(accent),
                "actionControlFg": h(p.bg),
                "primaryText": h(p.text),
                "secondaryText": h(p.text_muted),
                "mediaRecordDot": h(p.error),
                "mediaRecordControl": {
                    "button": h(accent),
                    "micLevel": a("33", accent),
                    "activeIcon": h(p.bg),
                },
            },
            "inputMediaPanel": {
                "panelSeparator": h(p.border),
                "panelIcon": h(p.text_muted),
                "panelHighlightedIconBg": h(p.elem_hover),
                "stickersBg": h(p.panel),
                "stickersSectionText": h(p.text_muted),
                "stickersSearchBg": h(p.elem),
                "stickersSearchPlaceholder": h(p.text_muted),
                "stickersSearchPrimary": h(p.text),
                "stickersSearchControl": h(p.text_muted),
                "gifsBg": h(p.panel),
            },
            "inputButtonPanel": {
                "panelBg": h(p.panel),
                "panelSeparator": h(p.border),
                "buttonBg": h(p.elem),
                "buttonStroke": h(p.border),
                "buttonHighlightedBg": h(p.elem_hover),
                "buttonHighlightedStroke": h(p.border),
                "buttonText": h(p.text),
            },
            "historyNav": {
                "bg": h(p.panel),
                "stroke": h(p.border),
                "fg": h(p.text_muted),
                "badgeBg": h(accent),
                "badgeStroke": h(accent),
                "badgeText": h(p.bg),
            },
        },
        "actionSheet": {
            "dim": a("7f", p.overlay_black),
            "bgType": "dark",
            "opaqueItemBg": h(p.panel),
            "itemBg": a("cc", p.panel),
            "opaqueItemHighlightedBg": h(p.elem_hover),
            "itemHighlightedBg": a("33", p.elem_hover),
            "opaqueItemSeparator": h(p.border),
            "standardActionText": h(accent),
            "destructiveActionText": h(p.error),
            "disabledActionText": h(p.text_disabled),
            "primaryText": h(p.text),
            "secondaryText": h(p.text_muted),
            "controlAccent": h(accent),
            "inputBg": h(p.elem),
            "inputHollowBg": h(p.elem),
            "inputBorder": h(p.border),
            "inputPlaceholder": h(p.text_muted),
            "inputText": h(p.text),
            "inputClearButton": h(p.text_muted),
            "checkContent": h(p.bg),
        },
        "contextMenu": {
            "dim": a("99", p.overlay_black),
            "background": a("c3", p.panel),
            "itemSeparator": a("26", p.text_muted),
            "sectionSeparator": a("33", p.overlay_black),
            "itemBg": "00000000",
            "itemHighlightedBg": a("26", p.text_muted),
            "primary": h(p.text),
            "secondary": h(p.text_muted),
            "destructive": h(p.error),
        },
        "notification": {
            "bg": h(p.panel),
            "primaryText": h(p.text),
            "expanded": {
                "bgType": "dark",
                "navBar": {
                    "background": h(p.title_bar),
                    "primaryText": h(p.text),
                    "control": h(accent),
                    "separator": h(p.border),
                },
            },
        },
        "chart": {
            "labels": h(p.text_muted),
            "helperLines": a("59", p.text_muted),
            "strongLines": a("59", p.text_muted),
            "barStrongLines": a("72", p.text_muted),
            "detailsText": h(p.text),
            "detailsArrow": h(p.text_muted),
            "detailsView": h(p.panel),
            "rangeViewFrame": h(p.border),
            "rangeViewMarker": h(p.text),
        },
    }


def _bubble_side(p: Palette, bg: str, accent: str, *, outgoing: bool) -> dict:
    text = p.text
    return {
        "bubble": {
            "withWp":    _bubble(p, bg),
            "withoutWp": _bubble(p, bg),
        },
        "primaryText": h(text),
        "secondaryText": a("99", text),
        "linkText": h(accent),
        "linkHighlight": a("7f", accent),
        "scam": h(p.error),
        "textHighlight": h(p.chat_check),
        "accentText": h(accent),
        "accentControl": h(accent),
        "mediaActiveControl": h(accent),
        "mediaInactiveControl": a("7f", accent),
        "mediaControlInnerBg": h(bg),
        "pendingActivity": a("7f", text),
        "fileTitle": h(accent),
        "fileDescription": a("99", text),
        "fileDuration": a("99", text),
        "mediaPlaceholder": h(p.elem),
        "polls": {
            "radioButton": h(p.text_muted),
            "radioProgress": h(accent),
            "highlight": a("1e", accent),
            "separator": h(p.border),
            "bar": h(accent),
            "barIconForeground": h(p.bg),
            "barPositive": h(p.success),
            "barNegative": h(p.error),
        },
        "actionButtonsBg":     {"withWp": a("7f", p.panel), "withoutWp": a("7f", p.panel)},
        "actionButtonsStroke": {"withWp": a("26", p.text_muted), "withoutWp": a("26", p.text_muted)},
        "actionButtonsText":   {"withWp": h(text), "withoutWp": h(text)},
        "textSelection": a("33", accent),
        "textSelectionKnob": h(accent),
    }


def _bubble(p: Palette, bg: str) -> dict:
    return {
        "bg": h(bg),
        "gradientBg": h(bg),
        "highlightedBg": h(p.elem_active),
        "stroke": h(bg),
        "reactionInactiveBg": a("19", p.text),
        "reactionInactiveFg": h(p.text),
        "reactionActiveBg": h(p.accent),
        "reactionActiveFg": h(p.bg),
    }


def _freeform(p: Palette) -> dict:
    return {
        "bg": h(p.panel),
        "gradientBg": h(p.panel),
        "highlightedBg": h(p.elem_hover),
        "stroke": h(p.border),
        "reactionInactiveBg": a("19", p.text),
        "reactionInactiveFg": h(p.text),
        "reactionActiveBg": h(p.accent),
        "reactionActiveFg": h(p.bg),
    }


def _service_components(p: Palette) -> dict:
    return {
        "bg": h(p.panel),
        "primaryText": h(p.text_muted),
        "linkHighlight": a("1e", p.text),
        "scam": h(p.error),
        "dateFillStatic": a("99", p.panel),
        "dateFillFloat": a("33", p.panel),
    }


def render(node, indent: int = 0) -> str:
    """Walk a nested dict and emit YAML-flavored text matching the official
    PresentationThemeCoder output: leaves as `key: value`, subnodes as `key:`
    followed by 2-space-indented children."""
    if isinstance(node, dict):
        out = []
        for k, v in node.items():
            pad = "  " * indent
            if isinstance(v, dict):
                out.append(f"{pad}{k}:")
                out.append(render(v, indent + 1))
            elif isinstance(v, bool):
                out.append(f"{pad}{k}: {'true' if v else 'false'}")
            else:
                out.append(f"{pad}{k}: {v}")
        return "\n".join(out)
    return str(node)


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    repo = os.path.dirname(here)
    p = load_palette(os.path.join(repo, "ayu-graphite.toml"))
    out = os.path.join(here, "ayu-graphite.tgios-theme")
    with open(out, "w") as f:
        f.write(render(build_ios(p)) + "\n")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
