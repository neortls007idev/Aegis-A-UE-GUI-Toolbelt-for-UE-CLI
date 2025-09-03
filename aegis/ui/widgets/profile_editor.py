from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)

from aegis.core.profile import Profile


class ProfileEditor(QDialog):
    """Dialog for creating or editing a :class:`Profile`."""

    def __init__(self, profile: Profile | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Profile")

        layout = QGridLayout(self)

        # Engine root
        layout.addWidget(QLabel("Engine Root:"), 0, 0)
        self.engine_edit = QLineEdit()
        layout.addWidget(self.engine_edit, 0, 1)
        btn_engine = QPushButton("…")
        btn_engine.clicked.connect(self._select_engine)
        layout.addWidget(btn_engine, 0, 2)

        # Project root
        layout.addWidget(QLabel("Project Root:"), 1, 0)
        self.project_edit = QLineEdit()
        layout.addWidget(self.project_edit, 1, 1)
        btn_project = QPushButton("…")
        btn_project.clicked.connect(self._select_project)
        layout.addWidget(btn_project, 1, 2)

        # Nickname
        layout.addWidget(QLabel("Nickname:"), 2, 0)
        self.nickname_edit = QLineEdit()
        layout.addWidget(self.nickname_edit, 2, 1, 1, 2)

        # Buttons
        btn_save = QPushButton("Save")
        btn_cancel = QPushButton("Cancel")
        btn_save.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        btns = QHBoxLayout()
        btns.addStretch()
        btns.addWidget(btn_save)
        btns.addWidget(btn_cancel)
        layout.addLayout(btns, 3, 0, 1, 3)

        if profile:
            self.engine_edit.setText(str(profile.engine_root))
            self.project_edit.setText(str(profile.project_dir))
            self.nickname_edit.setText(profile.nickname)

    def _select_engine(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Engine Root")
        if path:
            self.engine_edit.setText(path)

    def _select_project(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select Project Directory")
        if path:
            self.project_edit.setText(path)

    def get_profile(self) -> Profile:
        """Return the profile described by the dialog fields."""
        return Profile(
            engine_root=Path(self.engine_edit.text()),
            project_dir=Path(self.project_edit.text()),
            nickname=self.nickname_edit.text().strip(),
        )

