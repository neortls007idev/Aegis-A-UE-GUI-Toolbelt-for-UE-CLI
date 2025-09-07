"""Tests for the :class:`CommandPreviewWidget`."""

import pytest

pytest.importorskip("PySide6")
from pytestqt.qtbot import QtBot
from PySide6.QtWidgets import QApplication

from aegis.ui.widgets.command_preview import CommandPreviewWidget


def test_copy_button_copies_text(qtbot: QtBot) -> None:
    widget = CommandPreviewWidget()
    qtbot.addWidget(widget)
    widget.set_command("echo test")
    clipboard = QApplication.clipboard()
    clipboard.clear()
    widget.copy_btn.click()
    assert clipboard.text() == "echo test"
    assert widget.line.isReadOnly()
