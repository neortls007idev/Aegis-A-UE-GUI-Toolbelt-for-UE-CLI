"""UI panel for RunUAT BuildGraph presets."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict

from PySide6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QComboBox,
)

from aegis.core.task_runner import TaskRunner
from aegis.core.profile import Profile
from aegis.modules.buildgraph import BuildGraph


PRESETS: Dict[str, list[str]] = {
    "Game-Windows-Package": ["Project", "Platform", "Config", "ArchiveDir"],
    "Game-Android-AAB": [
        "Project",
        "Platform",
        "Config",
        "Keystore",
        "KeyAlias",
        "KeyStorePassEnvVar",
        "ArchiveDir",
    ],
    "Game-Android-OBB": [
        "Project",
        "Platform",
        "Config",
        "Keystore",
        "KeyAlias",
        "KeyStorePassEnvVar",
        "ArchiveDir",
    ],
    "Tools-Pack": ["ArchiveDir"],
}


class BuildGraphPanel(QWidget):
    """Simple BuildGraph runner with preset vars."""

    def __init__(
        self,
        runner: TaskRunner,
        log_cb: Callable[[str, str], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.runner = runner
        self.log = log_cb

        self.runuat_edit = QLineEdit()
        self.runuat_btn = QPushButton("Browse…")
        self.runuat_btn.clicked.connect(self._pick_runuat)

        self.script_combo = QComboBox()
        self.script_combo.addItems(list(PRESETS.keys()))
        self.script_combo.currentTextChanged.connect(self._rebuild_vars)

        self.vars_form = QFormLayout()
        self.vars_edits: Dict[str, QLineEdit] = {}
        self._rebuild_vars(self.script_combo.currentText())

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

    # ----- UI -----
    def _build_layout(self) -> None:
        root = QVBoxLayout(self)
        paths = QGroupBox("Paths & Preset")
        lp = QVBoxLayout(paths)
        lp.addLayout(self._row(QLabel("RunUAT"), self.runuat_edit, self.runuat_btn))
        lp.addLayout(self._row(QLabel("Preset"), self.script_combo))
        lp.addLayout(self.vars_form)
        root.addWidget(paths)

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

    def _rebuild_vars(self, preset: str) -> None:
        while self.vars_form.rowCount():
            self.vars_form.removeRow(0)
        self.vars_edits.clear()
        for key in PRESETS[preset]:
            edit = QLineEdit()
            self.vars_form.addRow(QLabel(key), edit)
            self.vars_edits[key] = edit

    # ----- File pickers -----
    def _pick_runuat(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select RunUAT")
        if path:
            self.runuat_edit.setText(path)

    # ----- Profile -----
    def update_profile(self, profile: Profile | None) -> None:
        if not profile:
            return
        runuat = profile.engine_root / "Engine" / "Build" / "BatchFiles" / "RunUAT.bat"
        self.runuat_edit.setText(str(runuat))
        proj_edit = self.vars_edits.get("Project")
        if proj_edit:
            for uproj in profile.project_dir.glob("*.uproject"):
                proj_edit.setText(str(uproj))
                break
        self._dry_run()

    # ----- Compose -----
    def _buildgraph(self) -> BuildGraph:
        preset = self.script_combo.currentText()
        script = Path(f"docs/buildgraph/presets/{preset.lower().replace('-', '_')}.xml")
        sets = {k: e.text() for k, e in self.vars_edits.items() if e.text()}
        return BuildGraph(
            runuat=Path(self.runuat_edit.text()),
            script=script,
            target="ArchiveClient" if preset != "Tools-Pack" else "ArchiveTools",
            sets=sets,
            clean=True,
        )

    def _compose(self) -> list[str]:
        return self._buildgraph().argv()

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
