from pathlib import Path

from aegis.modules.trace_ops import TraceOpsController


def test_build_trace_flags() -> None:
    ctrl = TraceOpsController()
    flags = ctrl.build_trace_flags(["CPU", "GPU"], "1.2.3.4", {"statnamedevents": ""})
    assert "-trace=CPU,GPU" in flags
    assert "-tracehost=1.2.3.4" in flags
    assert "-statnamedevents" in flags


def test_server_argv() -> None:
    ctrl = TraceOpsController()
    bin_dir = Path("/Engine/Binaries/Win64")
    argv = ctrl.server_argv(bin_dir, Path("/store"))
    assert argv[0].endswith("UnrealTraceServer.exe")
    assert "--store" in argv
