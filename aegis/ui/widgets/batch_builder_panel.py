"""Panel for constructing and running batches of build tasks.

Handles queueing, profile integration, and delegates BuildCookRun overrides
to :class:`UatOverrideWidget`.
"""

from __future__ import annotations

import sys
import shlex
from pathlib import Path
from typing import Callable, Optional, Set
import shutil

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QProgressBar,
    QCheckBox,
    QGroupBox,
)

from aegis.core.profile import Profile
from aegis.core.task_runner import TaskRunner
from aegis.modules.ubt import Ubt
from aegis.modules.uat import Uat
from aegis.ui.widgets.uat_override_widget import UatOverrideWidget
from aegis.ui.widgets.task_queue_widget import TaskQueueWidget
from aegis.ui.models.queued_task import QueuedTask


# Include server and editor configurations by default
DEFAULT_CONFIGS = [
    "Debug",
    "DebugGame",
    "DebugServer",
    "DebugEditor",
    "Development",
    "DevelopmentServer",
    "DevelopmentEditor",
    "Test",
    "TestServer",
    "TestEditor",
    "Shipping",
    "ShippingServer",
    "ShippingEditor",
]

# Mac is included for editor builds
DEFAULT_PLATFORMS = ["Win64", "Linux", "Mac", "Android"]

# Tasks that support manual command editing
EDITABLE_TAGS = {
    "build",
    "clean",
    "rebuild",
    "cook",
    "stage",
    "package",
    "ddc-build",
    "ddc-clean",
    "ddc-rebuild",
}


