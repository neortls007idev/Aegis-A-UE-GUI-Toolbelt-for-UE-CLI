"""Tests for the :class:`CommandEditor` widget."""

import pytest

pytest.importorskip("PySide6")

from PySide6.QtCore import QObject, Signal

from aegis.ui.widgets.command_editor import CommandEditor


class DummyBatch(QObject):
    tasks_changed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.cmds = ["first", "second"]

    def all_command_previews(self) -> list[str]:
        return self.cmds

    def task_is_editable(self, row: int) -> bool:
        return True

    def set_command_override(
        self, row: int, cmd: str | None, *, emit: bool = True
    ) -> None:
        self.cmds[row] = cmd or ""
        if emit:
            self.tasks_changed.emit()

    def command_preview(self, row: int) -> str:
        return self.cmds[row]


def test_refresh_populates_rows(qtbot) -> None:
    batch = DummyBatch()
    editor = CommandEditor(batch)  # type: ignore[arg-type]
    qtbot.addWidget(editor)
    assert editor.rowCount() == 2
    assert editor.item(0, 2).text() == "first"
