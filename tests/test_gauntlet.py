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
        devices=["Windows@local"],
        trace_categories="Frame,CPU",
        trace_host="127.0.0.1",
        trace_port=1980,
        exec_cmds="cmds",
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
    assert "-Device=Windows@local" in argv
    assert "-trace=Frame,CPU" in argv
    assert "-tracehost=127.0.0.1" in argv
    assert "-traceport=1980" in argv
    assert "-ExecCmds=cmds" in argv
    assert "-Timeout=30" in argv
