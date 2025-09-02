from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QVBoxLayout,
    QWidget,
)


class EnvFixDialog(QDialog):
    """Dialog to select environment fix scripts."""

    def __init__(self, scripts: dict[str, Path], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Fix Environment")
        self._scripts = scripts
        self._checks: dict[str, QCheckBox] = {}

        layout = QVBoxLayout(self)
        for name, path in scripts.items():
            cb = QCheckBox(f"{name} (" + str(path) + ")")
            cb.setChecked(True)
            self._checks[name] = cb
            layout.addWidget(cb)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def selected_scripts(self) -> list[Path]:
        return [
            self._scripts[name] for name, cb in self._checks.items() if cb.isChecked()
        ]
