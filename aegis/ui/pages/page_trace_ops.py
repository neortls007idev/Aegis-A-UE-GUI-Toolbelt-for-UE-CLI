from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtCore import Qt
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

from aegis.core.profile import Profile
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
        self.profile: Profile | None = None
        self.engine_label = QLabel("(no profile)")
        self.engine_label.setObjectName("engine_label")
        self.engine_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.trace_name_edit = QLineEdit()
        self.trace_name_edit.setPlaceholderText("Trace name")
        self.trace_name_edit.setObjectName("trace_name_edit")
        self.rebuild_insights_btn = QPushButton("Rebuild & Fix Unreal Insights")
        self.rebuild_insights_btn.setObjectName("rebuild_insights_btn")
        self.launch_insights_btn = QPushButton("Launch Unreal Insights")
        self.launch_insights_btn.setObjectName("launch_insights_btn")
        self.launch_insights_btn.setEnabled(False)
        self.insights_bin: Path | None = None
        self.store_edit = QLineEdit()
        self.store_edit.setPlaceholderText("Trace store")
        self.store_edit.setObjectName("store_edit")
        self.browse_store_btn = QPushButton("Browse…")
        self.browse_store_btn.setObjectName("browse_store_btn")
        self._store_overridden = False
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
        row1.addWidget(self.engine_label, 1)
        ls.addLayout(row1)
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Trace name:"))
        row2.addWidget(self.trace_name_edit, 1)
        row2.addWidget(self.rebuild_insights_btn)
        row2.addWidget(self.launch_insights_btn)
        ls.addLayout(row2)
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Store:"))
        row3.addWidget(self.store_edit, 1)
        row3.addWidget(self.browse_store_btn)
        ls.addLayout(row3)
        row4 = QHBoxLayout()
        row4.addWidget(self.start_btn)
        row4.addWidget(self.stop_btn)
        ls.addLayout(row4)
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
        self.trace_name_edit.textChanged.connect(lambda _: self._update_store())
        self.store_edit.textEdited.connect(self._mark_store_overridden)
        self.browse_store_btn.clicked.connect(self._choose_store)
        self.start_btn.clicked.connect(self._start_server)
        self.stop_btn.clicked.connect(self._stop_server)
        self.rebuild_insights_btn.clicked.connect(self._rebuild_insights)
        self.launch_insights_btn.clicked.connect(self._launch_insights)
        self.host_edit.textChanged.connect(lambda _: self._update_flags())
        for chk in self.channel_checks.values():
            chk.stateChanged.connect(lambda _state: self._update_flags())

    # ----- Helpers -----
    def _choose_store(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Choose Trace Store")
        if path:
            self.store_edit.setText(path)
            self._store_overridden = True

    def _start_server(self) -> None:
        engine = Path(self.engine_label.text())
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

    # ----- Profile -----
    def update_profile(self, profile: Profile | None) -> None:
        self.profile = profile
        if not profile:
            self.engine_label.setText("(no profile)")
            self.store_edit.clear()
            self.launch_insights_btn.setEnabled(False)
            return
        bin_path = profile.engine_root / "Engine" / "Binaries"
        self.engine_label.setText(str(bin_path))
        self.insights_bin = self.controller.find_insights_bin(bin_path)
        self.launch_insights_btn.setEnabled(
            self.insights_bin is not None and self.insights_bin.exists()
        )
        self._store_overridden = False
        self._update_store()

    # ----- Insights helpers -----
    def _rebuild_insights(self) -> None:
        if not self.profile:
            self.log("[insights] No profile selected", "error")
            return
        argv = self.controller.rebuild_insights(self.profile.engine_root)
        self.log(f"Rebuilding Unreal Insights: {' '.join(argv)}", "info")

    def _launch_insights(self) -> None:
        if not self.insights_bin or not self.insights_bin.exists():
            self.log("[insights] Unreal Insights not found", "error")
            return
        argv = self.controller.launch_insights(self.insights_bin)
        self.log(f"Launched Unreal Insights: {' '.join(argv)}", "info")

    def _update_store(self) -> None:
        if self._store_overridden or not self.profile:
            return
        name = self.trace_name_edit.text().strip() or "trace"
        dir_path = self.profile.project_dir / "Unreal Insights" / name
        self.store_edit.setText(str(dir_path))

    def _mark_store_overridden(self) -> None:
        self._store_overridden = True
