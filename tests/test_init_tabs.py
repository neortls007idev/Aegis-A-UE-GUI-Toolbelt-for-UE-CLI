"""Tests for tab initialization helper."""

import pytest

pytest.importorskip("PySide6")

from aegis.core.task_runner import TaskRunner
from aegis.ui.init_tabs import init_tabs


def _noop_log(_msg: str, _level: str) -> None:
    pass


def test_init_tabs_creates_tabs(qtbot) -> None:
    setup = init_tabs(TaskRunner(), _noop_log)
    qtbot.addWidget(setup.central)
    assert setup.tabs.count() == 7
