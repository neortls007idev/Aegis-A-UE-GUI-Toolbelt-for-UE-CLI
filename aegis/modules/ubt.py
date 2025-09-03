from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Ubt:
    """Tiny helper to build Unreal Build Tool commands."""

    engine_root: Path
    project_dir: Path

    logger = logging.getLogger(__name__)

    def _engine_dir(self) -> Path:
        root = self.engine_root
        if (root / "Build" / "BatchFiles").exists():
            self.logger.debug("Using engine directory %s", root)
            return root
        candidate = root / "Engine"
        if (candidate / "Build" / "BatchFiles").exists():
            self.logger.debug("Detected engine root %s", root)
            return candidate
        msg = f"Could not locate Engine/Build/BatchFiles under {root}"
        self.logger.error(msg)
        raise FileNotFoundError(msg)

    def _uproject(self) -> Path:
        for p in self.project_dir.glob("*.uproject"):
            self.logger.debug("Using uproject %s", p)
            return p
        msg = f"No .uproject file found in {self.project_dir}"
        self.logger.error(msg)
        raise FileNotFoundError(msg)

    def exe(self) -> Path:
        """Return the platform-specific UBT executable path."""
        script_dir = self._engine_dir() / "Build" / "BatchFiles"
        return script_dir / ("Build.bat" if sys.platform == "win32" else "Build.sh")

    def build_argv(
        self,
        target: str,
        platform: str,
        config: str,
        clean: bool = False,
    ) -> list[str]:
        argv = [str(self.exe())]
        if clean:
            argv.append("-clean")
        argv += [
            target,
            platform,
            config,
            f"-Project={self._uproject()}",
            "-WaitMutex",
            "-FromMsBuild",
        ]
        return argv

    def guess_target(self, config: str) -> tuple[str, str]:
        name = self.project_dir.name
        if config.endswith("Editor"):
            return f"{name}Editor", config[:-6]
        if config.endswith("Server"):
            return f"{name}Server", config[:-6]
        return name, config
