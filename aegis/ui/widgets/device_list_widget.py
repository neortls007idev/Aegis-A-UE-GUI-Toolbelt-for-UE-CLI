"""Widget for listing and selecting connected devices."""

from __future__ import annotations

import subprocess
from typing import Callable, List

from PySide6.QtWidgets import (
    QAbstractItemView,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from aegis.core.profile import Profile
from aegis.core.task_runner import TaskRunner
from aegis.modules.uaft import Uaft


class DeviceListWidget(QWidget):
    """List connected devices via UAFT."""

    def __init__(
        self,
        runner: TaskRunner,
        log_cb: Callable[[str, str], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.runner = runner
        self.log = log_cb
        self.uaft: Uaft | None = None
        self.setObjectName("device_panel")

        self.list_btn = QPushButton("List Devices")
        self.list_btn.setObjectName("list_devices_btn")
        self.list_btn.clicked.connect(self._list_devices)

        self.table = QTableWidget(0, 3)
        self.table.setObjectName("devices_table")
        self.table.setHorizontalHeaderLabels(["Make", "Model", "Serial"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.MultiSelection)
        self.table.horizontalHeader().setStretchLastSection(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self.table)

    # ----- Profile -----
    def update_profile(self, profile: Profile | None) -> None:
        self.uaft = Uaft(profile.engine_root, profile.project_dir) if profile else None

    # ----- Actions -----
    def _list_devices(self) -> None:
        if not self.uaft:
            self.log("[uaft] UAFT not configured", "error")
            return
        lines: List[str] = []
        argv = self.uaft.devices_argv()
        self.log(f"[uaft] {' '.join(argv)}", "info")
        self.runner.start(
            argv,
            on_stdout=lines.append,
            on_stderr=lambda s: self.log(f"[uaft] {s}", "error"),
            on_exit=lambda code: self._on_devices_exit(code, lines),
        )

    def _on_devices_exit(self, code: int, lines: List[str]) -> None:
        if code != 0:
            self.log(f"[uaft] exit code {code}", "error")
            return
        devs = Uaft.parse_devices(lines)
        self.table.setRowCount(0)
        for serial in devs:
            make, model = self._adb_device_info(serial)
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(make))
            self.table.setItem(row, 1, QTableWidgetItem(model))
            self.table.setItem(row, 2, QTableWidgetItem(serial))
        if devs:
            self.table.selectRow(0)

    def selected_devices(self) -> List[str]:
        return [
            self.table.item(idx.row(), 2).text()
            for idx in self.table.selectionModel().selectedRows()
        ]

    def _adb_device_info(self, serial: str) -> tuple[str, str]:
        try:
            make = subprocess.run(
                ["adb", "-s", serial, "shell", "getprop", "ro.product.manufacturer"],
                capture_output=True,
                text=True,
                check=False,
            ).stdout.strip()
            model = subprocess.run(
                ["adb", "-s", serial, "shell", "getprop", "ro.product.model"],
                capture_output=True,
                text=True,
                check=False,
            ).stdout.strip()
            return make or "?", model or serial
        except Exception:
            return "?", serial
