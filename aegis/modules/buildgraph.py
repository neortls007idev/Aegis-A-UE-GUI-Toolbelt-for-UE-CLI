"""Helpers for BuildGraph presets."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass
class BuildGraph:
    """Compose RunUAT BuildGraph commands."""

    runuat: Path
    script: Path
    target: str
    sets: Dict[str, str] = field(default_factory=dict)
    clean: bool = False

    def argv(self) -> List[str]:
        argv: List[str] = [
            str(self.runuat),
            "BuildGraph",
            f"-Script={self.script}",
            f"-Target={self.target}",
        ]
        for key, val in self.sets.items():
            argv.append(f"-set:{key}={val}")
        if self.clean:
            argv.append("-Clean")
        return argv
