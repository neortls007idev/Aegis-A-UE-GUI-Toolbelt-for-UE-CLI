"""UI panel for Gauntlet test runs."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable, List

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
)

from aegis.core.task_runner import TaskRunner
from aegis.core.profile import Profile
from aegis.modules.gauntlet import Gauntlet
from aegis.ui.models.build_defaults import DEFAULT_CONFIGS, DEFAULT_PLATFORMS
from aegis.ui.widgets.device_list_widget import DeviceListWidget


class GauntletPanel(QWidget):
    """Simple Gauntlet runner."""

    def __init__(
        self,
        runner: TaskRunner,
        log_cb: Callable[[str, str], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.runner = runner
        self.log = log_cb

        # Paths
        self.runuat_label = QLabel("RunUAT: (not found)")
        self.runuat_label.setObjectName("runuat_lbl")
        self.runuat_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.runuat_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.editor_label = QLabel("UnrealEditor-Cmd: (not found)")
        self.editor_label.setObjectName("editor_lbl")
        self.editor_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.editor_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.project_path: Path | None = None
        self.runuat_path: Path | None = None
        self.editor_path: Path | None = None

        # Scenario
        self.tests_edit = QLineEdit()
        self.tests_edit.setPlaceholderText("MyTest,OtherTest")
        self.clients_spin = QSpinBox()
        self.clients_spin.setMinimum(0)
        self.clients_spin.setValue(1)
        self.server_chk = QCheckBox("Run Server")
        self.platform_combo = QComboBox()
        self.config_combo = QComboBox()
        self.map_edit = QLineEdit()
        self.device_panel = DeviceListWidget(runner, log_cb)
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 1000)
        self.timeout_spin.setValue(60)

        # Capture
        self.csv_chk = QCheckBox("CSV Profiler")
        self.csv_categories = QLineEdit("FrameTime,GameThreadTime,RenderThreadTime")
        self.insights_chk = QCheckBox("Unreal Insights")
        self.trace_categories = QLineEdit("Bookmark,Frame,CPU,File,LoadTime,Memory")
        self.trace_categories.setObjectName("trace_categories")
        self.trace_host = QLineEdit("127.0.0.1")
        self.trace_port = QLineEdit("1980")
        self.logcat_chk = QCheckBox("Pull Android logcat")
        self.artifacts_edit = QLineEdit()
        self.artifacts_edit.setText(".aegis/artifacts/gauntlet")
        self.artifacts_btn = QPushButton("Browse…")
        self.artifacts_btn.clicked.connect(self._pick_artifacts)

        # Command + log
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)

        self.dry_run_btn = QPushButton("Dry Run")
        self.dry_run_btn.clicked.connect(self._dry_run)
        self.run_btn = QPushButton("Run")
        self.run_btn.clicked.connect(self._run)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.runner.cancel)

        self._populate_build_options(None)
        self._build_layout()

    # ----- UI helpers -----
    def _populate_build_options(self, profile: Profile | None) -> None:
        plats = (
            profile.build_platforms
            if profile and profile.build_platforms
            else DEFAULT_PLATFORMS
        )
        cfgs = (
            profile.build_configs
            if profile and profile.build_configs
            else DEFAULT_CONFIGS
        )
        self.platform_combo.clear()
        self.platform_combo.addItems(plats)
        self.config_combo.clear()
        self.config_combo.addItems(cfgs)

    def _build_layout(self) -> None:
        root = QVBoxLayout(self)

        paths = QGroupBox("Paths")
        lp = QHBoxLayout(paths)
        lp.addWidget(self.runuat_label)
        lp.addSpacing(8)
        lp.addWidget(self.editor_label)
        lp.addStretch(1)
        root.addWidget(paths)

        scen = QGroupBox("Scenario")
        ls = QVBoxLayout(scen)
        ls.addLayout(self._row(QLabel("Tests"), self.tests_edit))
        ls.addLayout(self._row(QLabel("Clients"), self.clients_spin, self.server_chk))
        ls.addLayout(
            self._row(
                QLabel("Platform"),
                self.platform_combo,
                QLabel("Config"),
                self.config_combo,
            )
        )
        ls.addLayout(self._row(QLabel("Map"), self.map_edit))
        ls.addLayout(self._row(self.device_panel.list_btn))
        ls.addWidget(self.device_panel)
        ls.addLayout(self._row(QLabel("Timeout"), self.timeout_spin))
        root.addWidget(scen)

        cap = QGroupBox("Capture & Artifacts")
        lc = QVBoxLayout(cap)
        lc.addLayout(self._row(self.csv_chk, QLabel("Categories"), self.csv_categories))
        lc.addLayout(
            self._row(
                self.insights_chk,
                QLabel("Categories"),
                self.trace_categories,
                QLabel("Host"),
                self.trace_host,
                QLabel("Port"),
                self.trace_port,
            )
        )
        lc.addWidget(self.logcat_chk)
        lc.addLayout(
            self._row(QLabel("Artifacts"), self.artifacts_edit, self.artifacts_btn)
        )
        root.addWidget(cap)

        ctrl = QHBoxLayout()
        ctrl.addWidget(self.dry_run_btn)
        ctrl.addWidget(self.run_btn)
        ctrl.addWidget(self.stop_btn)
        ctrl.addStretch(1)
        root.addLayout(ctrl)

        root.addWidget(self.preview, 1)

    def _row(self, *widgets) -> QHBoxLayout:
        layout = QHBoxLayout()
        for w in widgets:
            if isinstance(w, QWidget):
                layout.addWidget(w)
        layout.addStretch(1)
        return layout

    # ----- File pickers -----
    def _pick_artifacts(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select artifacts root")
        if path:
            self.artifacts_edit.setText(path)

    # ----- Profile -----
    def update_profile(self, profile: Profile | None) -> None:
        self._populate_build_options(profile)
        self.device_panel.update_profile(profile)
        if not profile:
            self.runuat_label.setText("RunUAT: (not found)")
            self.editor_label.setText("UnrealEditor-Cmd: (not found)")
            self.project_path = None
            self.runuat_path = None
            self.editor_path = None
            return
        runuat = profile.engine_root / "Engine" / "Build" / "BatchFiles" / "RunUAT.bat"
        self.runuat_label.setText(f"RunUAT: {runuat}")
        self.runuat_path = runuat
        editor = (
            profile.engine_root
            / "Engine"
            / "Binaries"
            / "Win64"
            / "UnrealEditor-Cmd.exe"
        )
        self.editor_label.setText(f"UnrealEditor-Cmd: {editor}")
        self.editor_path = editor
        self.project_path = None
        for uproj in profile.project_dir.glob("*.uproject"):
            self.project_path = uproj
            break
        self._dry_run()

    # ----- Command builders -----
    def _gauntlet(self) -> Gauntlet:
        tests = [t.strip() for t in self.tests_edit.text().split(",") if t.strip()]
        devices: List[str] = []
        for dev in self.device_panel.selected_devices():
            if self.platform_combo.currentText() == "Android":
                devices.append(f"Android@{dev}")
            else:
                devices.append(dev)
        cmds = ["DisableAllScreenMessages", "t.MaxFPS 0"]
        if self.csv_chk.isChecked():
            categories = self.csv_categories.text() or "FrameTime"
            cmds.append(f"csvprofile start -categories={categories}")
            cmds.append("csvprofile stop")
        cmds.append("quit")
        trace_cats = (
            self.trace_categories.text() if self.insights_chk.isChecked() else None
        )
        trace_host = self.trace_host.text() if self.insights_chk.isChecked() else None
        trace_port = (
            int(self.trace_port.text()) if self.insights_chk.isChecked() else None
        )
        return Gauntlet(
            runuat=self.runuat_path or Path(),
            project=self.project_path or Path(),
            tests=tests,
            platforms=[self.platform_combo.currentText()],
            configuration=self.config_combo.currentText(),
            devices=devices,
            editor_exe=self.editor_path,
            timeout_minutes=int(self.timeout_spin.value()),
            exec_cmds=";".join(cmds),
            trace_categories=trace_cats,
            trace_host=trace_host,
            trace_port=trace_port,
        )

    def _compose(self) -> list[str]:
        return self._gauntlet().argv()

    def _dry_run(self) -> None:
        argv = self._compose()
        self.preview.setPlainText("\n".join(argv))

    def _run(self) -> None:
        argv = self._compose()
        self.preview.setPlainText("\n".join(argv))

        def on_exit(code: int) -> None:
            self._append_log(f"Exit code {code}", "exit")
            if (
                self.logcat_chk.isChecked()
                and self.platform_combo.currentText() == "Android"
            ):
                for dev in self.device_panel.selected_devices():
                    self._pull_logcat(dev)

        self.runner.start(
            argv,
            lambda s: self._append_log(s, "stdout"),
            lambda s: self._append_log(s, "stderr"),
            on_exit,
        )

    def _append_log(self, line: str, stream: str) -> None:
        self.log(stream, line)

    def _pull_logcat(self, device: str) -> None:
        art = Path(self.artifacts_edit.text()) / "devices" / device
        art.mkdir(parents=True, exist_ok=True)
        out_file = art / "logcat.txt"
        try:
            with out_file.open("w", encoding="utf-8") as fh:
                subprocess.run(
                    ["adb", "-s", device, "logcat", "-d"],
                    stdout=fh,
                    stderr=subprocess.STDOUT,
                )
            self._append_log(f"Pulled logcat for {device}", "stdout")
        except OSError as exc:
            self._append_log(f"adb failed for {device}: {exc}", "stderr")
