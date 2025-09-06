"""Widget managing a queue of build tasks with start/stop controls."""

from __future__ import annotations

import shlex
from typing import Callable

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from aegis.ui.models.queued_task import QueuedTask


class TaskQueueWidget(QWidget):
    """List of queued tasks with ordering and execution controls."""

    tasks_changed = Signal()
    start_requested = Signal()
    cancel_requested = Signal()

    def __init__(
        self,
        argv_cb: Callable[[QueuedTask, bool], list[str]],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.argv_cb = argv_cb
        self.tasks: list[QueuedTask] = []
        self.current_index = -1

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Queued Tasks"))

        self.task_list = QListWidget()
        self.task_list.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.task_list)

        row = QHBoxLayout()
        btn_up = QPushButton("Up")
        btn_down = QPushButton("Down")
        btn_remove = QPushButton("Remove")
        btn_edit_all = QPushButton("Edit All")
        btn_start = QPushButton("Start")
        btn_cancel = QPushButton("Cancel")
        btn_up.clicked.connect(lambda: self.move_selected(-1))
        btn_down.clicked.connect(lambda: self.move_selected(1))
        btn_remove.clicked.connect(self.remove_selected)
        btn_edit_all.clicked.connect(self.check_all_edits)
        btn_start.clicked.connect(self.start_requested.emit)
        btn_cancel.clicked.connect(self.cancel_requested.emit)
        for b in (
            btn_up,
            btn_down,
            btn_remove,
            btn_edit_all,
            btn_start,
            btn_cancel,
        ):
            row.addWidget(b)
        layout.addLayout(row)

    def add_task(self, task: QueuedTask) -> None:
        """Append a task to the queue and update its preview tooltip."""
        preview = self.argv_cb(task, preview=True)
        task.item.setSizeHint(task.widget.sizeHint())
        task.item.setToolTip(" ".join(shlex.quote(a) for a in preview))
        self.tasks.append(task)
        self.task_list.addItem(task.item)
        self.task_list.setItemWidget(task.item, task.widget)
        self.tasks_changed.emit()

    def move_selected(self, delta: int) -> None:
        row = self.task_list.currentRow()
        if row == -1 or row <= self.current_index:
            return
        new_row = row + delta
        if (
            new_row <= self.current_index
            or new_row < 0
            or new_row >= self.task_list.count()
        ):
            return
        task = self.tasks.pop(row)
        self.tasks.insert(new_row, task)
        item = self.task_list.takeItem(row)
        self.task_list.insertItem(new_row, item)
        self.task_list.setItemWidget(item, task.widget)
        self.task_list.setCurrentRow(new_row)
        self.tasks_changed.emit()

    def remove_selected(self) -> None:
        row = self.task_list.currentRow()
        if row == -1 or row <= self.current_index:
            return
        self.tasks.pop(row)
        self.task_list.takeItem(row)
        self.tasks_changed.emit()

    def check_all_edits(self) -> None:
        for task in self.tasks:
            if task.edit.isEnabled():
                task.edit.setChecked(True)

    def command_preview(self, row: int) -> str:
        if row < 0 or row >= len(self.tasks):
            return ""
        task = self.tasks[row]
        try:
            argv = self.argv_cb(task, preview=True)
        except Exception:
            return ""
        cmd = " ".join(shlex.quote(a) for a in argv)
        return task.cmd_override or cmd

    def set_command_override(
        self, row: int, cmd: str | None, *, emit: bool = True
    ) -> None:
        if row < 0 or row >= len(self.tasks):
            return
        task = self.tasks[row]
        task.cmd_override = cmd or None
        if task.cmd_override:
            task.item.setToolTip(task.cmd_override)
        else:
            try:
                argv = self.argv_cb(task, preview=True)
                task.item.setToolTip(" ".join(shlex.quote(a) for a in argv))
            except Exception:
                task.item.setToolTip("")
        if emit:
            self.tasks_changed.emit()

    def task_is_editable(self, row: int) -> bool:
        return 0 <= row < len(self.tasks) and self.tasks[row].edit.isEnabled()

    def all_command_previews(self) -> list[str]:
        return [self.command_preview(i) for i in range(len(self.tasks))]

    def set_current_index(self, index: int) -> None:
        self.current_index = index
