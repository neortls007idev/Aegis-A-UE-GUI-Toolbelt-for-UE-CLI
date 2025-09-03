from __future__ import annotations

from typing import Dict, List, Tuple

import os
import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication

from aegis.ui.widgets.log_colors_editor import LogColorsEditor


@pytest.fixture(scope="module")
def app() -> QApplication:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_log_colors_editor_get_config(app: QApplication) -> None:
    levels: Dict[str, str] = {
        "info": "#111111",
        "warning": "#222222",
        "error": "#333333",
        "success": "#444444",
    }
    regex: List[Tuple[str, str]] = [("foo", "#555555"), ("bar", "#666666")]
    dlg = LogColorsEditor(levels, regex)
    lvls, rx = dlg.get_config()
    assert lvls == levels
    assert rx == regex
