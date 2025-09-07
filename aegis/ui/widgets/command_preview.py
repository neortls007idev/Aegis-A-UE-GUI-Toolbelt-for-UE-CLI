from __future__ import annotations

from PySide6.QtWidgets import QApplication, QHBoxLayout, QPushButton, QLineEdit, QWidget


class CommandPreviewWidget(QWidget):
    """Read-only line edit with a copy button for CLI previews."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("command_preview")
        self.line = QLineEdit()
        self.line.setReadOnly(True)
        self.line.setObjectName("command_edit")
        self.copy_btn = QPushButton("Copy")
        self.copy_btn.setObjectName("copy_btn")
        layout = QHBoxLayout(self)
        layout.addWidget(self.line, 1)
        layout.addWidget(self.copy_btn)
        self.copy_btn.clicked.connect(self._copy)

    def set_command(self, cmd: str) -> None:
        self.line.setText(cmd)

    def _copy(self) -> None:
        QApplication.clipboard().setText(self.line.text())
