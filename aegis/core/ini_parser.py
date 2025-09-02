from __future__ import annotations

from pathlib import Path
from typing import Dict

IniData = Dict[str, Dict[str, str]]


def parse_ini(path: Path) -> IniData:
    """Parse a simple INI file into a nested dict.

    Supports multiple sections in ``[section]`` form and ``;`` comments.
    Inline comments are stripped. Values are kept as strings.
    """
    data: IniData = {}
    current: Dict[str, str] | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            sect = line[1:-1].strip()
            current = data.setdefault(sect, {})
            continue
        if current is None or "=" not in line:
            continue
        key, val = line.split("=", 1)
        current[key.strip()] = val.strip()
    return data
