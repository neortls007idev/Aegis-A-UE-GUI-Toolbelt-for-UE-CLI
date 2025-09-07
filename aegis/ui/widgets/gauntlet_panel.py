"""UI panel for Gauntlet test runs."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Callable, List

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
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from aegis.core.task_runner import TaskRunner
from aegis.core.profile import Profile
from aegis.modules.gauntlet import Gauntlet


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
        self.runuat_edit = QLineEdit()
        self.runuat_edit.setObjectName("runuat_edit")
        self.runuat_btn = QPushButton("Browse…")
        self.runuat_btn.setObjectName("runuat_btn")
        self.runuat_btn.clicked.connect(self._pick_runuat)

        self.project_edit = QLineEdit()
        self.project_edit.setObjectName("project_edit")
        self.project_btn = QPushButton("Browse…")
        self.project_btn.clicked.connect(self._pick_project)

        self.editor_edit = QLineEdit()
        self.editor_edit.setObjectName("editor_edit")
        self.editor_btn = QPushButton("Browse…")
        self.editor_btn.clicked.connect(self._pick_editor)

        # Scenario
        self.tests_edit = QLineEdit()
        self.tests_edit.setPlaceholderText("MyTest,OtherTest")
        self.clients_spin = QSpinBox()
        self.clients_spin.setMinimum(0)
        self.clients_spin.setValue(1)
        self.server_chk = QCheckBox("Run Server")
        self.platform_combo = QComboBox()
        self.platform_combo.addItems(["Windows", "Android"])
        self.config_combo = QComboBox()
        self.config_combo.addItems(["Development", "Shipping"])
        self.map_edit = QLineEdit()
        self.devices_edit = QLineEdit()
        self.devices_edit.setObjectName("devices_edit")
        self.devices_edit.setPlaceholderText("adb1234,adb5678")
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
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)

        self.dry_run_btn = QPushButton("Dry Run")
        self.dry_run_btn.clicked.connect(self._dry_run)
        self.run_btn = QPushButton("Run")
        self.run_btn.clicked.connect(self._run)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.runner.cancel)

        self._build_layout()

    # ----- UI helpers -----
    def _build_layout(self) -> None:
        root = QVBoxLayout(self)

        paths = QGroupBox("Paths")
        lp = QVBoxLayout(paths)
        lp.addLayout(self._row(QLabel("RunUAT"), self.runuat_edit, self.runuat_btn))
        lp.addLayout(
            self._row(QLabel("UnrealEditor-Cmd"), self.editor_edit, self.editor_btn)
        )
        lp.addLayout(self._row(QLabel("Project"), self.project_edit, self.project_btn))
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
        ls.addLayout(self._row(QLabel("Devices"), self.devices_edit))
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

        tabs = QTabWidget()
        tabs.addTab(self.preview, "Preview")
        tabs.addTab(self.log_view, "Log")
        root.addWidget(tabs, 1)

    def _row(self, *widgets) -> QHBoxLayout:
        layout = QHBoxLayout()
        for w in widgets:
            if isinstance(w, QWidget):
                layout.addWidget(w)
        layout.addStretch(1)
        return layout

    # ----- File pickers -----
    def _pick_runuat(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select RunUAT")
        if path:
            self.runuat_edit.setText(path)

    def _pick_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select .uproject", filter="*.uproject"
        )
        if path:
            self.project_edit.setText(path)

    def _pick_editor(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select UnrealEditor-Cmd")
        if path:
            self.editor_edit.setText(path)

    def _pick_artifacts(self) -> None:
        path = QFileDialog.getExistingDirectory(self, "Select artifacts root")
        if path:
            self.artifacts_edit.setText(path)

    # ----- Profile -----
    def update_profile(self, profile: Profile | None) -> None:
        if not profile:
            return
        runuat = profile.engine_root / "Engine" / "Build" / "BatchFiles" / "RunUAT.bat"
        self.runuat_edit.setText(str(runuat))
        editor = (
            profile.engine_root
            / "Engine"
            / "Binaries"
            / "Win64"
            / "UnrealEditor-Cmd.exe"
        )
        self.editor_edit.setText(str(editor))
        for uproj in profile.project_dir.glob("*.uproject"):
            self.project_edit.setText(str(uproj))
            break
        self._dry_run()

    # ----- Command builders -----
    def _gauntlet(self) -> Gauntlet:
        tests = [t.strip() for t in self.tests_edit.text().split(",") if t.strip()]
        devices: List[str] = []
        for dev in self._device_list():
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
            runuat=Path(self.runuat_edit.text()),
            project=Path(self.project_edit.text()),
            tests=tests,
            platforms=[self.platform_combo.currentText()],
            configuration=self.config_combo.currentText(),
            devices=devices,
            editor_exe=(
                Path(self.editor_edit.text()) if self.editor_edit.text() else None
            ),
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
        self.log_view.clear()

        def on_exit(code: int) -> None:
            self._append_log(f"Exit code {code}", "exit")
            if (
                self.logcat_chk.isChecked()
                and self.platform_combo.currentText() == "Android"
            ):
                for dev in self._device_list():
                    self._pull_logcat(dev)

        self.runner.start(
            argv,
            lambda s: self._append_log(s, "stdout"),
            lambda s: self._append_log(s, "stderr"),
            on_exit,
        )

    def _append_log(self, line: str, stream: str) -> None:
        self.log(stream, line)
        self.log_view.append(f"[{stream}] {line}")

    def _device_list(self) -> List[str]:
        return [d.strip() for d in self.devices_edit.text().split(",") if d.strip()]

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
