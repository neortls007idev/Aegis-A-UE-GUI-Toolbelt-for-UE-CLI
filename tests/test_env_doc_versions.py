from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication

from aegis.core.profile import Profile
from aegis.core.task_runner import TaskRunner
from aegis.ui.widgets.env_doc import EnvDocPanel
from aegis.ui.widgets.env_fix_dialog import EnvFixDialog


@pytest.fixture(scope="module")
def app() -> QApplication:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _panel() -> EnvDocPanel:
    return EnvDocPanel(TaskRunner(), lambda *_: None)


def test_detect_android_sdk_version(app: QApplication, tmp_path: Path) -> None:
    platforms = tmp_path / "platforms"
    platforms.mkdir()
    (platforms / "android-30").mkdir()
    (platforms / "android-33").mkdir()
    panel = _panel()
    version, color = panel._detect_version("Android SDK", tmp_path)
    assert version == "33"
    assert color is None


def test_detect_android_ndk_version(app: QApplication, tmp_path: Path) -> None:
    ndk_dir = tmp_path / "25.2.9519653"
    ndk_dir.mkdir()
    panel = _panel()
    version, color = panel._detect_version("Android NDK", ndk_dir)
    assert version == "25.2.9519653"
    assert color is None


def test_detect_vulkan_sdk_version(app: QApplication, tmp_path: Path) -> None:
    vulkan_dir = tmp_path / "1.3.250.0"
    vulkan_dir.mkdir()
    panel = _panel()
    version, color = panel._detect_version("Vulkan SDK", vulkan_dir)
    assert version == "1.3.250.0"
    assert color is None


def test_retest_sdks_logs(app: QApplication, tmp_path: Path) -> None:
    logs: list[tuple[str, str]] = []
    engine = tmp_path / "eng"
    (engine / "Extras" / "Android" / "SDK").mkdir(parents=True)
    (engine / "Extras" / "Android" / "NDK").mkdir(parents=True)
    (engine / "Extras" / "Android" / "JDK").mkdir(parents=True)
    panel = EnvDocPanel(TaskRunner(), lambda m, level: logs.append((m, level)))
    panel.update_profile(Profile(engine, tmp_path))
    logs.clear()
    panel._retest_sdks()
    assert logs[-1] == (
        "[env] Re-Test SDK installations and Environment variables complete",
        "success",
    )


def test_retest_sdks_logs_failed(app: QApplication, tmp_path: Path) -> None:
    logs: list[tuple[str, str]] = []
    engine = tmp_path / "eng_fail"
    (engine / "Extras" / "Android" / "SDK").mkdir(parents=True)
    (engine / "Extras" / "Android" / "JDK").mkdir(parents=True)
    panel = EnvDocPanel(TaskRunner(), lambda m, level: logs.append((m, level)))
    panel.update_profile(Profile(engine, tmp_path))
    logs.clear()
    panel._retest_sdks()
    assert logs[-1] == (
        "[env] Re-Test SDK installations and Environment variables failed",
        "error",
    )


def test_env_fix_dialog_add_scripts(app: QApplication, tmp_path: Path) -> None:
    dlg = EnvFixDialog({})
    s1 = tmp_path / "one.bat"
    s2 = tmp_path / "two.exe"
    s1.write_text("", "utf-8")
    s2.write_text("", "utf-8")
    dlg.add_script(s1)
    dlg.add_script(s2)
    selected = dlg.selected_scripts()
    assert s1 in selected and s2 in selected


def test_run_scripts_noninteractive(app: QApplication, tmp_path: Path) -> None:
    panel = EnvDocPanel(TaskRunner(), lambda *_: None)
    captured: list[list[str]] = []

    def fake_start(argv, on_stdout=None, on_stderr=None, on_exit=None):
        captured.append(argv)
        if on_exit:
            on_exit(0)

    panel.runner.start = fake_start  # type: ignore[assignment]
    script = tmp_path / "dummy.exe"
    script.write_text("", "utf-8")
    panel._run_scripts([script])
    assert captured[0][-1] == "-noninteractive"
