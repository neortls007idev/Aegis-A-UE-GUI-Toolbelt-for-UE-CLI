from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from .directory_tab import DirectoryTab
from .single_tab import SingleFileTab
from .worker import PakWorker


class PakIoStorePanel(QWidget):
    """Panel handling Pak/IoStore operations."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("tab_pak")

        self._build_ui()
        self._connect()

        self.worker = PakWorker(
            self._log,
            self.preview.setPlainText,
            lambda: self.unrealpak_edit.text(),
            lambda: self.iostore_edit.text(),
            lambda: self.single_tab.pak_filter.text().strip(),
            lambda: self.dir_tab.dir_unzip_extract.isChecked(),
            self.dir_tab.set_row_status,
            self._on_worker_state,
        )
        self.single_tab.set_worker(
            self.worker,
            lambda: self.unrealpak_edit.text(),
            lambda: self.iostore_edit.text(),
        )
        self.dir_tab.set_worker(
            self.worker,
            lambda: self.unrealpak_edit.text(),
            lambda: self.iostore_edit.text(),
            lambda: self.single_tab.pak_filter.text().strip(),
        )
        self._on_worker_state()

    # ----- UI ---------------------------------------------------------
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        tools_box = QGroupBox("Tool Paths")
        tl = QVBoxLayout()
        self.unrealpak_edit = QLineEdit()
        self.unrealpak_browse = QPushButton("Browse")
        r1 = QHBoxLayout()
        r1.addWidget(QLabel("UnrealPak.exe"))
        r1.addWidget(self.unrealpak_edit, 1)
        r1.addWidget(self.unrealpak_browse)
        tl.addLayout(r1)
        self.iostore_edit = QLineEdit()
        self.iostore_browse = QPushButton("Browse")
        r2 = QHBoxLayout()
        r2.addWidget(QLabel("IoStoreUtilities.exe"))
        r2.addWidget(self.iostore_edit, 1)
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
            self.unrealpak_edit.setText(path)

    def _pick_iostore(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "IoStoreUtilities", "", "Executables (*)"
        )
        if path:
            self.iostore_edit.setText(path)

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
