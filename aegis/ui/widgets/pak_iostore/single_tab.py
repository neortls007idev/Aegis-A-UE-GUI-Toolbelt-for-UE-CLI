from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .utils import build_iostore_cmd, build_unrealpak_cmd, dest_for
from .worker import PakWorker, Task


class SingleFileTab(QWidget):
    """Sub-widget handling single-file Pak/IoStore actions."""

    def __init__(
        self, log_cb: Callable[[str], None], parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self._log = log_cb
        self.worker: Optional[PakWorker] = None
        self._unrealpak: Callable[[], str] = lambda: ""
        self._iostore: Callable[[], str] = lambda: ""
        self._busy = False
        self._eula = False
        self._build_ui()
        self._connect()

    # ------------------------------------------------------------------
    def set_worker(
        self,
        worker: PakWorker,
        unrealpak: Callable[[], str],
        iostore: Callable[[], str],
    ) -> None:
        self.worker = worker
        self._unrealpak = unrealpak
        self._iostore = iostore

    # ----- UI ---------------------------------------------------------
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.pak_file = QLineEdit()
        self.pak_browse = QPushButton("Browse")
        row_pak = QHBoxLayout()
        row_pak.addWidget(QLabel(".pak"))
        row_pak.addWidget(self.pak_file, 1)
        row_pak.addWidget(self.pak_browse)
        layout.addLayout(row_pak)

        self.pak_filter = QLineEdit()
        self.pak_filter.setObjectName("pak_filter_edit")
        row_filter = QHBoxLayout()
        row_filter.addWidget(QLabel("Filter"))
        row_filter.addWidget(self.pak_filter, 1)
        layout.addLayout(row_filter)

        self.utoc_file = QLineEdit()
        self.utoc_browse = QPushButton("Browse")
        row_utoc = QHBoxLayout()
        row_utoc.addWidget(QLabel(".utoc"))
        row_utoc.addWidget(self.utoc_file, 1)
        row_utoc.addWidget(self.utoc_browse)
        layout.addLayout(row_utoc)

        self.obb_file = QLineEdit()
        self.obb_browse = QPushButton("Browse")
        row_obb = QHBoxLayout()
        row_obb.addWidget(QLabel(".obb"))
        row_obb.addWidget(self.obb_file, 1)
        row_obb.addWidget(self.obb_browse)
        layout.addLayout(row_obb)

        self.aab_file = QLineEdit()
        self.aab_browse = QPushButton("Browse")
        row_aab = QHBoxLayout()
        row_aab.addWidget(QLabel(".aab"))
        row_aab.addWidget(self.aab_file, 1)
        row_aab.addWidget(self.aab_browse)
        layout.addLayout(row_aab)

        btn_row = QHBoxLayout()
        self.single_list_btn = QPushButton("List")
        self.single_search_btn = QPushButton("Search")
        self.single_extract_btn = QPushButton("Extract")
        self.single_validate_btn = QPushButton("Validate")
        btn_row.addWidget(self.single_list_btn)
        btn_row.addWidget(self.single_search_btn)
        btn_row.addWidget(self.single_extract_btn)
        btn_row.addWidget(self.single_validate_btn)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

    def _connect(self) -> None:
        self.pak_browse.clicked.connect(
            lambda: self._pick_file(self.pak_file, "Pak Files (*.pak)")
        )
        self.utoc_browse.clicked.connect(
            lambda: self._pick_file(self.utoc_file, "IoStore Files (*.utoc)")
        )
        self.obb_browse.clicked.connect(
            lambda: self._pick_file(self.obb_file, "OBB Files (*.obb)")
        )
        self.aab_browse.clicked.connect(
            lambda: self._pick_file(self.aab_file, "AAB Files (*.aab)")
        )
        self.single_list_btn.clicked.connect(lambda: self._run("list"))
        self.single_search_btn.clicked.connect(lambda: self._run("search"))
        self.single_extract_btn.clicked.connect(lambda: self._run("extract"))
        self.single_validate_btn.clicked.connect(lambda: self._run("validate"))

    # ----- State ------------------------------------------------------
    def update_enabled(self, busy: bool, eula: bool) -> None:
        self._busy = busy
        self._eula = eula
        enable = eula and not busy
        self.single_list_btn.setEnabled(not busy)
        self.single_search_btn.setEnabled(not busy)
        self.single_extract_btn.setEnabled(enable)
        self.single_validate_btn.setEnabled(enable)

    # ----- Actions ----------------------------------------------------
    def _pick_file(self, edit: QLineEdit, filt: str) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Choose file", "", filt)
        if path:
            edit.setText(path)

    def _run(self, action: str) -> None:
        if not self.worker:
            return
        if action == "extract" and not self._eula:
            self._log("Ownership checkbox not ticked")
            return
        task = self._build_task(action)
        if task:
            self.worker.enqueue([task])

    def _build_task(self, action: str) -> Optional[Task]:
        mapping = [
            (self.pak_file, "unrealpak", "_extracted"),
            (self.utoc_file, "iostore", "_extracted"),
            (self.obb_file, "zip", "_unzipped"),
            (self.aab_file, "zip", "_unzipped"),
        ]
        for edit, kind, suf in mapping:
            if edit.text():
                path = Path(edit.text())
                if not path.exists():
                    self._log(f"Missing file: {path}")
                    return None
                if kind == "unrealpak":
                    mode = (
                        action if action in {"list", "extract", "validate"} else "list"
                    )
                    dest = (
                        None
                        if action in {"list", "search", "validate"}
                        else dest_for(path, suf)
                    )
                    argv = build_unrealpak_cmd(
                        self._unrealpak(),
                        path,
                        mode,
                        dest,
                        self.pak_filter.text().strip() or None,
                    )
                    return Task("proc", action, path, dest, None, argv)
                if kind == "iostore":
                    mode = (
                        action if action in {"list", "extract", "validate"} else "list"
                    )
                    dest = (
                        None
                        if action in {"list", "search", "validate"}
                        else dest_for(path, suf)
                    )
                    argv = build_iostore_cmd(self._iostore(), path, mode, dest)
                    return Task("proc", action, path, dest, None, argv)
                tkind = "zip"
                dest = (
                    None
                    if action in {"list", "search", "validate"}
                    else dest_for(path, suf)
                )
                return Task(tkind, action, path, dest, None)
        self._log("No file selected")
        return None
