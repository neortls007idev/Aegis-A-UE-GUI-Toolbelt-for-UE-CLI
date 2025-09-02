from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from aegis.core.profile import Profile


class ProfileInfoBar(QWidget):
    """Display paths related to the active profile."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 2, 6, 2)
        layout.setSpacing(12)
        self.engine_label = QLabel()
        self.project_label = QLabel()
        self.profile_path_label = QLabel()
        self.profile_name_label = QLabel()
        for lbl in (
            self.engine_label,
            self.project_label,
            self.profile_path_label,
            self.profile_name_label,
        ):
            lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
            layout.addWidget(lbl)
        layout.addStretch()
        self.update(None, None)

    def update(self, profile: Optional[Profile], path: Optional[str]) -> None:
        msg = "Create a profile"
        if profile:
            self.engine_label.setText(f"Engine: {profile.engine_root}")
            self.project_label.setText(f"Project: {profile.project_dir}")
            self.profile_name_label.setText(f"Profile: {profile.display_name()}" or msg)
        else:
            self.engine_label.setText(f"Engine: {msg}")
            self.project_label.setText(f"Project: {msg}")
            self.profile_name_label.setText(f"Profile: {msg}")
        self.profile_path_label.setText(f"Profile Path: {path or msg}")
