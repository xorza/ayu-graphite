"""What every target builder does on the way out: name its file, spell a hex
value the way its format wants it, and write the result.

A builder still owns its own mapping and its own spelling — which role lands
on which key, and whether that key wants `rgb(R,G,B)` or `rrggbb`, is the whole
content of a target. What is shared here is the one hex parse under all of
those spellings, the two formats more than one target writes, and the plumbing
around them, so ten builders open, write and report a file the same way."""
import json
import os
from collections.abc import Iterable
from dataclasses import dataclass


def beside(build_file: str, name: str) -> str:
    """`name` in the calling builder's own directory. Pass `__file__`."""
    return os.path.join(os.path.dirname(os.path.abspath(build_file)), name)


def write_bytes(path: str, data: bytes) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)
    print(f"wrote {path}")


def write_text(path: str, text: str) -> None:
    write_bytes(path, text.encode())


def write_json(path: str, value) -> None:
    write_text(path, json.dumps(value, indent=2))


def rgb_bytes(hex6: str) -> tuple[int, int, int]:
    """#rrggbb -> the three 0-255 channels."""
    h = hex6.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def rgb_csv(hex6: str) -> str:
    """`R,G,B` — what both KDE INI formats store."""
    return "{},{},{}".format(*rgb_bytes(hex6))


def render_ini(sections: dict[str, dict[str, str]]) -> str:
    """The INI both KDE targets are written in."""
    out = []
    for section, kvs in sections.items():
        out.append(f"[{section}]")
        out += [f"{k}={v}" for k, v in kvs.items()]
        out.append("")
    return "\n".join(out)


@dataclass
class RonEntry:
    """One line of a RON table: the role the reading application draws with,
    the color it gets, and the two columns of provenance behind it — the role
    here it came from, and what that resolved to."""
    name: str
    value: str
    key: str
    note: str


@dataclass
class RonColumns:
    """Column widths for a RON table, measured once so provenance reads as
    three columns rather than as a comment trailing each value."""
    name: int
    value: int
    key: int

    @classmethod
    def of(cls, entries: Iterable[RonEntry]) -> "RonColumns":
        entries = list(entries)
        return cls(
            name=max(len(e.name) for e in entries) + 2,
            # +5: the two quotes, the comma, and the two spaces before the comment.
            value=max(len(e.value) for e in entries) + 5,
            key=max(len(e.key) for e in entries) + 2,
        )

    def row(self, entry: RonEntry, indent: int = 4) -> str:
        """One entry. A nameless entry is an element of a list, which carries
        its provenance in the same columns as the table around it."""
        head = f"{entry.name + ':':{self.name}}" if entry.name else ""
        value = '"' + entry.value + '",'
        return (f"{' ' * indent}{head}{value:{self.value}}"
                f"// {entry.key:{self.key}}{entry.note}")
