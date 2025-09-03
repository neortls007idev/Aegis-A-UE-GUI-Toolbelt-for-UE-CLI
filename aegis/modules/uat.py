from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import logging
import sys


@dataclass
class Uat:
    """Thin UAT command helper for BuildCookRun and DDC tasks.

    Flags live in
    ``Engine/Source/Programs/AutomationTool/Scripts/BuildCookRun.Automation.cs``.
    """

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

    def _exe(self) -> Path:
        script = "RunUAT.bat" if sys.platform.startswith("win") else "RunUAT.sh"
        return self._engine_dir() / "Build" / "BatchFiles" / script

    def _uproject(self) -> Path:
        for p in self.project_dir.glob("*.uproject"):
            self.logger.debug("Using uproject %s", p)
            return p
        msg = f"No .uproject file found in {self.project_dir}"
        self.logger.error(msg)
        raise FileNotFoundError(msg)

    def buildcookrun_argv(
        self,
        platform: str,
        config: str,
        *,
        build: bool = False,
        cook: bool = False,
        stage: bool = False,
        package: bool = False,
        skip_build: bool = False,
        skip_cook: bool = False,
        skip_stage: bool = False,
    ) -> list[str]:
        argv = [
            str(self._exe()),
            "BuildCookRun",
            f"-Project={self._uproject()}",
            "-NoP4",
            f"-ClientConfig={config}",
            f"-TargetPlatform={platform}",
        ]
        if build:
            argv.append("-Build")
        elif skip_build:
            argv.append("-SkipBuild")
        if cook:
            argv.append("-Cook")
        elif skip_cook:
            argv.append("-SkipCook")
        if stage:
            argv.append("-Stage")
        elif skip_stage:
            argv.append("-SkipStage")
        if package:
            argv.append("-Package")
        return argv

    def build_ddc_argv(self, platform: str, clean: bool = False) -> list[str]:
        argv = [
            str(self._exe()),
            "BuildDerivedDataCache",
            f"-Project={self._uproject()}",
            f"-TargetPlatform={platform}",
        ]
        if clean:
            argv.append("-Clean")
        return argv

    def rebuild_ddc_argv(self, platform: str) -> list[str]:
        argv = self.build_ddc_argv(platform, clean=True)
        argv.append("-Fill")
        return argv
