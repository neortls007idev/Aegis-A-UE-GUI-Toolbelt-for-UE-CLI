from __future__ import annotations

from pathlib import Path
from typing import List, Optional


def dest_for(src: Path, suffix: str) -> Path:
    """Return ``src`` with ``suffix`` appended before the extension."""
    return src.with_name(src.stem + suffix)


def build_unrealpak_cmd(
    exe: str,
    pak: Path,
    mode: str,
    dest: Optional[Path] = None,
    filt: Optional[str] = None,
) -> List[str]:
    """Construct an UnrealPak command."""
    cmd = [exe or "UnrealPak.exe", str(pak)]
    if mode == "list":
        cmd.append("-List")
    elif mode == "extract" and dest:
        cmd += ["-Extract", str(dest)]
    if filt:
        cmd.append(f'-Filter="{filt}"')
    return cmd


def build_iostore_cmd(
    exe: str,
    utoc: Path,
    mode: str,
    dest: Optional[Path] = None,
) -> List[str]:
    """Construct an IoStoreUtilities command."""
    cmd = [exe or "IoStoreUtilities.exe"]
    if mode == "list":
        cmd += ["-List", f"-Container={utoc}"]
    elif mode == "extract" and dest:
        cmd += ["-Extract", f"-Container={utoc}", f"-OutputDir={dest}"]
    return cmd
