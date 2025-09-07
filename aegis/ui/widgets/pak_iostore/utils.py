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
    if mode == "list" or mode == "search":
        cmd.append("-List")
    elif mode == "extract" and dest:
        cmd += ["-Extract", str(dest)]
    elif mode == "validate":
        cmd.append("-Test")
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
    if mode == "list" or mode == "search":
        cmd += ["-List", f"-Container={utoc}"]
    elif mode == "extract" and dest:
        cmd += ["-Extract", f"-Container={utoc}", f"-OutputDir={dest}"]
    elif mode == "validate":
        cmd += ["-Validate", f"-Container={utoc}"]
    return cmd


def compare_dirs(a: Path, b: Path) -> tuple[set[str], set[str], set[str]]:
    """Return sets of relative paths only in ``a``, only in ``b``, and differing."""
    from filecmp import dircmp

    def _collect(dcmp: dircmp, prefix: str = "") -> tuple[set[str], set[str], set[str]]:
        only_a = {prefix + name for name in dcmp.left_only}
        only_b = {prefix + name for name in dcmp.right_only}
        diff = {prefix + name for name in dcmp.diff_files}
        for name, sub in dcmp.subdirs.items():
            sa, sb, sd = _collect(sub, prefix + name + "/")
            only_a.update(sa)
            only_b.update(sb)
            diff.update(sd)
        return only_a, only_b, diff

    return _collect(dircmp(a, b))
