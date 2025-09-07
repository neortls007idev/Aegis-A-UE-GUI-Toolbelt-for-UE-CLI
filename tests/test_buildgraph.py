"""Tests for BuildGraph command builder."""

from pathlib import Path

from aegis.modules.buildgraph import BuildGraph


def test_buildgraph_args() -> None:
    b = BuildGraph(
        runuat=Path("/Engine/RunUAT.bat"),
        script=Path("docs/buildgraph/presets/game_windows_package.xml"),
        target="ArchiveClient",
        sets={"Project": "Game.uproject", "Platform": "Win64"},
        clean=True,
    )
    argv = b.argv()
    assert argv[1] == "BuildGraph"
    assert "-Script=docs/buildgraph/presets/game_windows_package.xml" in argv
    assert "-Target=ArchiveClient" in argv
    assert "-set:Project=Game.uproject" in argv
    assert "-Clean" in argv
