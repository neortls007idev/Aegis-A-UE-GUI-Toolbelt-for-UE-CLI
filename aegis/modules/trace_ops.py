from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import Iterable
import sys


@dataclass
class TraceServerStatus:
    pid: int | None
    port: int
    store_dir: Path | None
    running: bool


@dataclass
class TraceInfo:
    path: Path
    size: int
    recording: bool


@dataclass
class ExportResult:
    trace: Path
    code: int


class TraceOpsController:
    """Lightweight helpers around Unreal Trace operations."""

    def __init__(self) -> None:
        self.server_proc: subprocess.Popen[str] | None = None
        self.port = 1981

    # ----- Server -----
    @staticmethod
    def engine_dir(engine_root: Path) -> Path:
        """Return the Engine directory for a given Unreal root."""
        eng = engine_root / "Engine"
        return eng if eng.is_dir() else engine_root

    @classmethod
    def engine_bin_path(cls, engine_root: Path) -> Path:
        """Return the ``Engine/Binaries`` directory for ``engine_root``.

        ``engine_root`` should point to the Unreal repository root or the
        ``Engine`` subdirectory. Do **not** include ``Binaries``; this helper
        appends it after normalizing the root.
        """
        return cls.engine_dir(engine_root) / "Binaries"

    def _find_binary(self, engine_bin: Path, names: Iterable[str]) -> Path | None:
        """Search ``engine_bin`` and its subfolders for an executable."""
        candidates = [engine_bin / name for name in names]
        if engine_bin.exists():
            for sub in engine_bin.iterdir():
                if sub.is_dir():
                    for name in names:
                        candidates.append(sub / name)
        for cand in candidates:
            if cand.exists():
                return cand
        return None

    def find_trace_server_bin(self, engine_bin: Path) -> Path | None:
        """Locate the Unreal Trace Server executable."""
        return self._find_binary(
            engine_bin, ["UnrealTraceServer.exe", "UnrealTraceServer"]
        )

    def find_insights_bin(self, engine_bin: Path) -> Path | None:
        """Locate the Unreal Insights executable."""
        return self._find_binary(engine_bin, ["UnrealInsights.exe", "UnrealInsights"])

    def server_argv(self, engine_bin: Path, store_dir: Path | None) -> list[str]:
        exe = self.find_trace_server_bin(engine_bin)
        if not exe:
            raise FileNotFoundError(f"UnrealTraceServer not found under {engine_bin}")
        argv = [str(exe)]
        if store_dir:
            argv += ["--store", str(store_dir)]
        return argv

    def start_server(self, engine_bin: Path, store_dir: Path | None) -> list[str]:
        argv = self.server_argv(engine_bin, store_dir)
        self.server_proc = subprocess.Popen(argv, text=True)
        return argv

    def stop_server(self) -> bool:
        if self.server_proc and self.server_proc.poll() is None:
            self.server_proc.terminate()
            self.server_proc = None
            return True
        return False

    def server_status(self) -> TraceServerStatus:
        running = self.server_proc is not None and self.server_proc.poll() is None
        pid = self.server_proc.pid if self.server_proc else None
        return TraceServerStatus(
            pid=pid, port=self.port, store_dir=None, running=running
        )

    # ----- Client helpers -----
    def build_trace_flags(
        self, preset: Iterable[str], host: str, extras: dict[str, str] | None = None
    ) -> str:
        channels = ",".join(preset)
        parts = [f"-trace={channels}", f"-tracehost={host}"]
        if extras:
            for k, v in extras.items():
                parts.append(f"-{k}={v}" if v else f"-{k}")
        return " ".join(parts)

    # ----- Trace store -----
    def list_traces(self, store_dir: Path) -> list[TraceInfo]:
        infos: list[TraceInfo] = []
        for entry in sorted(store_dir.glob("*.utrace")):
            size = entry.stat().st_size
            infos.append(TraceInfo(path=entry, size=size, recording=False))
        return infos

    # ----- Insights -----
    def open_in_insights(self, insights_bin: Path, trace: Path) -> list[str]:
        argv = [str(insights_bin), f"-OpenTraceFile={trace}"]
        subprocess.Popen(argv, text=True)
        return argv

    def launch_insights(self, insights_bin: Path) -> list[str]:
        argv = [str(insights_bin)]
        subprocess.Popen(argv, text=True)
        return argv

    def rebuild_insights(self, engine_root: Path) -> list[str]:
        engine_dir = self.engine_dir(engine_root)
        script_name = "RunUAT.bat" if sys.platform == "win32" else "RunUAT.sh"
        script = engine_dir / "Build" / "BatchFiles" / script_name
        argv = [str(script), "BuildUnrealInsights"]
        subprocess.Popen(argv, text=True)
        return argv

    def export_batch(
        self, traces: list[Path], rsp: Path, insights_bin: Path, out_dir: Path
    ) -> list[ExportResult]:
        results: list[ExportResult] = []
        for trace in traces:
            argv = [
                str(insights_bin),
                f"-OpenTraceFile={trace}",
                "-AutoQuit",
                "-NoUI",
                f"-ExecOnAnalysisCompleteCmd=@={rsp}",
            ]
            code = subprocess.call(argv, cwd=out_dir)
            results.append(ExportResult(trace=trace, code=code))
        return results
