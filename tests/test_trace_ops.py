from pathlib import Path

from aegis.modules.trace_ops import TraceOpsController


def test_build_trace_flags() -> None:
    ctrl = TraceOpsController()
    flags = ctrl.build_trace_flags(["CPU", "GPU"], "1.2.3.4", {"statnamedevents": ""})
    assert "-trace=CPU,GPU" in flags
    assert "-tracehost=1.2.3.4" in flags
    assert "-statnamedevents" in flags


def test_server_argv(tmp_path: Path) -> None:
    ctrl = TraceOpsController()
    bin_root = tmp_path / "Engine" / "Binaries"
    plat_dir = bin_root / "Win64"
    plat_dir.mkdir(parents=True)
    (plat_dir / "UnrealTraceServer.exe").write_text("x")
    argv = ctrl.server_argv(bin_root, Path("/store"))
    assert argv[0].endswith("UnrealTraceServer.exe")
    assert "--store" in argv
