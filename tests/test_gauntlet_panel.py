import pytest

pytest.importorskip("PySide6")

from pathlib import Path
from aegis.core.profile import Profile
from aegis.core.task_runner import TaskRunner
from aegis.ui.widgets.gauntlet_panel import GauntletPanel


def _noop_log(_msg: str, _level: str) -> None:
    pass


def test_gauntlet_panel_autofills(tmp_path: Path, qtbot) -> None:
    engine = tmp_path / "UE"
    bin_dir = engine / "Engine" / "Binaries" / "Win64"
    batch_dir = engine / "Engine" / "Build" / "BatchFiles"
    bin_dir.mkdir(parents=True)
    batch_dir.mkdir(parents=True)
    (bin_dir / "UnrealEditor-Cmd.exe").write_text("x")
    (batch_dir / "RunUAT.bat").write_text("x")
    proj_dir = tmp_path / "Proj"
    proj_dir.mkdir()
    uproj = proj_dir / "Game.uproject"
    uproj.write_text("x")
    profile = Profile(engine_root=engine, project_dir=proj_dir)
    panel = GauntletPanel(TaskRunner(), _noop_log)
    qtbot.addWidget(panel)
    panel.update_profile(profile)
    assert panel.runuat_edit.text() == str(batch_dir / "RunUAT.bat")
    assert panel.project_edit.text() == str(uproj)
    assert panel.editor_edit.text() == str(bin_dir / "UnrealEditor-Cmd.exe")
