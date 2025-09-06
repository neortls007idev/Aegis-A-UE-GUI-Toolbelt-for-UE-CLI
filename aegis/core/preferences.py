from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

PREFERENCES_FILE = Path(__file__).resolve().parents[2] / "app_preferences" / "app.json"


@dataclass
class AppPreferences:
    allow_docking: bool = True
    allow_resizing: bool = True
    launch_maximized: bool = False
    width: int = 1280
    height: int = 800

    @classmethod
    def load(cls, path: Path = PREFERENCES_FILE) -> "AppPreferences":
        data: dict[str, object] = {}
        if path.is_file():
            try:
                data = json.loads(path.read_text())
            except Exception:
                data = {}
        prefs = cls()
        for key, value in data.items():
            if hasattr(prefs, key):
                setattr(prefs, key, value)
        return prefs

    def save(self, path: Path = PREFERENCES_FILE) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(asdict(self), indent=2))


preferences = AppPreferences.load()
