"""UI panel for Gauntlet test runs."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional
import sys

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

from aegis.core.profile import Profile
from aegis.core.task_runner import TaskRunner
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
        self.profile: Optional[Profile] = None

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
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 1000)
        self.timeout_spin.setValue(60)

        # Capture
        self.csv_chk = QCheckBox("CSV Profiler")
        self.csv_categories = QLineEdit("FrameTime,GameThreadTime,RenderThreadTime")
        self.insights_chk = QCheckBox("Unreal Insights")
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
        ls.addLayout(self._row(QLabel("Timeout"), self.timeout_spin))
        root.addWidget(scen)

        cap = QGroupBox("Capture & Artifacts")
        lc = QVBoxLayout(cap)
        lc.addLayout(self._row(self.csv_chk, QLabel("Categories"), self.csv_categories))
        lc.addLayout(
            self._row(
                self.insights_chk,
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
    def update_profile(self, profile: Optional[Profile]) -> None:
        self.profile = profile
        if not profile:
            return
        engine = profile.engine_root
        script = "RunUAT.bat" if sys.platform.startswith("win") else "RunUAT.sh"
        runuat = engine / "Engine" / "Build" / "BatchFiles" / script
        if runuat.exists():
            self.runuat_edit.setText(str(runuat))
        editor = (
            engine / "Engine" / "Binaries" / "Win64" / "UnrealEditor-Cmd.exe"
            if sys.platform.startswith("win")
            else engine / "Engine" / "Binaries" / "Linux" / "UnrealEditor"
        )
        if editor.exists():
            self.editor_edit.setText(str(editor))
        proj = next(profile.project_dir.glob("*.uproject"), None)
        if proj:
            self.project_edit.setText(str(proj))

    # ----- Command builders -----
    def _gauntlet(self) -> Gauntlet:
        tests = [t.strip() for t in self.tests_edit.text().split(",") if t.strip()]
        devices: list[str] = []
        cmd_str = None
        if self.csv_chk.isChecked():
            categories = self.csv_categories.text() or "FrameTime"
            cmd_str = (
                "DisableAllScreenMessages;csvprofile start -categories="
                f"{categories};csvprofile stop;quit"
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
            exec_cmds=cmd_str,
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
        self.runner.start(
            argv,
            lambda s: self._append_log(s, "stdout"),
            lambda s: self._append_log(s, "stderr"),
            lambda code: self._append_log(f"Exit code {code}", "exit"),
        )

    def _append_log(self, line: str, stream: str) -> None:
        self.log(stream, line)
        self.log_view.append(f"[{stream}] {line}")
