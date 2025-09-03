from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QToolButton, QWidget


class TooltipIcon(QToolButton):
    """Small "?" button that shows a tooltip on hover."""

    def __init__(self, tip: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setText("?")
        self.setToolTip(tip)
        self.setCursor(Qt.WhatsThisCursor)
        self.setAutoRaise(True)
        self.setFixedSize(16, 16)
        self.setStyleSheet("QToolButton { border: none; padding: 0; }")
