from pathlib import Path

from aegis.core.preferences import AppPreferences


def test_preferences_load_and_save(tmp_path: Path) -> None:
    path = tmp_path / "prefs.json"
    prefs = AppPreferences.load(path)
    assert prefs.allow_docking is True
    prefs.allow_docking = False
    prefs.save(path)
    loaded = AppPreferences.load(path)
    assert loaded.allow_docking is False
