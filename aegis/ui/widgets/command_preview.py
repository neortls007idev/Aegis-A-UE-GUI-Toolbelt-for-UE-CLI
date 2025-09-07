from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QPushButton, QLineEdit, QWidget
from PySide6.QtCore import Qt


class CommandPreviewWidget(QWidget):
    """Read-only line edit with a copy button for CLI previews."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("command_preview")
        self.line = QLineEdit()
        self.line.setReadOnly(True)
        self.line.setObjectName("command_edit")
        self.line.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setObjectName("copy_btn")
        layout = QHBoxLayout(self)
        layout.addWidget(self.line, 1)
        layout.addWidget(self.copy_btn)
        self.copy_btn.clicked.connect(self._copy)

    def set_command(self, cmd: str) -> None:
        self.line.setText(cmd)

    def _copy(self) -> None:
        self.line.selectAll()
        self.line.copy()
