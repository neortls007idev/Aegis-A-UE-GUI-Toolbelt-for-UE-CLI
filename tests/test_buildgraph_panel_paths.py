import pytest

pytest.importorskip("PySide6")

from pathlib import Path

from aegis.core.profile import Profile
from aegis.core.task_runner import TaskRunner
from aegis.ui.widgets.buildgraph_panel import BuildGraphPanel


def test_buildgraph_autopop(tmp_path: Path, qtbot) -> None:
    engine = tmp_path / "UE"
    (engine / "Engine" / "Build" / "BatchFiles").mkdir(parents=True)
    runuat = engine / "Engine" / "Build" / "BatchFiles" / "RunUAT.bat"
    runuat.write_text("", encoding="utf-8")
    project_dir = tmp_path / "Proj"
    project_dir.mkdir()
    uproject = project_dir / "Proj.uproject"
    uproject.write_text("{}", encoding="utf-8")
    profile = Profile(engine_root=engine, project_dir=project_dir)

    panel = BuildGraphPanel(TaskRunner(), lambda *_: None)
    qtbot.addWidget(panel)
    panel.update_profile(profile)

    assert panel.runuat_edit.text() == str(runuat)
    assert panel.vars_edits["Project"].text() == str(uproject)
