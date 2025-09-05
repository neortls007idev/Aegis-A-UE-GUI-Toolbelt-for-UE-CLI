from __future__ import annotations

import sys
import shlex
from dataclasses import dataclass
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
    QAbstractItemView,
    QTableWidget,
    QTableWidgetItem,
    QDialog,
    QCheckBox,
)

from aegis.core.profile import Profile
from aegis.core.task_runner import TaskRunner
from aegis.modules.ubt import Ubt
from aegis.modules.uat import Uat
from aegis.ui.widgets.manual_override_dialog import (
    ManualOverrideDialog,
    BUILD_COOK_RUN_SWITCHES,
)


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


@dataclass
class QueuedTask:
    tag: str
    config: str
    platform: str
    item: QListWidgetItem
    widget: QWidget
    bar: QProgressBar
    edit: QCheckBox
    clean: bool = False
    cmd_override: str | None = None


class BatchBuilderPanel(QWidget):
    """Batch builder UI with queued tasks and progress tracking."""

    batch_started = Signal(int)
    batch_progress = Signal(int)
    batch_finished = Signal()

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

        self.tasks: list[QueuedTask] = []
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
        over_layout = QVBoxLayout()
        over_layout.addWidget(QLabel("Manual Overrides"))
        self.override_table = QTableWidget(0, 2)
        self.override_table.setHorizontalHeaderLabels(["Switch", "Value"])
        self.override_table.horizontalHeader().setStretchLastSection(True)
        over_layout.addWidget(self.override_table)
        row = QHBoxLayout()
        btn_add_override = QPushButton("Add…")
        btn_add_override.clicked.connect(self._add_override)
        btn_remove_override = QPushButton("Remove")
        btn_remove_override.clicked.connect(self._remove_override)
        row.addWidget(btn_add_override)
        row.addWidget(btn_remove_override)
        over_layout.addLayout(row)
        layout.addLayout(over_layout)

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
        queue_layout = QVBoxLayout()
        queue_layout.addWidget(QLabel("Queued Tasks"))
        self.task_list = QListWidget()
        self.task_list.setSelectionMode(QAbstractItemView.SingleSelection)
        queue_layout.addWidget(self.task_list)
        row = QHBoxLayout()
        btn_up = QPushButton("Up")
        btn_down = QPushButton("Down")
        btn_remove = QPushButton("Remove")
        btn_start = QPushButton("Start")
        btn_cancel = QPushButton("Cancel")
        btn_up.clicked.connect(lambda: self._move_task(-1))
        btn_down.clicked.connect(lambda: self._move_task(1))
        btn_remove.clicked.connect(self._remove_task)
        btn_start.clicked.connect(self._start_batch)
        btn_cancel.clicked.connect(self.cancel_batch)
        for b in (btn_up, btn_down, btn_remove, btn_start, btn_cancel):
            row.addWidget(b)
        queue_layout.addLayout(row)
        layout.addLayout(queue_layout)

    # ----- Profile -----
    def update_profile(self, profile: Profile | None) -> None:
        self.profile = profile
        self.ubt = Ubt(profile.engine_root, profile.project_dir) if profile else None
        self.uat = Uat(profile.engine_root, profile.project_dir) if profile else None
        self.config_list.clear()
        self.platform_list.clear()
        self.override_table.setRowCount(0)
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

    def _add_override(self) -> None:
        dialog = ManualOverrideDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        for switch, value in dialog.selected_overrides():
            row = self.override_table.rowCount()
            self.override_table.insertRow(row)
            self.override_table.setItem(row, 0, QTableWidgetItem(switch))
            self.override_table.setItem(row, 1, QTableWidgetItem(value))
            hint = BUILD_COOK_RUN_SWITCHES.get(switch, "")
            self.override_table.item(row, 0).setToolTip(hint)
            self.override_table.item(row, 1).setToolTip(hint)

    def _remove_override(self) -> None:
        row = self.override_table.currentRow()
        if row != -1:
            self.override_table.removeRow(row)

    def _manual_override_args(self) -> list[str]:
        args: list[str] = []
        for row in range(self.override_table.rowCount()):
            key_item = self.override_table.item(row, 0)
            if not key_item:
                continue
            switch = key_item.text().strip()
            if not switch:
                continue
            # Ensure switches use the "-switch=value" form
            switch = "-" + switch.lstrip("-").split("=")[0]
            val_item = self.override_table.item(row, 1)
            value = val_item.text().strip() if val_item else ""
            if value:
                args.append(f"{switch}={value}")
            else:
                args.append(switch)
        return args

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
        edit_chk.setToolTip("Edit command before running")
        row.addWidget(edit_chk)
        label = f"{tag} {cfg_item.text()} {plat_item.text()}"
        if clean:
            label += " (clean)"
        row.addWidget(QLabel(label))
        bar = QProgressBar()
        bar.setRange(0, 1)
        bar.setValue(0)
        row.addWidget(bar)
        item = QListWidgetItem()
        item.setSizeHint(widget.sizeHint())
        self.task_list.addItem(item)
        self.task_list.setItemWidget(item, widget)
        task = QueuedTask(
            tag, cfg_item.text(), plat_item.text(), item, widget, bar, edit_chk, clean
        )
        try:
            preview_argv = self._argv_for(task, preview=True)
            item.setToolTip(" ".join(shlex.quote(a) for a in preview_argv))
        except Exception as e:
            self.log(f"[{tag}] {e}", "error")
            self.task_list.takeItem(self.task_list.row(item))
            return
        self.tasks.append(task)

    def _move_task(self, delta: int) -> None:
        row = self.task_list.currentRow()
        if row == -1 or row <= self.current_index:
            return
        new_row = row + delta
        if (
            new_row <= self.current_index
            or new_row >= self.task_list.count()
            or new_row < 0
        ):
            return
        task = self.tasks.pop(row)
        self.tasks.insert(new_row, task)
        item = self.task_list.takeItem(row)
        self.task_list.insertItem(new_row, item)
        self.task_list.setItemWidget(item, task.widget)
        self.task_list.setCurrentRow(new_row)

    def _remove_task(self) -> None:
        row = self.task_list.currentRow()
        if row == -1 or row <= self.current_index:
            return
        self.tasks.pop(row)
        self.task_list.takeItem(row)

    def command_preview(self, row: int) -> str:
        if row < 0 or row >= len(self.tasks):
            return ""
        task = self.tasks[row]
        try:
            argv = self._argv_for(task, preview=True)
        except Exception:
            return ""
        cmd = " ".join(shlex.quote(a) for a in argv)
        return task.cmd_override or cmd

    def set_command_override(self, row: int, cmd: str | None) -> None:
        if row < 0 or row >= len(self.tasks):
            return
        task = self.tasks[row]
        task.cmd_override = cmd or None
        if task.cmd_override:
            task.item.setToolTip(task.cmd_override)
        else:
            try:
                argv = self._argv_for(task, preview=True)
                task.item.setToolTip(" ".join(shlex.quote(a) for a in argv))
            except Exception:
                task.item.setToolTip("")

    def _start_batch(self) -> None:
        if self.current_index != -1 or not self.tasks:
            return
        for task in self.tasks:
            if task.edit.isChecked():
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
        self.current_index = -1
        self.cancel_requested = False
        self.batch_started.emit(len(self.tasks))
        self._run_next_task()

    def cancel_batch(self) -> None:
        if self.current_index == -1:
            return
        self.cancel_requested = True
        self.runner.cancel()

    def _run_next_task(self) -> None:
        self.current_index += 1
        if self.current_index >= len(self.tasks):
            self.current_index = -1
            self.batch_finished.emit()
            return
        task = self.tasks[self.current_index]
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
            argv += self._manual_override_args()
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
            argv += self._manual_override_args()
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
            argv += self._manual_override_args()
            return argv
        if task.tag == "ddc-build":
            argv = self.uat.build_ddc_argv(task.platform)
            argv += self._manual_override_args()
            return argv
        if task.tag == "ddc-clean":
            argv = self.uat.build_ddc_argv(task.platform, clean=True)
            argv += self._manual_override_args()
            return argv
        if task.tag == "ddc-rebuild":
            argv = self.uat.rebuild_ddc_argv(task.platform)
            argv += self._manual_override_args()
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
            self.batch_finished.emit()
        else:
            self._run_next_task()
