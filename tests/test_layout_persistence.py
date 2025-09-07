from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")
from PySide6.QtCore import QRect, QSettings
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QApplication, QWidget

from aegis.ui.layout_persistence import (
    clamp_rect_to_available,
    restore_window_geometry,
    save_window_geometry,
)


@pytest.fixture()
def app() -> QApplication:
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_clamp_rect_to_available(app: QApplication) -> None:
    w = QWidget()
    avail = QGuiApplication.primaryScreen().availableGeometry()
    rect = QRect(
        avail.right() - 10, avail.bottom() - 10, avail.width() * 2, avail.height() * 2
    )
    clamped = clamp_rect_to_available(rect, w)
    assert clamped.left() >= avail.left()
    assert clamped.top() >= avail.top()
    assert clamped.right() <= avail.right()
    assert clamped.bottom() <= avail.bottom()


def test_save_restore_geometry(tmp_path: Path, app: QApplication) -> None:
    w = QWidget()
    w.resize(800, 600)
    w.move(50, 50)
    s = QSettings(str(tmp_path / "geom.ini"), QSettings.IniFormat)
    save_window_geometry(w, s, key_prefix="ui")
    # Change size and position
    w.resize(200, 200)
    w.move(0, 0)
    restore_window_geometry(w, s, key_prefix="ui")
    avail = QGuiApplication.primaryScreen().availableGeometry()
    assert w.width() <= avail.width()
    assert w.height() <= avail.height()
