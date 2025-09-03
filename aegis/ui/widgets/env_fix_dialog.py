from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class EnvFixDialog(QDialog):
    """Dialog to select environment fix scripts."""

    def __init__(self, scripts: dict[str, Path], parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Fix Environment")
        self._scripts: dict[str, Path] = {}
        self._checks: dict[str, QCheckBox] = {}

        self._layout = QVBoxLayout(self)
        self._add_button = QPushButton("Add Script…")
        self._add_button.clicked.connect(self._prompt_add_scripts)
        self._layout.addWidget(self._add_button)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        self._layout.addWidget(buttons)

        for name, path in scripts.items():
            self.add_script(path, name)

    def selected_scripts(self) -> list[Path]:
        return [
            self._scripts[name] for name, cb in self._checks.items() if cb.isChecked()
        ]

    def _prompt_add_scripts(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Select scripts")
        for p in paths:
            self.add_script(Path(p))

    def add_script(self, path: Path, name: str | None = None) -> None:
        if not name:
            base = path.name
            name = base
            idx = 2
            while name in self._scripts:
                name = f"{base} ({idx})"
                idx += 1
        self._scripts[name] = path
        cb = QCheckBox(f"{name} (" + str(path) + ")")
        cb.setChecked(True)
        self._checks[name] = cb
        index = self._layout.indexOf(self._add_button)
        self._layout.insertWidget(index, cb)
