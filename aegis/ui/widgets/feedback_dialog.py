from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QTextEdit,
)


class FeedbackDialog(QDialog):
    def __init__(self, parent: QDialog | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Provide Feedback")
        layout = QFormLayout(self)
        self.subject_edit = QLineEdit()
        self.message_edit = QTextEdit()
        layout.addRow("Subject:", self.subject_edit)
        layout.addRow("Feedback:", self.message_edit)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        layout.addWidget(buttons)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

    def get_feedback(self) -> tuple[str, str]:
        return self.subject_edit.text(), self.message_edit.toPlainText()
