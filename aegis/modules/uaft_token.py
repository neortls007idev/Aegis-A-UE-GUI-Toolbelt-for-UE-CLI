from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
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
class UaftTokenWatcher:
    """Monitor a UAFT project for token changes."""

    project_dir: Path
    watch: bool = True
    _token: str | None = field(init=False, default=None)
    _token_mtime: float = field(init=False, default=0.0)
    _observer: Observer | None = field(init=False, default=None)
    _watcher: threading.Thread | None = field(init=False, default=None)
    _stop_evt: threading.Event = field(init=False, default_factory=threading.Event)
    token_updated: threading.Event = field(init=False, default_factory=threading.Event)

    def __post_init__(self) -> None:
        self._token = self._read_token()
        if self.watch:
            cfg_path = self._config_path()
            if cfg_path and cfg_path.exists():
                self._token_mtime = cfg_path.stat().st_mtime
                if Observer:
                    handler = _ConfigHandler(self)
                    self._observer = Observer()
                    self._observer.schedule(
                        handler, str(cfg_path.parent), recursive=False
                    )
                    self._observer.start()
                else:
                    self._watcher = threading.Thread(
                        target=self._watch_token, daemon=True
                    )
                    self._watcher.start()

    def _config_path(self) -> Path | None:
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

    def _on_config_change(self) -> None:
        self._token = self._read_token()
        self.token_updated.set()

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


class _ConfigHandler(FileSystemEventHandler):
    """Watchdog handler to reload UAFT token on config changes."""

    def __init__(self, watcher: UaftTokenWatcher) -> None:
        self.watcher = watcher

    def on_modified(self, event: FileSystemEvent) -> None:  # pragma: no cover - simple
        cfg_path = self.watcher._config_path()
        if cfg_path and Path(event.src_path) == cfg_path:
            self.watcher._on_config_change()
