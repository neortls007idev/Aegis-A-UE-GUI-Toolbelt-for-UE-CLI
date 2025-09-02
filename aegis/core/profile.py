from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json


@dataclass
class Profile:
    """Paths describing an Unreal project profile."""

    engine_root: Path
    project_dir: Path
    nickname: str = ""

    def save(self, path: Path) -> None:
        data = {
            "engine_root": str(self.engine_root),
            "project_dir": str(self.project_dir),
            "nickname": self.nickname,
        }
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path) -> Profile:
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            engine_root=Path(data["engine_root"]),
            project_dir=Path(data["project_dir"]),
            nickname=data.get("nickname", ""),
        )

    def display_name(self) -> str:
        """Return a string representation for window titles."""
        nick = self.nickname.strip()
        proj = self.project_dir.name
        return f"{nick}-{proj}" if nick else proj

