"""Tests for Pak/IoStore helpers."""

import pytest

pytest.importorskip("PySide6")

from pathlib import Path

from aegis.core.profile import Profile
from aegis.core.settings import settings
from aegis.ui.widgets.pak_iostore_panel import PakIoStorePanel

from aegis.ui.widgets.pak_iostore.utils import (
    build_iostore_cmd,
    build_unrealpak_cmd,
    compare_dirs,
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
    assert build_unrealpak_cmd("/path/UnrealPak.exe", pak, "validate") == [
        "/path/UnrealPak.exe",
        str(pak),
        "-Test",
    ]
    assert build_iostore_cmd("/path/IoStoreUtilities.exe", utoc, "validate") == [
        "/path/IoStoreUtilities.exe",
        "-Validate",
        f"-Container={utoc}",
    ]
    assert dest_for(pak, "_extracted") == Path("/tmp/test_extracted")


def test_compare_dirs(tmp_path: Path) -> None:
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.mkdir()
    b.mkdir()
    (a / "same.txt").write_text("hi")
    (b / "same.txt").write_text("hi")
    (a / "only_a.txt").write_text("a")
    (b / "only_b.txt").write_text("b")
    (a / "diff.txt").write_text("one")
    (b / "diff.txt").write_text("two")
    only_a, only_b, diff = compare_dirs(a, b)
    assert only_a == {"only_a.txt"}
    assert only_b == {"only_b.txt"}
    assert diff == {"diff.txt"}


def test_panel_autopick_and_cache(tmp_path: Path, qtbot) -> None:
    engine = tmp_path / "UE"
    bin_dir = engine / "Engine" / "Binaries" / "Win64"
    bin_dir.mkdir(parents=True)
    (bin_dir / "UnrealPak.exe").write_text("x")
    (bin_dir / "IoStoreUtilities.exe").write_text("x")
    proj = tmp_path / "Proj"
    proj.mkdir()
    profile = Profile(engine_root=engine, project_dir=proj)
    panel = PakIoStorePanel()
    qtbot.addWidget(panel)
    settings.set_pak_path("dir_root", None)
    panel.update_profile(profile)
    assert panel.unrealpak_path == bin_dir / "UnrealPak.exe"
    assert panel.iostore_path == bin_dir / "IoStoreUtilities.exe"
    assert panel.dir_tab.dir_root.text() == str(proj)
    new_dir = tmp_path / "Other"
    panel.dir_tab.dir_root.setText(str(new_dir))
    assert settings.pak_path("dir_root") == str(new_dir)
