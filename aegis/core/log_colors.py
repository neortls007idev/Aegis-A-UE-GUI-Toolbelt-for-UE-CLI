from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Dict, List, Tuple

from PySide6.QtCore import QSettings

DEFAULT_LEVEL_COLORS: Dict[str, str] = {
    "info": "#888",
    "warning": "#cc0",
    "error": "#b00",
    "success": "#0a0",
}


@dataclass
class LogColors:
    settings: QSettings
    prefix: str = "log_colors"

    def get_level_color(self, level: str) -> str:
        return self.settings.value(
            f"{self.prefix}/levels/{level}",
            DEFAULT_LEVEL_COLORS.get(level, "#888"),
            type=str,
        )

    def set_level_color(self, level: str, color: str) -> None:
        self.settings.setValue(f"{self.prefix}/levels/{level}", color)

    def regex_rules(self) -> List[Tuple[str, str]]:
        data = self.settings.value(f"{self.prefix}/regex", "[]", type=str)
        try:
            raw = json.loads(data)
        except Exception:
            raw = []
        rules: List[Tuple[str, str]] = []
        for entry in raw[:5]:
            pattern = entry.get("pattern")
            color = entry.get("color")
            if pattern and color:
                rules.append((pattern, color))
        return rules

    def set_regex_rules(self, rules: List[Tuple[str, str]]) -> None:
        payload = [{"pattern": p, "color": c} for p, c in rules if p and c][:5]
        self.settings.setValue(f"{self.prefix}/regex", json.dumps(payload))

    def color_for(self, message: str, level: str) -> str:
        for pattern, color in self.regex_rules():
            try:
                if re.search(pattern, message):
                    return color
            except re.error:
                continue
        return self.get_level_color(level)

    def export_json(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.all(), f, indent=2)

    def import_json(self, path: str) -> None:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        levels = data.get("levels", {})
        for level, color in levels.items():
            if level in DEFAULT_LEVEL_COLORS:
                self.set_level_color(level, color)
        regex_list = []
        for entry in data.get("regex", [])[:5]:
            pattern = entry.get("pattern")
            color = entry.get("color")
            if pattern and color:
                regex_list.append((pattern, color))
        self.set_regex_rules(regex_list)

    def all(self) -> Dict[str, object]:
        return {
            "levels": {
                level: self.get_level_color(level) for level in DEFAULT_LEVEL_COLORS
            },
            "regex": [{"pattern": p, "color": c} for p, c in self.regex_rules()],
        }

    def reset(self) -> None:
        self.settings.beginGroup(self.prefix)
        self.settings.remove("")
        self.settings.endGroup()
