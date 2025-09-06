from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("PySide6")
from PySide6.QtCore import QByteArray, QSettings

from aegis.core.settings import APP, ORG, Settings


@pytest.fixture
def settings_obj(tmp_path: Path) -> Settings:
    fmt = QSettings.Format.IniFormat
    scope = QSettings.Scope.UserScope
    orig = Path(QSettings(fmt, scope, ORG, APP).fileName()).parent
    QSettings.setPath(fmt, scope, str(tmp_path))
    s = Settings()
    yield s
    QSettings.setPath(fmt, scope, str(orig))


def test_theme_and_custom_path(settings_obj: Settings) -> None:
    s = settings_obj
    assert s.theme_mode() == "system"
    s.set_theme_mode("dark")
    assert s.theme_mode() == "dark"
    assert s.custom_theme_path() is None
    s.set_custom_theme_path("theme.qss")
    assert s.custom_theme_path() == "theme.qss"
    s.set_custom_theme_path(None)
    assert s.custom_theme_path() is None


def test_geometry_state_and_profile(settings_obj: Settings) -> None:
    s = settings_obj
    geom = QByteArray(b"geom")
    s.save_geometry(geom)
    assert s.load_geometry() == geom
    state = QByteArray(b"state")
    s.save_state(state)
    assert s.load_state() == state
    assert s.layout_version() == 0
    s.set_layout_version(2)
    assert s.layout_version() == 2
    assert s.profile_path() is None
    s.set_profile_path("/tmp/profile")
    assert s.profile_path() == "/tmp/profile"
    s.set_profile_path(None)
    assert s.profile_path() is None
