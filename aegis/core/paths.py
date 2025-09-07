from __future__ import annotations

from pathlib import Path
import os


def find_engine_binaries(engine_root: Path | None = None) -> Path | None:
    """Return the Engine's binary directory if it looks valid.

    The search order prefers an explicit ``engine_root``. If omitted, the
    ``UE_ENGINE_ROOT`` environment variable is checked. The returned path is the
    ``Engine/Binaries/Win64`` folder on Windows or the generic ``Engine/Binaries``
    otherwise.
    """

    roots: list[Path] = []
    if engine_root:
        roots.append(engine_root)
    env = os.getenv("UE_ENGINE_ROOT")
    if env:
        roots.append(Path(env))
    for root in roots:
        win = root / "Engine" / "Binaries" / "Win64"
        if win.exists():
            return win
        generic = root / "Engine" / "Binaries"
        if generic.exists():
            return generic
    return None


def default_trace_store() -> Path:
    """Return the default trace store directory.

    Mirrors Unreal's per-user store location. The directory is not guaranteed to
    exist and callers may create it as needed.
    """

    if os.name == "nt":
        base = (
            Path(os.getenv("LOCALAPPDATA", ""))
            / "UnrealEngine"
            / "Common"
            / "UnrealTrace"
            / "Store"
            / "001"
        )
    else:
        base = Path.home() / ".unrealtrace" / "Store" / "001"
    return base
