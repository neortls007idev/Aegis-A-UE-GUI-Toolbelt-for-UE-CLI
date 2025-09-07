from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from aegis.core.profile import Profile
from aegis.core.settings import settings

from .directory_tab import DirectoryTab
from .single_tab import SingleFileTab
from .worker import PakWorker


class PakIoStorePanel(QWidget):
    """Panel handling Pak/IoStore operations."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("tab_pak")

        self.profile: Profile | None = None
        self.unrealpak_path: Path | None = None
        self.iostore_path: Path | None = None

        self._build_ui()
        self._connect()

        self.worker = PakWorker(
            self._log,
            self.preview.setPlainText,
            lambda: str(self.unrealpak_path) if self.unrealpak_path else "",
            lambda: str(self.iostore_path) if self.iostore_path else "",
            lambda: self.single_tab.pak_filter.text().strip(),
            lambda: self.dir_tab.dir_unzip_extract.isChecked(),
            self.dir_tab.set_row_status,
            self._on_worker_state,
        )
        self.single_tab.set_worker(
            self.worker,
            lambda: str(self.unrealpak_path) if self.unrealpak_path else "",
            lambda: str(self.iostore_path) if self.iostore_path else "",
        )
        self.dir_tab.set_worker(
            self.worker,
            lambda: str(self.unrealpak_path) if self.unrealpak_path else "",
            lambda: str(self.iostore_path) if self.iostore_path else "",
            lambda: self.single_tab.pak_filter.text().strip(),
        )

        self.dir_tab.dir_root.textChanged.connect(
            lambda t: settings.set_pak_path("dir_root", t)
        )
        self.dir_tab.compare_a.textChanged.connect(
            lambda t: settings.set_pak_path("compare_a", t)
        )
        self.dir_tab.compare_b.textChanged.connect(
            lambda t: settings.set_pak_path("compare_b", t)
        )
        self.single_tab.pak_file.textChanged.connect(
            lambda t: settings.set_pak_path("pak_file", t)
        )

        self._on_worker_state()

    # ----- UI ---------------------------------------------------------
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        tools_box = QGroupBox("Tool Paths")
        tl = QVBoxLayout()
        self.unrealpak_label = QLabel("UnrealPak: (not found)")
        self.unrealpak_label.setObjectName("unrealpak_label")
        self.unrealpak_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.unrealpak_browse = QPushButton("Browse")
        r1 = QHBoxLayout()
        r1.addWidget(self.unrealpak_label, 1)
        r1.addWidget(self.unrealpak_browse)
        tl.addLayout(r1)
        self.iostore_label = QLabel("IoStore: (not found)")
        self.iostore_label.setObjectName("iostore_label")
        self.iostore_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.iostore_browse = QPushButton("Browse")
        r2 = QHBoxLayout()
        r2.addWidget(self.iostore_label, 1)
        r2.addWidget(self.iostore_browse)
        tl.addLayout(r2)
        tools_box.setLayout(tl)
        root.addWidget(tools_box)

        self.mode_tabs = QTabWidget()
        self.single_tab = SingleFileTab(self._log)
        self.dir_tab = DirectoryTab(self._log)
        self.mode_tabs.addTab(self.single_tab, "Single File")
        self.mode_tabs.addTab(self.dir_tab, "Directory")
        root.addWidget(self.mode_tabs)

        self.eula_chk = QCheckBox("I certify I own these files")
        root.addWidget(self.eula_chk)

        self.preview = QPlainTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setObjectName("pak_preview")
        root.addWidget(self.preview)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setObjectName("pak_log")
        root.addWidget(self.log)

    # ----- Connections -----------------------------------------------
    def _connect(self) -> None:
        self.unrealpak_browse.clicked.connect(self._pick_unrealpak)
        self.iostore_browse.clicked.connect(self._pick_iostore)
        self.eula_chk.toggled.connect(self._update_enabled)

    # ----- Helpers ---------------------------------------------------
    def _pick_unrealpak(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "UnrealPak", "", "Executables (*)")
        if path:
            self.unrealpak_path = Path(path)
            self.unrealpak_label.setText(f"UnrealPak: {path}")
            settings.set_pak_path("unrealpak", path)

    def _pick_iostore(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "IoStoreUtilities", "", "Executables (*)"
        )
        if path:
            self.iostore_path = Path(path)
            self.iostore_label.setText(f"IoStore: {path}")
            settings.set_pak_path("iostore", path)

    def _log(self, text: str) -> None:
        self.log.appendPlainText(text)

    def _on_worker_state(self) -> None:
        running, pending = self.worker.status()
        self.dir_tab.update_status(running, pending)
        self._update_enabled()

    def _update_enabled(self) -> None:
        busy = self.worker.is_busy()
        eula = self.eula_chk.isChecked()
        self.single_tab.update_enabled(busy, eula)
        self.dir_tab.update_enabled(busy, eula)

    # ----- Profile & scan --------------------------------------------
    def update_profile(self, profile: Profile | None) -> None:
        self.profile = profile
        if not profile:
            self.unrealpak_path = None
            self.iostore_path = None
            self.unrealpak_label.setText("UnrealPak: (no profile)")
            self.iostore_label.setText("IoStore: (no profile)")
            return
        self._scan()
        proj = profile.project_dir
        self.dir_tab.dir_root.setText(settings.pak_path("dir_root") or str(proj))
        self.dir_tab.compare_a.setText(settings.pak_path("compare_a") or str(proj))
        self.dir_tab.compare_b.setText(settings.pak_path("compare_b") or str(proj))
        self.single_tab.pak_file.setText(settings.pak_path("pak_file") or str(proj))

    def _scan(self) -> None:
        self.unrealpak_path = None
        self.iostore_path = None
        if self.profile:
            root = self.profile.engine_root
            self.unrealpak_path = next(root.rglob("UnrealPak.exe"), None)
            if not self.unrealpak_path:
                self.unrealpak_path = next(root.rglob("UnrealPak"), None)
            self.iostore_path = next(root.rglob("IoStoreUtilities.exe"), None)
            if not self.iostore_path:
                self.iostore_path = next(root.rglob("IoStoreUtilities"), None)
        if not self.unrealpak_path:
            saved = settings.pak_path("unrealpak")
            if saved:
                p = Path(saved)
                if p.exists():
                    self.unrealpak_path = p
        if not self.iostore_path:
            saved = settings.pak_path("iostore")
            if saved:
                p = Path(saved)
                if p.exists():
                    self.iostore_path = p
        if self.unrealpak_path:
            settings.set_pak_path("unrealpak", str(self.unrealpak_path))
        if self.iostore_path:
            settings.set_pak_path("iostore", str(self.iostore_path))
        self.unrealpak_label.setText(
            f"UnrealPak: {self.unrealpak_path}"
            if self.unrealpak_path
            else "UnrealPak: (not found)"
        )
        self.iostore_label.setText(
            f"IoStore: {self.iostore_path}"
            if self.iostore_path
            else "IoStore: (not found)"
        )
