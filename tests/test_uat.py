from pathlib import Path

from aegis.modules.uat import Uat


def _setup(tmp_path: Path) -> tuple[Path, Path]:
    engine_root = tmp_path / "UE"
    (engine_root / "Engine/Build/BatchFiles").mkdir(parents=True)
    project_dir = tmp_path / "MyGame"
    project_dir.mkdir()
    (project_dir / "MyGame.uproject").write_text("", encoding="utf-8")
    return engine_root, project_dir


def test_cook_argv_skips_build(tmp_path: Path) -> None:
    engine_root, project_dir = _setup(tmp_path)
    uat = Uat(engine_root, project_dir)
    argv = uat.buildcookrun_argv("Win64", "Development", cook=True, skip_build=True)
    assert argv[0] == str(engine_root / "Engine/Build/BatchFiles/RunUAT.sh")
    assert "-Cook" in argv
    assert "-SkipBuild" in argv


def test_ddc_clean_argv(tmp_path: Path) -> None:
    engine_root, project_dir = _setup(tmp_path)
    uat = Uat(engine_root, project_dir)
    argv = uat.build_ddc_argv("Win64", clean=True)
    assert argv[1] == "BuildDerivedDataCache"
    assert "-Clean" in argv


def test_ddc_rebuild_adds_fill(tmp_path: Path) -> None:
    engine_root, project_dir = _setup(tmp_path)
    uat = Uat(engine_root, project_dir)
    argv = uat.rebuild_ddc_argv("Win64")
    assert "-Clean" in argv and "-Fill" in argv


def test_engine_path_direct(tmp_path: Path) -> None:
    engine_root, project_dir = _setup(tmp_path)
    uat = Uat(engine_root / "Engine", project_dir)
    argv = uat.build_ddc_argv("Win64")
    assert argv[0] == str(engine_root / "Engine/Build/BatchFiles/RunUAT.sh")


def test_pak_flags(tmp_path: Path) -> None:
    engine_root, project_dir = _setup(tmp_path)
    uat = Uat(engine_root, project_dir)
    argv = uat.buildcookrun_argv("Win64", "Development", stage=True, pak=True)
    assert "-Pak" in argv
    argv = uat.buildcookrun_argv(
        "Win64",
        "Development",
        package=True,
        skip_build=True,
        skip_cook=True,
        skip_stage=True,
        skip_pak=True,
    )
    assert "-SkipPak" in argv


def test_exe_path(tmp_path: Path) -> None:
    engine_root, project_dir = _setup(tmp_path)
    uat = Uat(engine_root, project_dir)
    assert uat.exe() == engine_root / "Engine/Build/BatchFiles/RunUAT.sh"
