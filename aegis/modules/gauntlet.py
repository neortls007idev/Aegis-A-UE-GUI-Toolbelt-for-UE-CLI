"""Helpers to build Gauntlet commands."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List


@dataclass
class Gauntlet:
    """Compose Gauntlet RunUAT commands."""

    runuat: Path
    project: Path
    tests: Iterable[str] = field(default_factory=list)
    build: str = "Local"
    cooked: bool = True
    platforms: Iterable[str] = field(default_factory=list)
    configuration: str = "Development"
    devices: Iterable[str] = field(default_factory=list)
    editor_exe: Path | None = None
    timeout_minutes: int | None = None
    exec_cmds: str | None = None

    def argv(self) -> List[str]:
        argv: List[str] = [str(self.runuat), "Gauntlet", f"-Project={self.project}"]
        for test in self.tests:
            argv.append(f"-Test={test}")
        argv.append(f"-Build={self.build}")
        if self.cooked:
            argv.append("-Cooked")
        for plat in self.platforms:
            argv.append(f"-Platform={plat}")
        argv.append(f"-Configuration={self.configuration}")
        for dev in self.devices:
            argv.append(f"-Device={dev}")
        argv += ["-Unattended", "-NoP4", "-LogVerbose"]
        if self.timeout_minutes is not None:
            argv.append(f"-Timeout={self.timeout_minutes}")
        if self.editor_exe:
            argv.append(f"-EditorExe={self.editor_exe}")
        if self.exec_cmds:
            argv.append("--")
            argv.append(f"-ExecCmds={self.exec_cmds}")
        return argv