class BatchBuilderPanel(QWidget):
    """Batch builder UI with queued tasks and progress tracking."""

    batch_started = Signal(int)
    batch_progress = Signal(int)
    batch_finished = Signal()
    tasks_changed = Signal()

    def __init__(
        self,
        runner: TaskRunner,
        log_cb: Callable[[str, str], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.runner = runner
        self.log = log_cb
        self.profile: Profile | None = None
        self.ubt: Ubt | None = None
        self.uat: Uat | None = None

        self.current_index = -1
        self.cancel_requested = False

        main_layout = QVBoxLayout(self)

        path_layout = QHBoxLayout()
        self.ubt_label = QLabel("UBT: (not found)")
        self.ubt_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.uat_label = QLabel("UAT: (not found)")
        self.uat_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        path_layout.addWidget(self.ubt_label)
        path_layout.addSpacing(8)
        path_layout.addWidget(self.uat_label)
        path_layout.addStretch(1)
        main_layout.addLayout(path_layout)

        layout = QHBoxLayout()
        main_layout.addLayout(layout)

        # ----- Configs -----
        cfg_layout = QVBoxLayout()
        cfg_layout.addWidget(QLabel("Config"))
        self.config_list = QListWidget()
        self.config_list.setSelectionMode(QListWidget.SingleSelection)
        self.config_list.currentTextChanged.connect(self._on_config_changed)
        cfg_layout.addWidget(self.config_list)
        btn_add_cfg = QPushButton("Add…")
        btn_add_cfg.clicked.connect(self._add_config)
        cfg_layout.addWidget(btn_add_cfg)
        layout.addLayout(cfg_layout)

        # ----- Platforms -----
        plat_layout = QVBoxLayout()
        plat_layout.addWidget(QLabel("Platform"))
        self.platform_list = QListWidget()
        self.platform_list.setSelectionMode(QListWidget.SingleSelection)
        plat_layout.addWidget(self.platform_list)
        btn_add_plat = QPushButton("Add…")
        btn_add_plat.clicked.connect(self._add_platform)
        plat_layout.addWidget(btn_add_plat)
        layout.addLayout(plat_layout)

        # ----- Overrides -----
        over_group = QGroupBox("Manual Overrides")
        over_layout = QVBoxLayout(over_group)
        self.uat_overrides = UatOverrideWidget()
        over_layout.addWidget(self.uat_overrides)
        layout.addWidget(over_group)

        # ----- Actions -----
        act_layout = QVBoxLayout()
        btn_clean = QPushButton("Clean")
        btn_build = QPushButton("Build")
        btn_rebuild = QPushButton("Rebuild")
        btn_cook = QPushButton("Cook")
        btn_stage = QPushButton("Stage")
        btn_package = QPushButton("Package")
        btn_ddc_build = QPushButton("Build DDC")
        btn_ddc_clean = QPushButton("Clean DDC")
        btn_ddc_rebuild = QPushButton("Rebuild DDC")
        for text, btn in [
            ("clean", btn_clean),
            ("build", btn_build),
            ("rebuild", btn_rebuild),
            ("cook", btn_cook),
            ("stage", btn_stage),
            ("package", btn_package),
            ("ddc-build", btn_ddc_build),
            ("ddc-clean", btn_ddc_clean),
            ("ddc-rebuild", btn_ddc_rebuild),
        ]:
            act_layout.addWidget(btn)
            btn.clicked.connect(lambda _, t=text: self._queue_task(t))
        act_layout.addStretch()
        layout.addLayout(act_layout)

        # ----- Queue -----
        self.queue = TaskQueueWidget(self._argv_for)
        self.queue.start_requested.connect(self._start_batch)
        self.queue.cancel_requested.connect(self.cancel_batch)
        self.queue.tasks_changed.connect(self.tasks_changed)
        layout.addWidget(self.queue)

    # ----- Profile -----
    def update_profile(self, profile: Profile | None) -> None:
        self.profile = profile
        self.ubt = Ubt(profile.engine_root, profile.project_dir) if profile else None
        self.uat = Uat(profile.engine_root, profile.project_dir) if profile else None
        self.config_list.clear()
        self.platform_list.clear()
        self.uat_overrides.clear()
        if not profile:
            cfgs = DEFAULT_CONFIGS
            plats = DEFAULT_PLATFORMS
            self.ubt_label.setText("UBT: (no profile)")
            self.uat_label.setText("UAT: (no profile)")
        else:
            cfgs = profile.build_configs or DEFAULT_CONFIGS
            plats = profile.build_platforms or DEFAULT_PLATFORMS
            try:
                self.ubt_label.setText(f"UBT: {self.ubt.exe()}")
            except Exception:
                self.ubt_label.setText("UBT: (not found)")
            try:
                self.uat_label.setText(f"UAT: {self.uat.exe()}")
            except Exception:
                self.uat_label.setText("UAT: (not found)")
        for c in cfgs:
            self.config_list.addItem(QListWidgetItem(c))
        for p in plats:
            self.platform_list.addItem(QListWidgetItem(p))
        if self.config_list.count():
            self.config_list.setCurrentRow(0)

    # ----- Configs/Platforms -----
    def _add_config(self) -> None:
        name, ok = QInputDialog.getText(self, "Add Config", "Config name:")
        if ok and name:
            self.config_list.addItem(QListWidgetItem(name))
            if self.profile:
                self.profile.build_configs = self._current_configs()

    def _add_platform(self) -> None:
        name, ok = QInputDialog.getText(self, "Add Platform", "Platform name:")
        if ok and name:
            self.platform_list.addItem(QListWidgetItem(name))
            if self.profile:
                self.profile.build_platforms = self._current_platforms()

    def _current_configs(self) -> list[str]:
        return [
            self.config_list.item(i).text() for i in range(self.config_list.count())
        ]

    def _current_platforms(self) -> list[str]:
        return [
            self.platform_list.item(i).text() for i in range(self.platform_list.count())
        ]

    def _allowed_platforms_for_config(self, cfg: str) -> Optional[Set[str]]:
        if cfg.endswith("Editor"):
            return {"Win64", "Linux", "Mac"}
        return None

    def _on_config_changed(self, text: str) -> None:
        allowed = self._allowed_platforms_for_config(text)
        for i in range(self.platform_list.count()):
            item = self.platform_list.item(i)
            if allowed and item.text() not in allowed:
                item.setHidden(True)
            else:
                item.setHidden(False)

    # ----- Queue management -----
    def _queue_task(self, tag: str) -> None:
        cfg_item = self.config_list.currentItem()
        plat_item = self.platform_list.currentItem()
        if not cfg_item or not plat_item:
            self.log("[batch] Select config and platform", "error")
            return
        if "Editor" in cfg_item.text() and plat_item.text() not in {
            "Win64",
            "Linux",
            "Mac",
        }:
            self.log("[batch] Editor builds require Win64, Linux, or Mac", "error")
            return
        clean = False
        if tag in {"cook", "stage", "package"}:
            mode, ok = QInputDialog.getItem(
                self,
                "Mode",
                "Mode:",
                ["Iterative", "Clean"],
                0,
                False,
            )
            if not ok:
                return
            clean = mode == "Clean"
        widget = QWidget()
        row = QHBoxLayout(widget)
        edit_chk = QCheckBox("Edit")
        edit_chk.setAutoExclusive(False)
        edit_chk.setTristate(False)
        if tag not in EDITABLE_TAGS:
            edit_chk.setEnabled(False)
            edit_chk.setToolTip("Manual edit not available")
        else:
            edit_chk.setToolTip("Edit command before running")
        row.addWidget(edit_chk)
        label = f"{tag} {cfg_item.text()} {plat_item.text()}"
        if clean:
            label += " (clean)"
        lbl = QLabel(label)
        if tag not in EDITABLE_TAGS:
            lbl.setEnabled(False)
        row.addWidget(lbl)
        bar = QProgressBar()
        bar.setRange(0, 1)
        bar.setValue(0)
        row.addWidget(bar)
        item = QListWidgetItem()
        task = QueuedTask(
            tag, cfg_item.text(), plat_item.text(), item, widget, bar, edit_chk, clean
        )
        try:
            self.queue.add_task(task)
        except Exception as e:
            self.log(f"[{tag}] {e}", "error")
            return

    def command_preview(self, row: int) -> str:
        return self.queue.command_preview(row)

    def set_command_override(
        self, row: int, cmd: str | None, *, emit: bool = True
    ) -> None:
        self.queue.set_command_override(row, cmd, emit=emit)

    def task_is_editable(self, row: int) -> bool:
        return self.queue.task_is_editable(row)

    def all_command_previews(self) -> list[str]:
        return self.queue.all_command_previews()

    def _start_batch(self) -> None:
        if self.current_index != -1 or not self.queue.tasks:
            return
        for task in self.queue.tasks:
            if task.edit.isChecked() and task.tag in EDITABLE_TAGS:
                try:
                    preview_argv = self._argv_for(task, preview=True)
                    default_cmd = task.cmd_override or " ".join(
                        shlex.quote(a) for a in preview_argv
                    )
                except Exception as e:
                    self.log(f"[{task.tag}] {e}", "error")
                    return
                cmd, ok = QInputDialog.getMultiLineText(
                    self, "Edit Command", "Command:", default_cmd
                )
                if not ok:
                    return
                task.cmd_override = cmd.strip() or None
                if task.cmd_override:
                    task.item.setToolTip(task.cmd_override)
                else:
                    task.item.setToolTip(default_cmd)
            task.edit.setChecked(False)
        self.queue.tasks_changed.emit()
        self.current_index = -1
        self.cancel_requested = False
        self.batch_started.emit(len(self.queue.tasks))
        self.queue.set_current_index(self.current_index)
        self._run_next_task()

    def cancel_batch(self) -> None:
        if self.current_index == -1:
            return
        self.cancel_requested = True
        self.runner.cancel()

    def _run_next_task(self) -> None:
        self.current_index += 1
        if self.current_index >= len(self.queue.tasks):
            self.current_index = -1
            self.queue.set_current_index(self.current_index)
            self.batch_finished.emit()
            return
        self.queue.set_current_index(self.current_index)
        task = self.queue.tasks[self.current_index]
        task.bar.setRange(0, 0)
        if task.cmd_override:
            cmd_str = task.cmd_override
            try:
                argv = shlex.split(cmd_str)
            except ValueError as e:
                self.log(f"[{task.tag}] {e}", "error")
                self._task_done(task, -1)
                return
        else:
            try:
                argv = self._argv_for(task)
            except Exception as e:
                self.log(f"[{task.tag}] {e}", "error")
                self._task_done(task, -1)
                return
            cmd_str = " ".join(shlex.quote(a) for a in argv)
        self.log(f"[batch] {cmd_str}", "info")
        try:
            self.runner.start(
                argv,
                on_stdout=lambda s: self.log(f"[{task.tag}] {s}", "info"),
                on_stderr=lambda s: self.log(f"[{task.tag}] {s}", "error"),
                on_exit=lambda code: self._task_done(task, code),
            )
        except Exception as e:
            self.log(f"[{task.tag}] {e}", "error")
            self._task_done(task, -1)

    def _argv_for(self, task: QueuedTask, preview: bool = False) -> list[str]:
        if not self.profile or not self.ubt:
            raise RuntimeError("No profile loaded")
        if task.tag in {"build", "clean", "rebuild"}:
            target, cfg = self.ubt.guess_target(task.config)
            clean = task.tag != "build"
            return self.ubt.build_argv(target, task.platform, cfg, clean)
        if not self.uat:
            raise RuntimeError("No profile loaded")
        if task.tag == "cook":
            if task.clean and not preview:
                self._clean_dir(self.profile.project_dir / "Saved" / "Cooked")
            argv = self.uat.buildcookrun_argv(
                task.platform,
                task.config,
                cook=True,
                skip_build=True,
            )
            argv += self.uat_overrides.manual_args()
            return argv
        if task.tag == "stage":
            if task.clean and not preview:
                self._clean_dir(self.profile.project_dir / "Saved" / "Staged")
            argv = self.uat.buildcookrun_argv(
                task.platform,
                task.config,
                stage=True,
                pak=True,
                skip_build=True,
                skip_cook=True,
            )
            argv += self.uat_overrides.manual_args()
            return argv
        if task.tag == "package":
            if task.clean and not preview:
                self._clean_dir(self.profile.project_dir / "Saved" / "Staged")
            argv = self.uat.buildcookrun_argv(
                task.platform,
                task.config,
                package=True,
                skip_pak=True,
                skip_build=True,
                skip_cook=True,
                skip_stage=True,
            )
            argv += self.uat_overrides.manual_args()
            return argv
        if task.tag == "ddc-build":
            argv = self.uat.build_ddc_argv(task.platform)
            argv += self.uat_overrides.manual_args()
            return argv
        if task.tag == "ddc-clean":
            argv = self.uat.build_ddc_argv(task.platform, clean=True)
            argv += self.uat_overrides.manual_args()
            return argv
        if task.tag == "ddc-rebuild":
            argv = self.uat.rebuild_ddc_argv(task.platform)
            argv += self.uat_overrides.manual_args()
            return argv
        return [
            sys.executable,
            "-c",
            f"print('{task.tag} {task.config} {task.platform}')",
        ]

    def _clean_dir(self, path: Path) -> None:
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)

    def _task_done(self, task: QueuedTask, code: int) -> None:
        task.bar.setRange(0, 1)
        task.bar.setValue(1 if code == 0 else 0)
        self.log(f"[{task.tag}] exit code {code}", "success" if code == 0 else "error")
        self.batch_progress.emit(self.current_index + 1)
        if self.cancel_requested:
            self.current_index = -1
            self.queue.set_current_index(self.current_index)
            self.batch_finished.emit()
        else:
            self._run_next_task()
