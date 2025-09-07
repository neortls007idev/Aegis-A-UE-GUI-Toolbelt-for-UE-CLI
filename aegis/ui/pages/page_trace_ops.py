from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from aegis.modules.trace_ops import TraceOpsController
from aegis.ui.widgets.command_preview import CommandPreviewWidget


CHANNELS = [
    "Bookmark",
    "Frame",
    "CPU",
    "GPU",
    "LoadTime",
    "File",
    "Net",
    "Counters",
]


class TraceOpsPage(QWidget):
    """Basic UI for Trace Server helpers."""

    def __init__(
        self,
        controller: TraceOpsController,
        log_cb: Callable[[str, str], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.controller = controller
        self.log = log_cb
        self.setObjectName("trace_ops_page")

        # Server widgets
        self.engine_edit = QLineEdit()
        self.engine_edit.setPlaceholderText("Engine/Binaries path")
        self.engine_edit.setObjectName("engine_edit")
        self.browse_engine_btn = QPushButton("Browse…")
        self.browse_engine_btn.setObjectName("browse_engine_btn")
        self.store_edit = QLineEdit()
        self.store_edit.setPlaceholderText("Trace store (optional)")
        self.store_edit.setObjectName("store_edit")
        self.browse_store_btn = QPushButton("Browse…")
        self.browse_store_btn.setObjectName("browse_store_btn")
        self.start_btn = QPushButton("Start Server")
        self.start_btn.setObjectName("start_btn")
        self.stop_btn = QPushButton("Stop Server")
        self.stop_btn.setObjectName("stop_btn")

        # Client flags
        self.host_edit = QLineEdit("127.0.0.1")
        self.host_edit.setObjectName("host_edit")
        self.channel_checks = {name: QCheckBox(name) for name in CHANNELS}
        self.flags_preview = CommandPreviewWidget()

        self._build_layout()
        self._connect()
        self._update_flags()

    # ----- Layout -----
    def _build_layout(self) -> None:
        root = QVBoxLayout(self)

        server_box = QGroupBox("Trace Server")
        ls = QVBoxLayout()
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Engine bin:"))
        row1.addWidget(self.engine_edit, 1)
        row1.addWidget(self.browse_engine_btn)
        ls.addLayout(row1)
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Store:"))
        row2.addWidget(self.store_edit, 1)
        row2.addWidget(self.browse_store_btn)
        ls.addLayout(row2)
        row3 = QHBoxLayout()
        row3.addWidget(self.start_btn)
        row3.addWidget(self.stop_btn)
        ls.addLayout(row3)
        server_box.setLayout(ls)
        root.addWidget(server_box)

        client_box = QGroupBox("Client Connect Helpers")
        lc = QVBoxLayout()
        chan_row = QHBoxLayout()
        for chk in self.channel_checks.values():
            chan_row.addWidget(chk)
        lc.addLayout(chan_row)
        host_row = QHBoxLayout()
        host_row.addWidget(QLabel("Host:"))
        host_row.addWidget(self.host_edit)
        lc.addLayout(host_row)
        lc.addWidget(self.flags_preview)
        client_box.setLayout(lc)
        root.addWidget(client_box)

        root.addStretch(1)

    # ----- Signals -----
    def _connect(self) -> None:
        self.browse_engine_btn.clicked.connect(self._choose_engine)
        self.browse_store_btn.clicked.connect(self._choose_store)
        self.start_btn.clicked.connect(self._start_server)
        self.stop_btn.clicked.connect(self._stop_server)
        self.host_edit.textChanged.connect(lambda _: self._update_flags())
        for chk in self.channel_checks.values():
            chk.stateChanged.connect(lambda _state: self._update_flags())

    # ----- Helpers -----
    def _choose_engine(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Choose Engine Bin")
        if path:
            self.engine_edit.setText(path)
            self._update_flags()

    def _choose_store(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Choose Trace Store")
        if path:
            self.store_edit.setText(path)

    def _start_server(self) -> None:
        engine = Path(self.engine_edit.text())
        store = Path(self.store_edit.text()) if self.store_edit.text() else None
        argv = self.controller.start_server(engine, store)
        self.flags_preview.set_command(" ".join(argv))
        self.log(f"Trace server started: {' '.join(argv)}", "info")

    def _stop_server(self) -> None:
        if self.controller.stop_server():
            self.log("Trace server stopped", "info")
        else:
            self.log("Trace server not running", "warning")

    def _update_flags(self) -> None:
        preset = [name for name, chk in self.channel_checks.items() if chk.isChecked()]
        host = self.host_edit.text().strip() or "127.0.0.1"
        extras = {"statnamedevents": "", "cpuprofilertrace": ""}
        cmd = self.controller.build_trace_flags(preset, host, extras)
        self.flags_preview.set_command(cmd)
