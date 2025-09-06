from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

IniData = Dict[str, Dict[str, List[Optional[str]]]]


def parse_ini(path: Path) -> IniData:
    """Parse an Unreal Engine ``.ini`` file applying special operators.

    Unreal configuration files support line prefixes that modify how values are
    merged:

    ``+`` adds a line only if the property is missing, ``-`` removes exact
    matches, ``.`` always appends a new line, and ``!`` deletes a property by
    name. Semicolons are treated as literal characters rather than comments.

    Returns a nested mapping of ``section -> key -> list of values``. A value is
    ``None`` when the line had no ``=`` delimiter (flag-style entries).
    """

    data: IniData = {}
    section: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            section = line[1:-1].strip()
            data.setdefault(section, {})
            continue
        if section is None:
            continue
        prefix = ""
        if line[0] in "+-!.":
            prefix, line = line[0], line[1:]
        key, sep, raw_value = line.partition("=")
        key = key.strip()
        value: str | None = raw_value.strip() if sep else None
        sec = data.setdefault(section, {})
        existing = sec.get(key)
        if prefix == "+":
            if not existing:
                sec[key] = [value]
        elif prefix == "-":
            if existing:
                sec[key] = [v for v in existing if v != value]
                if not sec[key]:
                    sec.pop(key)
        elif prefix == ".":
            sec.setdefault(key, []).append(value)
        elif prefix == "!":
            sec.pop(key, None)
        else:
            sec[key] = [value]
    return data


def get_value(data: IniData, section: str, key: str) -> str | None:
    """Return the last surviving value for ``section/key`` or ``None``."""

    values = data.get(section, {}).get(key)
    return values[-1] if values else None
