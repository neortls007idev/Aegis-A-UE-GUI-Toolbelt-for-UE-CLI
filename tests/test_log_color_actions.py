"""Tests for log color actions mixin."""

import pytest

pytest.importorskip("PySide6")

from pathlib import Path

from PySide6.QtCore import QSettings

from aegis.core.log_colors import DEFAULT_LEVEL_COLORS
from aegis.core.settings import APP, ORG
from aegis.ui.log_color_actions import LogColorActions
from aegis.ui.widgets.log_panel import LogPanel


class Dummy(LogColorActions):
    def __init__(self) -> None:
        self.log_panel = LogPanel()


def test_reset_log_colors(tmp_path, qtbot) -> None:
    fmt = QSettings.Format.IniFormat
    scope = QSettings.Scope.UserScope
    orig = Path(QSettings(fmt, scope, ORG, APP).fileName()).parent
    QSettings.setPath(fmt, scope, str(tmp_path))
    try:
        dummy = Dummy()
        qtbot.addWidget(dummy.log_panel)
        dummy.log_panel.log_colors.set_level_color("info", "#123456")
        dummy._reset_log_colors()
        assert (
            dummy.log_panel.log_colors.get_level_color("info")
            == DEFAULT_LEVEL_COLORS["info"]
        )
    finally:
        QSettings.setPath(fmt, scope, str(orig))
