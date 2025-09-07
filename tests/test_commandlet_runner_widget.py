import pytest

pytest.importorskip("PySide6")

from pathlib import Path
import sys
from PySide6.QtWidgets import QInputDialog

from aegis.core.profile import Profile
from aegis.core.task_runner import TaskRunner
from aegis.modules.commandlets import load_commandlets
from aegis.ui.widgets.commandlet_runner_widget import CommandletRunnerWidget


def _noop_log(_msg: str, _level: str) -> None:
    pass


def test_autopick_paths(tmp_path: Path, qtbot) -> None:
    engine = tmp_path / "UE"
    bin_dir = engine / "Engine" / "Binaries" / "Win64"
    bin_dir.mkdir(parents=True)
    exe = bin_dir / "UnrealEditor-Cmd.exe"
    exe.write_text("x")
    proj_dir = tmp_path / "Proj"
    proj_dir.mkdir()
    uproj = proj_dir / "Game.uproject"
    uproj.write_text("x")
    profile = Profile(engine_root=engine, project_dir=proj_dir)
    widget = CommandletRunnerWidget(TaskRunner(), _noop_log)
    qtbot.addWidget(widget)
    widget.update_profile(profile)
    assert widget.paths.exe_lbl.text() == str(exe)
    assert widget.uproject == uproj
    assert widget.scope.project_le.text() == str(uproj)
    assert not widget.controls.preview_le.isReadOnly()


def test_edit_and_remove_cmdlet(tmp_path: Path, qtbot, monkeypatch) -> None:
    engine = tmp_path / "UE"
    bin_dir = engine / "Engine" / "Binaries" / "Win64"
    bin_dir.mkdir(parents=True)
    (bin_dir / "UnrealEditor-Cmd.exe").write_text("x")
    proj_dir = tmp_path / "Proj"
    proj_dir.mkdir()
    uproj = proj_dir / "Game.uproject"
    uproj.write_text("x")
    profile = Profile(engine_root=engine, project_dir=proj_dir)
    widget = CommandletRunnerWidget(TaskRunner(), _noop_log)
    qtbot.addWidget(widget)
    widget.update_profile(profile)

    monkeypatch.setattr(QInputDialog, "getText", lambda *a, **k: ("MyCmd", True))
    widget._add_cmdlet()
    cmds = load_commandlets(uproj)
    assert "MyCmd" in cmds

    monkeypatch.setattr(QInputDialog, "getText", lambda *a, **k: ("NewCmd", True))
    widget.scope.cmdlet_cb.setCurrentText("MyCmd")
    widget._edit_cmdlet()
    cmds = load_commandlets(uproj)
    assert "NewCmd" in cmds
    assert "MyCmd" not in cmds

    widget.scope.cmdlet_cb.setCurrentText("NewCmd")
    widget._remove_cmdlet()
    cmds = load_commandlets(uproj)
    assert "NewCmd" not in cmds


def test_run_manual_preview(tmp_path: Path, qtbot, monkeypatch) -> None:
    engine = tmp_path / "UE"
    bin_dir = engine / "Engine" / "Binaries" / "Win64"
    bin_dir.mkdir(parents=True)
    (bin_dir / "UnrealEditor-Cmd.exe").write_text("x")
    proj_dir = tmp_path / "Proj"
    proj_dir.mkdir()
    (proj_dir / "Game.uproject").write_text("x")
    profile = Profile(engine_root=engine, project_dir=proj_dir)
    widget = CommandletRunnerWidget(TaskRunner(), _noop_log)
    qtbot.addWidget(widget)
    widget.update_profile(profile)

    called: dict[str, list[str]] = {}

    def fake_start(argv, _out, _err, on_exit):
        called["argv"] = argv
        on_exit(0)

    monkeypatch.setattr(widget.runner, "start", fake_start)
    widget.controls.preview_le.setText("echo hi")
    widget._run()
    assert called["argv"] == ["echo", "hi"]


def test_override_project_path(tmp_path: Path, qtbot) -> None:
    engine = tmp_path / "UE"
    bin_dir = engine / "Engine" / "Binaries" / "Win64"
    bin_dir.mkdir(parents=True)
    (bin_dir / "UnrealEditor-Cmd.exe").write_text("x")
    proj_dir = tmp_path / "Proj"
    proj_dir.mkdir()
    (proj_dir / "Game.uproject").write_text("x")
    other = tmp_path / "Other" / "Other.uproject"
    other.parent.mkdir()
    other.write_text("x")
    profile = Profile(engine_root=engine, project_dir=proj_dir)
    widget = CommandletRunnerWidget(TaskRunner(), _noop_log)
    qtbot.addWidget(widget)
    widget.update_profile(profile)
    widget.scope.project_le.setText(str(other))
    assert widget.uproject == other


def test_rebuild_editor_invokes_ubt(tmp_path: Path, qtbot, monkeypatch) -> None:
    engine = tmp_path / "UE"
    script_dir = engine / "Engine" / "Build" / "BatchFiles"
    script_dir.mkdir(parents=True)
    script = script_dir / ("Build.bat" if sys.platform == "win32" else "Build.sh")
    script.write_text("echo")
    bin_dir = engine / "Engine" / "Binaries" / "Win64"
    bin_dir.mkdir(parents=True)
    (bin_dir / "UnrealEditor-Cmd.exe").write_text("x")
    proj_dir = tmp_path / "Proj"
    proj_dir.mkdir()
    (proj_dir / "Game.uproject").write_text("x")
    profile = Profile(engine_root=engine, project_dir=proj_dir)
    widget = CommandletRunnerWidget(TaskRunner(), _noop_log)
    qtbot.addWidget(widget)
    widget.update_profile(profile)

    called: dict[str, list[str]] = {}

    def fake_start(argv, _out, _err, on_exit):
        called["argv"] = argv
        on_exit(0)

    monkeypatch.setattr(widget.runner, "start", fake_start)
    widget._rebuild_editor()
    assert called["argv"][0] == str(script)
    assert "-clean" in called["argv"]
    assert "Development" in called["argv"]
