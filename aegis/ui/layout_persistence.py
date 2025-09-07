"""Persist and clamp window geometry within available screen bounds."""

from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, QSettings
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QWidget


def clamp_rect_to_available(rect: QRect, widget: QWidget) -> QRect:
    """Clamp *rect* to the screen's available geometry respecting widget minimums."""
    win = widget.windowHandle()
    screen = win.screen() if win else QGuiApplication.primaryScreen()
    avail = screen.availableGeometry()
    size = rect.size().boundedTo(avail.size())
    size.setWidth(max(size.width(), widget.minimumWidth()))
    size.setHeight(max(size.height(), widget.minimumHeight()))
    x = max(avail.left(), min(rect.left(), avail.right() - size.width()))
    y = max(avail.top(), min(rect.top(), avail.bottom() - size.height()))
    return QRect(QPoint(x, y), size)


def restore_window_geometry(
    window: QWidget, settings: QSettings, key_prefix: str = "main"
) -> None:
    """Restore saved geometry/state and clamp to the current screen."""
    geom = settings.value(f"{key_prefix}/geometry", None, type=bytes)
    state = settings.value(f"{key_prefix}/state", None, type=bytes)
    if geom:
        window.restoreGeometry(geom)
    if state:
        window.restoreState(state)
    clamped = clamp_rect_to_available(window.frameGeometry(), window)
    window.setGeometry(clamped)


def save_window_geometry(
    window: QWidget, settings: QSettings, key_prefix: str = "main"
) -> None:
    """Persist window geometry and state to *settings*."""
    settings.setValue(f"{key_prefix}/geometry", window.saveGeometry())
    settings.setValue(f"{key_prefix}/state", window.saveState())


def debug_minimums(window: QWidget) -> None:
    """Print minimum sizes for *window* and its children for debugging."""
    print("Window minimum:", window.minimumSize())
    for w in window.findChildren(QWidget):
        if w.minimumWidth() > 0 or w.minimumHeight() > 0:
            print(
                w.objectName(),
                w.metaObject().className(),
                w.minimumWidth(),
                w.minimumHeight(),
            )
