from __future__ import annotations

from typing import Dict

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QKeySequenceEdit,
    QVBoxLayout,
)

from aegis.core.key_bindings import ACTION_NAMES


class KeyBindingsEditor(QDialog):
    def __init__(self, bindings: Dict[str, str], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Key Bindings")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.edits: Dict[str, QKeySequenceEdit] = {}
        for action, title in ACTION_NAMES.items():
            edit = QKeySequenceEdit()
            seq = bindings.get(action)
            if seq:
                edit.setKeySequence(seq)
            form.addRow(title, edit)
            self.edits[action] = edit
        layout.addLayout(form)
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, parent=self
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_bindings(self) -> Dict[str, str]:
        result: Dict[str, str] = {}
        for action, edit in self.edits.items():
            seq = edit.keySequence().toString()
            result[action] = seq
        return result
