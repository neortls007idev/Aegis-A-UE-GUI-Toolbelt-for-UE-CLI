from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QDialog, QDialogButtonBox, QTextEdit, QVBoxLayout


class HelpDialog(QDialog):
    def __init__(self, readme_path: Path, parent: QDialog | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Help")
        layout = QVBoxLayout(self)
        text = QTextEdit()
        text.setReadOnly(True)
        try:
            with open(readme_path, "r", encoding="utf-8") as f:
                text.setPlainText(f.read())
        except Exception as e:  # pragma: no cover - best effort
            text.setPlainText(str(e))
        layout.addWidget(text)
        buttons = QDialogButtonBox(QDialogButtonBox.Close)
        layout.addWidget(buttons)
        buttons.rejected.connect(self.reject)
        buttons.accepted.connect(self.accept)
