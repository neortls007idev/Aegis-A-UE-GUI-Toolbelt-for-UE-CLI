from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass, field
import threading
from typing import Any

try:  # pragma: no cover - optional dependency
    from watchdog.events import FileSystemEvent, FileSystemEventHandler
    from watchdog.observers import Observer
except Exception:  # pragma: no cover - watchdog may be unavailable
    Observer = None  # type: ignore[assignment]
    FileSystemEvent = FileSystemEventHandler = Any  # type: ignore[assignment]

from aegis.core.ini_parser import get_value, parse_ini


@dataclass
class Uaft:
    """Thin UAFT command helper.

    Builds argv lists for UAFT operations and provides parsers for
    the tool's line-based output. The UI is responsible for running the
    commands via :class:`~aegis.core.task_runner.TaskRunner` and handling
    streaming output.
    """

    exe: Path
    project_dir: Path | None = None
    _token: str | None = field(init=False, default=None)
    _token_mtime: float = field(init=False, default=0.0)
    _observer: Observer | None = field(init=False, default=None)
    _watcher: threading.Thread | None = field(init=False, default=None)
    _stop_evt: threading.Event = field(init=False, default_factory=threading.Event)
    _token_updated: threading.Event = field(init=False, default_factory=threading.Event)

    def __post_init__(self) -> None:
        if self.project_dir:
            self._start_watcher()

    # ----- Security token -----
    def _config_path(self) -> Path | None:
        if not self.project_dir:
            return None
        for folder in ("Config", "Configs"):
            cfg = self.project_dir / folder / "DefaultEngine.ini"
            if cfg.exists():
                return cfg
        return self.project_dir / "Config" / "DefaultEngine.ini"

    def _read_token(self) -> str | None:
        cfg_path = self._config_path()
        if not cfg_path or not cfg_path.exists():
            return None
        cfg = parse_ini(cfg_path)
        sec = "/Script/AndroidFileServerEditor.AndroidFileServerRuntimeSettings"
        token = get_value(cfg, sec, "SecurityToken")
        if token and "=" in token:
            token = token.split("=", 1)[1].strip()
        return token

    def _watch_token(self) -> None:
        while not self._stop_evt.wait(timeout=1):
            cfg_path = self._config_path()
            if cfg_path and cfg_path.exists():
                mtime = cfg_path.stat().st_mtime
                if mtime != self._token_mtime:
                    self._token_mtime = mtime
                    self._on_config_change()

    def _start_watcher(self) -> None:
        self._token = self._read_token()
        cfg_path = self._config_path()
        if cfg_path and cfg_path.exists():
            self._token_mtime = cfg_path.stat().st_mtime
            if Observer:
                handler = _ConfigHandler(self)
                self._observer = Observer()
                self._observer.schedule(handler, str(cfg_path.parent), recursive=False)
                self._observer.start()
            else:
                self._watcher = threading.Thread(target=self._watch_token, daemon=True)
                self._watcher.start()

    def _on_config_change(self) -> None:
        self._token = self._read_token()
        self._token_updated.set()

    def stop(self) -> None:
        self._stop_evt.set()
        if self._observer and self._observer.is_alive():
            self._observer.stop()
            self._observer.join(timeout=1)
        if self._watcher and self._watcher.is_alive():
            self._watcher.join(timeout=1)

    def security_token(self) -> str | None:
        if not self._token:
            self._token = self._read_token()
        return self._token

    # ----- Arg builders -----
    def devices_argv(self) -> list[str]:
        return [str(self.exe), "devices"]

    @staticmethod
    def parse_devices(lines: list[str]) -> list[str]:
        devices: list[str] = []
        for ln in lines:
            ln = ln.strip().lstrip("@")
            if ln and " " not in ln and ln.lower() != "devices":
                devices.append(ln)
        return devices

    def packages_argv(self, serial: str | None = None) -> list[str]:
        args = [str(self.exe)]
        if serial:
            args += ["-s", serial]
        args += ["packages"]
        return args

    @staticmethod
    def parse_packages(lines: list[str]) -> list[str]:
        return [ln.strip() for ln in lines if "." in ln.strip()]

    def push_commandfile_argv(
        self,
        serial: str | None,
        ip: str | None,
        port: str | None,
        package: str,
        token: str | None,
        local_cmd: str,
    ) -> list[str]:
        args = [str(self.exe)]
        if serial:
            args += ["-s", serial]
        elif ip:
            args += ["-ip", ip]
        if port:
            args += ["-t", port]
        args += ["-p", package]
        token = token or self.security_token()
        if token:
            args += ["-k", token]
        args += ["push", local_cmd, "^commandfile"]
        return args

    def list_traces_argv(
        self,
        serial: str | None,
        ip: str | None,
        port: str | None,
        package: str,
        token: str | None,
    ) -> list[str]:
        args = [str(self.exe)]
        if serial:
            args += ["-s", serial]
        elif ip:
            args += ["-ip", ip]
        if port:
            args += ["-t", port]
        args += ["-p", package]
        token = token or self.security_token()
        if token:
            args += ["-k", token]
        args += ["ls", "-R", "^saved/Traces"]
        return args

    @staticmethod
    def parse_traces(lines: list[str]) -> list[str]:
        files: list[str] = []
        for ln in lines:
            ln = ln.strip()
            if ln.endswith(".trace") or ln.endswith(".utrace"):
                files.append(ln)
        return files

    def pull_trace_argv(
        self,
        serial: str | None,
        ip: str | None,
        port: str | None,
        package: str,
        token: str | None,
        remote_file: str,
        local_dir: Path,
    ) -> list[str]:
        local_dir.mkdir(parents=True, exist_ok=True)
        args = [str(self.exe)]
        if serial:
            args += ["-s", serial]
        elif ip:
            args += ["-ip", ip]
        if port:
            args += ["-t", port]
        args += ["-p", package]
        token = token or self.security_token()
        if token:
            args += ["-k", token]
        args += ["pull", remote_file, str(local_dir)]
        return args


class _ConfigHandler(FileSystemEventHandler):
    """Watchdog handler to reload UAFT token on config changes."""

    def __init__(self, uaft: Uaft) -> None:
        self.uaft = uaft

    def on_modified(self, event: FileSystemEvent) -> None:  # pragma: no cover - simple
        cfg_path = self.uaft._config_path()
        if cfg_path and Path(event.src_path) == cfg_path:
            self.uaft._on_config_change()
