from pathlib import Path
import logging
import pytest

from aegis.core.preferences import AppPreferences


def test_preferences_load_and_save(tmp_path: Path) -> None:
    path = tmp_path / "prefs.json"
    prefs = AppPreferences.load(path)
    assert prefs.allow_docking is True
    prefs.allow_docking = False
    prefs.save(path)
    loaded = AppPreferences.load(path)
    assert loaded.allow_docking is False


def test_corrupt_preferences_file_recovers(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    path = tmp_path / "prefs.json"
    path.write_text("{bad json}")
    with caplog.at_level(logging.WARNING):
        prefs = AppPreferences.load(path)
    assert prefs.allow_docking is True
    assert any(
        "Failed to load preferences" in message and str(path) in message
        for message in caplog.messages
    )
