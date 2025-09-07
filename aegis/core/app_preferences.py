from __future__ import annotations

from pathlib import Path
from typing import List

APP_PREFERENCES_DIR = Path(__file__).resolve().parents[2] / "app_preferences"


def _list_files(path: Path) -> List[Path]:
    """Return sorted list of files in *path*.

    The directory is created if missing.
    """
    path.mkdir(parents=True, exist_ok=True)
    return sorted(p for p in path.iterdir() if p.is_file())


def list_profiles(root: Path = APP_PREFERENCES_DIR) -> List[Path]:
    """List profile files in ``root/profiles``."""
    return _list_files(root / "profiles")


def list_themes(root: Path = APP_PREFERENCES_DIR) -> List[Path]:
    """List theme files in ``root/ui/themes``."""
    return _list_files(root / "ui" / "themes")


def list_log_colors(root: Path = APP_PREFERENCES_DIR) -> List[Path]:
    """List log color definition files in ``root/ui/log_colors``."""
    return _list_files(root / "ui" / "log_colors")


def list_keybindings(root: Path = APP_PREFERENCES_DIR) -> List[Path]:
    """List key binding files in ``root/keybindings``."""
    return _list_files(root / "keybindings")
