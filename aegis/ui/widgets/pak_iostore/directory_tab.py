from __future__ import annotations

from pathlib import Path
from typing import Callable, List, Optional

from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QCheckBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .utils import build_iostore_cmd, build_unrealpak_cmd, dest_for
from .worker import PakWorker, Task


class DirectoryTab(QWidget):
    """Sub-widget handling directory scans and batch operations."""

    def __init__(
        self, log_cb: Callable[[str], None], parent: Optional[QWidget] = None
    ) -> None:
        super().__init__(parent)
        self._log = log_cb
        self.worker: Optional[PakWorker] = None
        self._get_unrealpak: Callable[[], str] = lambda: ""
        self._get_iostore: Callable[[], str] = lambda: ""
        self._get_filter: Callable[[], str] = lambda: ""
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
        filt: Callable[[], str],
    ) -> None:
        self.worker = worker
        self._get_unrealpak = unrealpak
        self._get_iostore = iostore
        self._get_filter = filt

    # ----- UI ---------------------------------------------------------
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

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

        self.dir_search = QLineEdit()
        self.dir_search.setPlaceholderText("Search...")
        layout.addWidget(self.dir_search)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Type", "Path", "Size", "Status"])
        self.table.setObjectName("pak_table")
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        self.dir_extract_sel = QPushButton("Extract Selected")
        self.dir_extract_all = QPushButton("Extract All")
        self.dir_validate_sel = QPushButton("Validate Selected")
        self.dir_validate_all = QPushButton("Validate All")
        btn_row.addWidget(self.dir_extract_sel)
        btn_row.addWidget(self.dir_extract_all)
        btn_row.addWidget(self.dir_validate_sel)
        btn_row.addWidget(self.dir_validate_all)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        cmp_box = QGroupBox("Compare Builds")
        cmp_layout = QVBoxLayout()
        row_a = QHBoxLayout()
        self.compare_a = QLineEdit()
        self.compare_a_browse = QPushButton("Browse")
        row_a.addWidget(QLabel("Dir A"))
        row_a.addWidget(self.compare_a, 1)
        row_a.addWidget(self.compare_a_browse)
        cmp_layout.addLayout(row_a)
        row_b = QHBoxLayout()
        self.compare_b = QLineEdit()
        self.compare_b_browse = QPushButton("Browse")
        row_b.addWidget(QLabel("Dir B"))
        row_b.addWidget(self.compare_b, 1)
        row_b.addWidget(self.compare_b_browse)
        cmp_layout.addLayout(row_b)
        self.compare_btn = QPushButton("Compare Builds")
        cmp_layout.addWidget(self.compare_btn)
        cmp_box.setLayout(cmp_layout)
        layout.addWidget(cmp_box)

        self.status_label = QLabel("Idle")
        layout.addWidget(self.status_label)

    def _connect(self) -> None:
        self.dir_browse.clicked.connect(self._pick_dir)
        self.dir_scan_btn.clicked.connect(self.scan_directory)
        self.dir_search.textChanged.connect(self._filter_table)
        self.dir_extract_sel.clicked.connect(lambda: self._extract(True))
        self.dir_extract_all.clicked.connect(lambda: self._extract(False))
        self.dir_validate_sel.clicked.connect(lambda: self._validate(True))
        self.dir_validate_all.clicked.connect(lambda: self._validate(False))
        self.compare_a_browse.clicked.connect(
            lambda: self._pick_dir_into(self.compare_a)
        )
        self.compare_b_browse.clicked.connect(
            lambda: self._pick_dir_into(self.compare_b)
        )
        self.compare_btn.clicked.connect(self._compare_builds)
        self.table.itemSelectionChanged.connect(self._update_buttons)

    # ----- State ------------------------------------------------------
    def update_enabled(self, busy: bool, eula: bool) -> None:
        self._busy = busy
        self._eula = eula
        self._update_buttons()

    def _update_buttons(self) -> None:
        busy = self._busy
        eula = self._eula
        has_rows = self.table.rowCount() > 0
        has_sel = len(self.table.selectedIndexes()) > 0
        enable = eula and not busy
        self.dir_scan_btn.setEnabled(not busy)
        self.dir_extract_sel.setEnabled(enable and has_sel)
        self.dir_extract_all.setEnabled(enable and has_rows)
        self.dir_validate_sel.setEnabled(enable and has_sel)
        self.dir_validate_all.setEnabled(enable and has_rows)
        self.compare_btn.setEnabled(not busy)

    def update_status(self, running: int, pending: int) -> None:
        if running or pending:
            self.status_label.setText(f"Running {running + pending} tasks...")
        else:
            self.status_label.setText("Idle")

    def set_row_status(self, row: int, status: str) -> None:
        self.table.setItem(row, 3, QTableWidgetItem(status))

    # ----- Actions ----------------------------------------------------
    def _pick_dir(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Choose directory")
        if path:
            self.dir_root.setText(path)

    def _pick_dir_into(self, edit: QLineEdit) -> None:
        path = QFileDialog.getExistingDirectory(self, "Choose directory")
        if path:
            edit.setText(path)

    def _filter_table(self, text: str) -> None:
        text = text.lower()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 1)
            self.table.setRowHidden(row, text not in item.text().lower())

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
                name = p.name.lower()
                if "dlc" in name or name.endswith("_p.pak"):
                    kind = "PAK-DLC"
                else:
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
        self._update_buttons()

    def _rows(self, selected: bool) -> List[int]:
        if selected:
            return sorted({i.row() for i in self.table.selectedIndexes()})
        return list(range(self.table.rowCount()))

    def _extract(self, selected: bool) -> None:
        if not self.worker:
            return
        rows = self._rows(selected)
        tasks = self._build_tasks(rows, "extract")
        if tasks:
            self.worker.enqueue(tasks)

    def _validate(self, selected: bool) -> None:
        if not self.worker:
            return
        rows = self._rows(selected)
        tasks = self._build_tasks(rows, "validate")
        if tasks:
            self.worker.enqueue(tasks)

    def _build_tasks(self, rows: List[int], action: str) -> List[Task]:
        tasks: List[Task] = []
        for row in rows:
            path = Path(self.table.item(row, 1).text())
            ttype = self.table.item(row, 0).text()
            if ttype.startswith("PAK"):
                dest = None if action != "extract" else dest_for(path, "_extracted")
                argv = build_unrealpak_cmd(
                    self._get_unrealpak(),
                    path,
                    action,
                    dest,
                    self._get_filter() or None,
                )
                tasks.append(Task("proc", action, path, dest, row, argv))
            elif ttype.startswith("UTOC"):
                dest = None if action != "extract" else dest_for(path, "_extracted")
                argv = build_iostore_cmd(self._get_iostore(), path, action, dest)
                tasks.append(Task("proc", action, path, dest, row, argv))
            elif ttype == "ZIP":
                dest = None if action != "extract" else dest_for(path, "_unzipped")
                tasks.append(Task("zip", action, path, dest, row))
        return tasks

    def _compare_builds(self) -> None:
        if not self.worker:
            return
        a = Path(self.compare_a.text())
        b = Path(self.compare_b.text())
        if not a.is_dir() or not b.is_dir():
            self._log("Invalid compare directories")
            return
        task = Task("cmp", "compare", a, b, None)
        self.worker.enqueue([task])
