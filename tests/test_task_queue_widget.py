import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QListWidgetItem,
    QProgressBar,
    QWidget,
)

from aegis.ui.models.queued_task import QueuedTask
from aegis.ui.widgets.task_queue_widget import TaskQueueWidget


def ensure_app() -> None:
    if QApplication.instance() is None:
        QApplication([])


def make_task(tag: str, config: str, platform: str) -> QueuedTask:
    item = QListWidgetItem()
    widget = QWidget()
    layout = QHBoxLayout(widget)
    edit = QCheckBox()
    layout.addWidget(edit)
    bar = QProgressBar()
    layout.addWidget(bar)
    return QueuedTask(tag, config, platform, item, widget, bar, edit)


def dummy_argv(task: QueuedTask, preview: bool = False) -> list[str]:
    return ["echo", task.tag, task.config, task.platform]


def test_command_preview_and_override() -> None:
    ensure_app()
    queue = TaskQueueWidget(dummy_argv)
    task = make_task("build", "Dev", "Win64")
    queue.add_task(task)
    assert queue.command_preview(0) == "echo build Dev Win64"
    queue.set_command_override(0, "custom")
    assert queue.command_preview(0) == "custom"


def test_move_and_remove() -> None:
    ensure_app()
    queue = TaskQueueWidget(dummy_argv)
    first = make_task("build", "Dev", "Win64")
    second = make_task("cook", "Dev", "Win64")
    queue.add_task(first)
    queue.add_task(second)
    queue.task_list.setCurrentRow(1)
    queue.move_selected(-1)
    assert queue.tasks[0] is second
    queue.task_list.setCurrentRow(1)
    queue.remove_selected()
    assert len(queue.tasks) == 1
