from __future__ import annotations

from pathlib import Path
from typing import List, Optional

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
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .worker import PakWorker, Task
from .utils import build_iostore_cmd, build_unrealpak_cmd, dest_for


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
            lambda: self.pak_filter.text().strip(),
            lambda: self.dir_unzip_extract.isChecked(),
            self._set_row_status,
            self._on_worker_state,
        )
        self._on_worker_state()

    # ----- UI -----------------------------------------------------------
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
        self._build_single_tab()
        self._build_dir_tab()
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

    def _build_single_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)

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
        self.single_extract_btn = QPushButton("Extract")
        btn_row.addWidget(self.single_list_btn)
        btn_row.addWidget(self.single_extract_btn)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        self.mode_tabs.addTab(tab, "Single File")

    def _build_dir_tab(self) -> None:
        tab = QWidget()
        layout = QVBoxLayout(tab)

        dir_row = QHBoxLayout()
        self.dir_root = QLineEdit()
        self.dir_browse = QPushButton("Browse")
        dir_row.addWidget(QLabel("Root directory"))
        dir_row.addWidget(self.dir_root, 1)
        dir_row.addWidget(self.dir_browse)
        layout.addLayout(dir_row)

        self.dir_recurse = QCheckBox("Recurse subdirectories")
        self.dir_recurse.setChecked(True)
        self.dir_unzip = QCheckBox("Also unzip .obb/.aab files")
        self.dir_unzip.setChecked(True)
        self.dir_unzip_extract = QCheckBox(
            "After unzip, also extract any .pak found inside"
        )
        self.dir_unzip_extract.setChecked(True)
        layout.addWidget(self.dir_recurse)
        layout.addWidget(self.dir_unzip)
        layout.addWidget(self.dir_unzip_extract)

        self.dir_scan_btn = QPushButton("Scan")
        layout.addWidget(self.dir_scan_btn)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Type", "Path", "Size", "Status"])
        self.table.setObjectName("pak_table")
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        self.dir_extract_sel = QPushButton("Extract Selected")
        self.dir_extract_all = QPushButton("Extract All")
        btn_row.addWidget(self.dir_extract_sel)
        btn_row.addWidget(self.dir_extract_all)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        self.status_label = QLabel("Idle")
        layout.addWidget(self.status_label)

        self.mode_tabs.addTab(tab, "Directory")

    # ----- Connections --------------------------------------------------
    def _connect(self) -> None:
        self.unrealpak_browse.clicked.connect(self._pick_unrealpak)
        self.iostore_browse.clicked.connect(self._pick_iostore)

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
        self.single_list_btn.clicked.connect(self._single_list)
        self.single_extract_btn.clicked.connect(self._single_extract)

        self.dir_browse.clicked.connect(self._pick_dir)
        self.dir_scan_btn.clicked.connect(self.scan_directory)
        self.dir_extract_sel.clicked.connect(self._dir_extract_selected)
        self.dir_extract_all.clicked.connect(self._dir_extract_all)

        self.eula_chk.toggled.connect(self._update_extract_enabled)
        self.table.itemSelectionChanged.connect(self._update_extract_enabled)

        self._update_extract_enabled()

    # ----- Helpers ------------------------------------------------------
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

    def _pick_file(self, edit: QLineEdit, filt: str) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Choose file", "", filt)
        if path:
            edit.setText(path)
        self._update_extract_enabled()

    def _pick_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Choose directory")
        if path:
            self.dir_root.setText(path)

    def _log(self, text: str) -> None:
        self.log.appendPlainText(text)

    def _set_row_status(self, row: int, status: str) -> None:
        self.table.setItem(row, 3, QTableWidgetItem(status))

    def _on_worker_state(self) -> None:
        running, pending = self.worker.status()
        if running or pending:
            self.status_label.setText(f"Running {running + pending} tasks...")
        else:
            self.status_label.setText("Idle")
        self._update_extract_enabled()

    def _update_extract_enabled(self) -> None:
        enable = self.eula_chk.isChecked() and not self.worker.is_busy()
        self.single_extract_btn.setEnabled(enable)
        has_rows = self.table.rowCount() > 0
        has_sel = len(self.table.selectedIndexes()) > 0
        self.dir_extract_sel.setEnabled(enable and has_sel)
        self.dir_extract_all.setEnabled(enable and has_rows)

    # ----- Scan ---------------------------------------------------------
    def scan_directory(self) -> None:
        root = Path(self.dir_root.text())
        if not root.is_dir():
            self._log(f"Invalid directory: {root}")
            return
        self.table.setRowCount(0)
        paths = root.rglob("*") if self.dir_recurse.isChecked() else root.glob("*")
        for p in paths:
            if not p.is_file():
                continue
            ext = p.suffix.lower()
            if ext == ".pak":
                kind = "PAK"
            elif ext == ".utoc":
                kind = "UTOC"
            elif ext in {".obb", ".aab"} and self.dir_unzip.isChecked():
                kind = "ZIP"
            else:
                continue
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(kind))
            self.table.setItem(row, 1, QTableWidgetItem(str(p)))
            self.table.setItem(row, 2, QTableWidgetItem(str(p.stat().st_size)))
            self.table.setItem(row, 3, QTableWidgetItem("Pending"))
        self._update_extract_enabled()

    # ----- Task queue ---------------------------------------------------
    def _dir_extract_selected(self) -> None:
        rows = {i.row() for i in self.table.selectedIndexes()}
        self._enqueue_rows(sorted(rows))

    def _dir_extract_all(self) -> None:
        self._enqueue_rows(list(range(self.table.rowCount())))

    def _enqueue_rows(self, rows: List[int]) -> None:
        tasks: List[Task] = []
        for row in rows:
            path = Path(self.table.item(row, 1).text())
            ttype = self.table.item(row, 0).text()
            if ttype == "PAK":
                dest = dest_for(path, "_extracted")
                argv = build_unrealpak_cmd(
                    self.unrealpak_edit.text(),
                    path,
                    "extract",
                    dest,
                    self.pak_filter.text().strip() or None,
                )
                tasks.append(Task("proc", "extract", path, dest, row, argv))
            elif ttype == "UTOC":
                dest = dest_for(path, "_extracted")
                argv = build_iostore_cmd(
                    self.iostore_edit.text(), path, "extract", dest
                )
                tasks.append(Task("proc", "extract", path, dest, row, argv))
            elif ttype == "ZIP":
                dest = dest_for(path, "_unzipped")
                tasks.append(Task("zip", "extract", path, dest, row))
        self.worker.enqueue(tasks)

    def _single_list(self) -> None:
        task = self._single_task("list")
        if task:
            self.worker.enqueue([task])

    def _single_extract(self) -> None:
        if not self.eula_chk.isChecked():
            self._log("Ownership checkbox not ticked")
            return
        task = self._single_task("extract")
        if task:
            self.worker.enqueue([task])

    def _single_task(self, action: str) -> Optional[Task]:
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
                    dest = None if action == "list" else dest_for(path, suf)
                    argv = build_unrealpak_cmd(
                        self.unrealpak_edit.text(),
                        path,
                        action,
                        dest,
                        self.pak_filter.text().strip() or None,
                    )
                    return Task("proc", action, path, dest, None, argv)
                if kind == "iostore":
                    dest = None if action == "list" else dest_for(path, suf)
                    argv = build_iostore_cmd(
                        self.iostore_edit.text(), path, action, dest
                    )
                    return Task("proc", action, path, dest, None, argv)
                tkind = "zip"
                dest = None if action == "list" else dest_for(path, suf)
                return Task(tkind, action, path, dest, None)
        self._log("No file selected")
        return None
