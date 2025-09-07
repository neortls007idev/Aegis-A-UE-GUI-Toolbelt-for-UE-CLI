"""Tests for Gauntlet command builder."""

from pathlib import Path

from aegis.modules.gauntlet import Gauntlet


def test_gauntlet_basic() -> None:
    g = Gauntlet(
        runuat=Path("/Engine/RunUAT.bat"),
        project=Path("/Game/Test.uproject"),
        tests=["Smoke"],
        platforms=["Windows"],
        configuration="Development",
        timeout_minutes=30,
    )
    argv = g.argv()
    assert argv[:3] == [
        "/Engine/RunUAT.bat",
        "Gauntlet",
        "-Project=/Game/Test.uproject",
    ]
    assert "-Test=Smoke" in argv
    assert "-Platform=Windows" in argv
    assert "-Configuration=Development" in argv
    assert "-Timeout=30" in argv
