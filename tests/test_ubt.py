from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from aegis.modules.ubt import Ubt


def test_build_argv_includes_clean_and_project(tmp_path):
    engine_root = tmp_path / "UE"
    (engine_root / "Engine/Build/BatchFiles").mkdir(parents=True)
    project_dir = tmp_path / "MyGame"
    project_dir.mkdir()
    (project_dir / "MyGame.uproject").write_text("", encoding="utf-8")
    ubt = Ubt(engine_root, project_dir)
    target, cfg = ubt.guess_target("DevelopmentEditor")
    argv = ubt.build_argv(target, "Win64", cfg, clean=True)
    assert argv[0] == str(engine_root / "Engine/Build/BatchFiles/Build.sh")
    assert argv[1] == "-clean"
    assert argv[2] == "MyGameEditor"
    assert argv[3] == "Win64"
    assert argv[4] == "Development"
    assert f"-Project={project_dir / 'MyGame.uproject'}" in argv


def test_engine_path_direct(tmp_path):
    engine_root = tmp_path / "UE"
    (engine_root / "Engine/Build/BatchFiles").mkdir(parents=True)
    project_dir = tmp_path / "MyGame"
    project_dir.mkdir()
    (project_dir / "MyGame.uproject").write_text("", encoding="utf-8")
    ubt = Ubt(engine_root / "Engine", project_dir)
    argv = ubt.build_argv("MyGame", "Win64", "Development")
    assert argv[0] == str(engine_root / "Engine/Build/BatchFiles/Build.sh")
