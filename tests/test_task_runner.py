from __future__ import annotations

import errno

import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication
from PySide6.QtTest import QSignalSpy

from aegis.core.task_runner import TaskRunner


@pytest.fixture(scope="module")
def app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_invalid_executable_path_emits_error(app: QApplication, tmp_path) -> None:
    runner = TaskRunner()
    spy = QSignalSpy(runner.finished)
    stderr: list[str] = []
    codes: list[int] = []

    runner.start(
        [str(tmp_path / "missing.exe")], lambda _: None, stderr.append, codes.append
    )

    assert codes == [errno.ENOENT]
    assert spy.count() == 1
    assert spy.takeFirst()[0] == errno.ENOENT
    assert "missing.exe" in stderr[0]
