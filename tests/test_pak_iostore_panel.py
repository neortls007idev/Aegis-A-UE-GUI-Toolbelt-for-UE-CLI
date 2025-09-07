import pytest

pytest.importorskip("PySide6")

from pathlib import Path
import sys

from aegis.core.profile import Profile
from aegis.core.task_runner import TaskRunner
from aegis.ui.widgets.pak_iostore_panel import PakIoStorePanel


def _setup_panel(tmp_path: Path, qtbot) -> tuple[PakIoStorePanel, Path]:
    engine = tmp_path / "UE"
    script_dir = engine / "Engine" / "Build" / "BatchFiles"
    script_dir.mkdir(parents=True)
    script = script_dir / ("Build.bat" if sys.platform == "win32" else "Build.sh")
    script.write_text("echo")
    bin_dir = engine / "Engine" / "Binaries" / "Win64"
    bin_dir.mkdir(parents=True)
    (bin_dir / "UnrealPak.exe").write_text("x")
    (bin_dir / "IoStoreUtilities.exe").write_text("x")
    proj_dir = tmp_path / "Proj"
    proj_dir.mkdir()
    (proj_dir / "Game.uproject").write_text("x")
    profile = Profile(engine_root=engine, project_dir=proj_dir)
    panel = PakIoStorePanel(TaskRunner())
    qtbot.addWidget(panel)
    panel.update_profile(profile)
    return panel, script


def test_rebuild_unrealpak_invokes_ubt(tmp_path: Path, qtbot, monkeypatch) -> None:
    panel, script = _setup_panel(tmp_path, qtbot)
    called: dict[str, list[str]] = {}

    def fake_start(argv, on_stdout, on_stderr, on_exit):
        called["argv"] = argv
        on_exit(0)

    monkeypatch.setattr(panel.runner, "start", fake_start)
    panel._rebuild_unrealpak()
    assert called["argv"][0] == str(script)
    assert "UnrealPak" in called["argv"]


def test_rebuild_iostore_invokes_ubt(tmp_path: Path, qtbot, monkeypatch) -> None:
    panel, script = _setup_panel(tmp_path, qtbot)
    called: dict[str, list[str]] = {}

    def fake_start(argv, on_stdout, on_stderr, on_exit):
        called["argv"] = argv
        on_exit(0)

    monkeypatch.setattr(panel.runner, "start", fake_start)
    panel._rebuild_iostore()
    assert called["argv"][0] == str(script)
    assert "IoStoreUtilities" in called["argv"]
