"""Tests for Pak/IoStore helpers."""

import pytest

pytest.importorskip("PySide6")

from pathlib import Path

from aegis.ui.widgets.pak_iostore.utils import (
    build_iostore_cmd,
    build_unrealpak_cmd,
    dest_for,
)


def test_command_builders() -> None:
    pak = Path("/tmp/test.pak")
    utoc = Path("/tmp/sample.utoc")
    dest = Path("/tmp/out")

    assert build_unrealpak_cmd("/path/UnrealPak.exe", pak, "list") == [
        "/path/UnrealPak.exe",
        str(pak),
        "-List",
    ]
    assert build_unrealpak_cmd("/path/UnrealPak.exe", pak, "extract", dest) == [
        "/path/UnrealPak.exe",
        str(pak),
        "-Extract",
        str(dest),
    ]
    assert build_unrealpak_cmd(
        "/path/UnrealPak.exe",
        pak,
        "extract",
        dest,
        "*.uasset",
    ) == [
        "/path/UnrealPak.exe",
        str(pak),
        "-Extract",
        str(dest),
        '-Filter="*.uasset"',
    ]
    assert build_iostore_cmd("/path/IoStoreUtilities.exe", utoc, "list") == [
        "/path/IoStoreUtilities.exe",
        "-List",
        f"-Container={utoc}",
    ]
    assert build_iostore_cmd("/path/IoStoreUtilities.exe", utoc, "extract", dest) == [
        "/path/IoStoreUtilities.exe",
        "-Extract",
        f"-Container={utoc}",
        f"-OutputDir={dest}",
    ]
    assert dest_for(pak, "_extracted") == Path("/tmp/test_extracted")
