from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from PySide6.QtCore import QSettings

DEFAULT_KEY_BINDINGS: Dict[str, str] = {
    "file.new_window": "Ctrl+Shift+N",
    "file.exit": "Alt+F4",
    "view.reset_layout": "Ctrl+0",
    "profile.new": "Ctrl+N",
    "profile.open": "Ctrl+O",
    "profile.save": "Ctrl+S",
    "profile.edit": "Ctrl+E",
}

# Human readable names for UI presentation
ACTION_NAMES: Dict[str, str] = {
    "file.new_window": "New Window",
    "file.exit": "Exit",
    "view.reset_layout": "Reset Layout",
    "profile.new": "New Profile",
    "profile.open": "Open Profile",
    "profile.save": "Save Profile",
    "profile.edit": "Edit Profile",
}


@dataclass
class KeyBindings:
    settings: QSettings
    prefix: str = "keybindings/"

    def get(self, action: str) -> str:
        return self.settings.value(
            f"{self.prefix}{action}", DEFAULT_KEY_BINDINGS.get(action, ""), type=str
        )

    def set(self, action: str, sequence: str | None) -> None:
        """Assign *sequence* to *action*, ensuring uniqueness.

        ``None`` reverts to the default binding, while an empty string
        explicitly clears the shortcut.
        """
        if sequence == "":
            # Explicit unbind
            self.settings.setValue(f"{self.prefix}{action}", "")
            return
        if sequence is None or sequence == DEFAULT_KEY_BINDINGS.get(action, ""):
            # Revert to default
            self.settings.remove(f"{self.prefix}{action}")
            return
        # Remove duplicate from other actions (including defaults)
        for other in DEFAULT_KEY_BINDINGS:
            if other != action and self.get(other) == sequence:
                self.settings.setValue(f"{self.prefix}{other}", "")
        self.settings.setValue(f"{self.prefix}{action}", sequence)

    def assign(self, action: str, sequence: str) -> None:
        """Convenience wrapper to assign *sequence* to *action*."""
        self.set(action, sequence)

    def clear(self, action: str) -> None:
        """Explicitly remove any binding from *action*."""
        self.set(action, "")

    def all(self) -> Dict[str, str]:
        bindings = DEFAULT_KEY_BINDINGS.copy()
        self.settings.beginGroup("keybindings")
        for key in self.settings.allKeys():
            bindings[key] = self.settings.value(key, type=str)
        self.settings.endGroup()
        return bindings

    def export_json(self, path: str) -> None:
        import json

        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.all(), f, indent=2)

    def import_json(self, path: str) -> None:
        import json

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for action, seq in data.items():
            if action in DEFAULT_KEY_BINDINGS:
                self.set(action, seq)

    def reset(self) -> None:
        """Remove all custom key bindings, restoring defaults."""
        self.settings.beginGroup("keybindings")
        self.settings.remove("")
        self.settings.endGroup()
