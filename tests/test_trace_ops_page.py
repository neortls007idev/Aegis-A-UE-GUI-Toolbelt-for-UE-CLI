from pathlib import Path
import sys

import pytest

pytest.importorskip("PySide6")

from aegis.core.profile import Profile  # noqa: E402
from aegis.modules.trace_ops import TraceOpsController  # noqa: E402
from aegis.ui.pages.page_trace_ops import TraceOpsPage  # noqa: E402


def _noop_log(_msg: str, _level: str) -> None:
    pass


def test_profile_auto_paths(tmp_path: Path, qtbot) -> None:
    engine = tmp_path / "UE"
    plat = "Win64" if sys.platform == "win32" else "Linux"
    bin_dir = engine / "Engine" / "Binaries" / plat
    bin_dir.mkdir(parents=True)
    (
        bin_dir
        / ("UnrealInsights.exe" if sys.platform == "win32" else "UnrealInsights")
    ).write_text("x")
    project_dir = tmp_path / "Proj"
    project_dir.mkdir()
    profile = Profile(engine_root=engine, project_dir=project_dir)
    page = TraceOpsPage(TraceOpsController(), _noop_log)
    qtbot.addWidget(page)
    page.update_profile(profile)
    assert page.engine_label.text() == str(bin_dir)
    page.trace_name_edit.setText("MyTrace")
    expected = project_dir / "Unreal Insights" / "MyTrace"
    assert page.store_edit.text() == str(expected)
    assert page.launch_insights_btn.isEnabled()
