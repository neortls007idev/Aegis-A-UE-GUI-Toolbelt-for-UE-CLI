from __future__ import annotations

from typing import Dict, List, Tuple

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QVBoxLayout,
)

from aegis.core.log_colors import DEFAULT_LEVEL_COLORS


class LogColorsEditor(QDialog):
    def __init__(
        self,
        levels: Dict[str, str],
        regex: List[Tuple[str, str]],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Log Colors")
        layout = QVBoxLayout(self)

        # Level colors
        form = QFormLayout()
        self.level_edits: Dict[str, QLineEdit] = {}
        for level in ["info", "warning", "error", "success"]:
            edit = QLineEdit(levels.get(level, ""))
            form.addRow(level.capitalize(), edit)
            self.level_edits[level] = edit
        layout.addLayout(form)

        # Regex colors
        group = QGroupBox("Regex Colors")
        group_layout = QVBoxLayout(group)
        self.regex_edits: List[Tuple[QLineEdit, QLineEdit]] = []
        for i in range(5):
            row = QHBoxLayout()
            pat = QLineEdit()
            col = QLineEdit()
            if i < len(regex):
                pat.setText(regex[i][0])
                col.setText(regex[i][1])
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
        levels = {level: edit.text() for level, edit in self.level_edits.items()}
        regex: List[Tuple[str, str]] = []
        for pat, col in self.regex_edits:
            if pat.text() and col.text():
                regex.append((pat.text(), col.text()))
        return levels, regex

    def _reset_defaults(self) -> None:
        for level, edit in self.level_edits.items():
            edit.setText(DEFAULT_LEVEL_COLORS[level])
        for pat, col in self.regex_edits:
            pat.clear()
            col.clear()
