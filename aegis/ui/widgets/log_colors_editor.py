from __future__ import annotations

from typing import Callable, Dict, List, Tuple

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QColorDialog,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from aegis.core.log_colors import DEFAULT_LEVEL_COLORS


class ColorButton(QPushButton):
    def __init__(
        self,
        color: str = "#ffffff",
        parent=None,
        on_preview: Callable[[str], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self._color = QColor(color)
        self._on_preview = on_preview
        self.clicked.connect(self._choose_color)
        self._apply_color()

    def _choose_color(self) -> None:
        original = QColor(self._color)
        dlg = QColorDialog(self._color, self)
        dlg.currentColorChanged.connect(self._preview_color)
        if dlg.exec():
            self._color = dlg.currentColor()
            self._apply_color()
        else:
            self._color = original
            self._apply_color()
            if self._on_preview:
                self._on_preview(original.name())

    def _preview_color(self, color: QColor) -> None:
        self._color = color
        self._apply_color()
        if self._on_preview:
            self._on_preview(color.name())

    def _apply_color(self) -> None:
        name = self._color.name()
        self.setText(name)
        self.setStyleSheet(f"background-color: {name};")

    def color(self) -> str:
        return self._color.name()

    def set_color(self, color: str) -> None:
        self._color = QColor(color)
        self._apply_color()


class LogColorsEditor(QDialog):
    def __init__(
        self,
        levels: Dict[str, str],
        regex: List[Tuple[str, str]],
        parent=None,
        on_preview: Callable[[str, str], None] | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Log Colors")
        layout = QVBoxLayout(self)

        # Level colors
        form = QFormLayout()
        self.level_buttons: Dict[str, ColorButton] = {}
        for level in ["info", "warning", "error", "success"]:
            btn = ColorButton(
                levels.get(level, DEFAULT_LEVEL_COLORS[level]),
                on_preview=(
                    (lambda c, lvl=level: on_preview(lvl, c)) if on_preview else None
                ),
            )
            form.addRow(level.capitalize(), btn)
            self.level_buttons[level] = btn
        layout.addLayout(form)

        # Regex colors
        group = QGroupBox("Regex Colors")
        group_layout = QVBoxLayout(group)
        self.regex_edits: List[Tuple[QLineEdit, ColorButton]] = []
        for i in range(5):
            row = QHBoxLayout()
            pat = QLineEdit()
            col = ColorButton("#ffffff")
            if i < len(regex):
                pat.setText(regex[i][0])
                col.set_color(regex[i][1])
            row.addWidget(pat, 3)
            row.addWidget(col, 1)
            group_layout.addLayout(row)
            self.regex_edits.append((pat, col))
        layout.addWidget(group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok
            | QDialogButtonBox.Cancel
            | QDialogButtonBox.RestoreDefaults,
            parent=self,
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.RestoreDefaults).clicked.connect(
            self._reset_defaults
        )
        layout.addWidget(buttons)

    def get_config(self) -> Tuple[Dict[str, str], List[Tuple[str, str]]]:
        levels = {level: btn.color() for level, btn in self.level_buttons.items()}
        regex: List[Tuple[str, str]] = []
        for pat, col in self.regex_edits:
            if pat.text():
                regex.append((pat.text(), col.color()))
        return levels, regex

    def _reset_defaults(self) -> None:
        for level, btn in self.level_buttons.items():
            btn.set_color(DEFAULT_LEVEL_COLORS[level])
        for pat, col in self.regex_edits:
            pat.clear()
            col.set_color("#ffffff")
