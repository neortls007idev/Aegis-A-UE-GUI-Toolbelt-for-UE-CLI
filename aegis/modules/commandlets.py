"""Utilities for building and saving Unreal commandlet runs."""

from __future__ import annotations

import json
import shlex
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import List


@dataclass
class CommandletFlags:
    """Common commandlet behavior flags."""

    unattended: bool = True
    nop4: bool = True
    nullrhi: bool = False
    stdout: bool = True
    utf8: bool = True

    def to_argv(self) -> List[str]:
        argv: List[str] = []
        if self.unattended:
            argv.append("-unattended")
        if self.nop4:
            argv.append("-nop4")
        if self.nullrhi:
            argv.append("-NullRHI")
        if self.stdout:
            argv.append("-stdout")
        if self.utf8:
            argv.append("-UTF8Output")
        return argv


@dataclass
class CommandletRecipe:
    """Serializable recipe describing a commandlet invocation."""

    commandlet: str = "ResavePackages"
    packages: list[str] = field(default_factory=list)
    maps: list[str] = field(default_factory=list)
    collection: str = ""
    extra_args: str = ""
    flags: CommandletFlags = field(default_factory=CommandletFlags)
    version: int = 1

    def to_json(self) -> str:
        data = asdict(self)
        data["flags"] = asdict(self.flags)
        return json.dumps(data, indent=2)

    @staticmethod
    def from_json(text: str) -> "CommandletRecipe":
        data = json.loads(text)
        flags = CommandletFlags(**data.get("flags", {}))
        return CommandletRecipe(
            commandlet=data.get("commandlet", "ResavePackages"),
            packages=data.get("packages", []),
            maps=data.get("maps", []),
            collection=data.get("collection", ""),
            extra_args=data.get("extra_args", ""),
            flags=flags,
        )


def build_argv(exe: Path, project: Path, recipe: CommandletRecipe) -> List[str]:
    """Compose the argv list for a commandlet run."""

    argv: List[str] = [str(exe), str(project), f"-run={recipe.commandlet}"]
    argv.extend(recipe.flags.to_argv())
    for token in recipe.packages:
        if token:
            argv.append(f'-Package="{token}"')
    for token in recipe.maps:
        if token:
            argv.append(f"-Map={token}")
    if recipe.collection:
        argv.append(f"-Collection={recipe.collection}")
    if recipe.extra_args:
        argv.extend(shlex.split(recipe.extra_args))
    return argv


def preview_command(argv: List[str]) -> str:
    """Return a shell-escaped command preview."""

    return shlex.join(argv)


def recipes_dir(uproject: Path) -> Path:
    """Return the directory for commandlet recipes."""

    return uproject.parent / ".aegies" / "recipes" / "commandlets"


def save_recipe(uproject: Path, name: str, recipe: CommandletRecipe) -> Path:
    """Write ``recipe`` to ``name`` under the project's recipes directory."""

    dir_path = recipes_dir(uproject)
    dir_path.mkdir(parents=True, exist_ok=True)
    file_path = dir_path / f"{name}.json"
    file_path.write_text(recipe.to_json(), encoding="utf-8")
    return file_path


def load_recipe(path: Path) -> CommandletRecipe:
    """Load a commandlet recipe from ``path``."""

    return CommandletRecipe.from_json(path.read_text(encoding="utf-8"))
