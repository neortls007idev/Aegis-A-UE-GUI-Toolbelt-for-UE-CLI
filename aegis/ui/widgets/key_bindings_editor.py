from __future__ import annotations

from typing import Dict

from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QKeySequenceEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from aegis.core.key_bindings import ACTION_NAMES, DEFAULT_KEY_BINDINGS


class KeyBindingsEditor(QDialog):
    def __init__(self, bindings: Dict[str, str], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Key Bindings")
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.edits: Dict[str, QKeySequenceEdit] = {}
        for action, title in ACTION_NAMES.items():
            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(0, 0, 0, 0)
            edit = QKeySequenceEdit()
            seq = bindings.get(action)
            if seq:
                edit.setKeySequence(seq)
            btn_assign = QPushButton("Assign")
            btn_clear = QPushButton("Clear")
            row_layout.addWidget(edit)
            row_layout.addWidget(btn_assign)
            row_layout.addWidget(btn_clear)
            form.addRow(title, row)
            self.edits[action] = edit
            edit.keySequenceChanged.connect(
                lambda seq, a=action: self._on_sequence_changed(a, seq)
            )
            btn_assign.clicked.connect(edit.setFocus)
            btn_clear.clicked.connect(
                lambda _=False, e=edit: e.setKeySequence(QKeySequence())
            )
        layout.addLayout(form)
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

    def get_bindings(self) -> Dict[str, str]:
        result: Dict[str, str] = {}
        for action, edit in self.edits.items():
            seq = edit.keySequence().toString()
            result[action] = seq
        return result

    def _on_sequence_changed(self, action: str, seq: QKeySequence) -> None:
        """Ensure uniqueness by clearing duplicates in other fields."""
        if not seq.toString():
            return
        for other_action, other_edit in self.edits.items():
            if (
                other_action != action
                and other_edit.keySequence().toString() == seq.toString()
            ):
                other_edit.setKeySequence(QKeySequence())

    def _reset_defaults(self) -> None:
        """Restore edits to default key bindings."""
        for action, edit in self.edits.items():
            seq = DEFAULT_KEY_BINDINGS.get(action, "")
            edit.setKeySequence(seq)
