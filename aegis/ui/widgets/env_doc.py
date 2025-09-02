from __future__ import annotations

from typing import Callable, Optional
import configparser
import json
import os
import tempfile
import urllib.request
from pathlib import Path

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QPushButton,
    QWidget,
)

from aegis.core.profile import Profile
from aegis.core.task_runner import TaskRunner
from .env_fix_dialog import EnvFixDialog


REMOTE_FIX_SCRIPTS_INDEX = "https://example.com/aegis/fix-scripts.json"


class EnvDocPanel(QWidget):
    """Simple Environment Doctor that checks SDK paths."""

    def __init__(
        self,
        runner: TaskRunner,
        log_cb: Callable[[str, str], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.runner = runner
        self.log = log_cb
        self.profile: Profile | None = None

        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Component", "Path", "Status"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.fix_button = QPushButton("Fix Env")
        self.fix_button.clicked.connect(self._fix_env)
        layout.addWidget(self.fix_button)

    # ----- Profile -----
    def update_profile(self, profile: Optional[Profile]) -> None:
        self.profile = profile
        self._run_checks()

    # ----- Checks -----
    def _run_checks(self) -> None:
        self.table.setRowCount(0)
        if not self.profile:
            return

        components: dict[str, list[str]] = {
            "Android SDK": ["Extras", "Android", "SDK"],
            "Android NDK": ["Extras", "Android", "NDK"],
            "JDK": ["Extras", "Android", "JDK"],
            "Vulkan SDK": ["Extras", "Vulkan", "VulkanSDK"],
        }
        env_vars = {
            "Android SDK": ["ANDROID_SDK_ROOT", "ANDROID_HOME"],
            "Android NDK": ["ANDROID_NDK_ROOT", "ANDROID_NDK_HOME"],
            "JDK": ["JAVA_HOME"],
            "Vulkan SDK": ["VULKAN_SDK"],
        }
        ini_values: dict[str, str] = {}
        ini_path = (
            self.profile.engine_root
            / "Engine"
            / "Config"
            / "Android"
            / "AndroidSDKSettings.ini"
        )
        if ini_path.exists():
            cfg = configparser.ConfigParser()
            cfg.read(ini_path)
            if cfg.has_section("AndroidSDKSettings"):
                sec = cfg["AndroidSDKSettings"]
                ini_values = {
                    "Android SDK": sec.get("SDKPath", ""),
                    "Android NDK": sec.get("NDKPath", ""),
                    "JDK": sec.get("JavaPath", ""),
                    "Vulkan SDK": sec.get("VulkanPath", ""),
                }

        sdk_path: Path | None = None
        for row, (name, parts) in enumerate(components.items()):
            default = self.profile.engine_root.joinpath(*parts)
            candidates: list[Path] = [default]
            ini_val = ini_values.get(name)
            if ini_val:
                candidates.append(Path(ini_val))
            for var in env_vars.get(name, []):
                p = os.environ.get(var)
                if p:
                    candidates.append(Path(p))
            if name == "Android NDK" and sdk_path:
                ndk_dir = sdk_path / "ndk"
                if ndk_dir.exists():
                    subdirs = sorted(
                        [p for p in ndk_dir.iterdir() if p.is_dir()], reverse=True
                    )
                    if subdirs:
                        candidates.insert(0, subdirs[0])
                    candidates.append(ndk_dir)
            path = next((p for p in candidates if p.exists()), default)
            if name == "Android SDK":
                sdk_path = path
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(name))
            self.table.setItem(row, 1, QTableWidgetItem(str(path)))
            if path.is_dir():
                item = QTableWidgetItem("Found")
                item.setForeground(QColor("#0a0"))
            elif path.exists():
                item = QTableWidgetItem("Mismatch")
                item.setForeground(QColor("#c80"))
            else:
                item = QTableWidgetItem("Missing")
                item.setForeground(QColor("#a00"))
            self.table.setItem(row, 2, item)

    # ----- Fix -----
    def _fix_env(self) -> None:
        if not self.profile:
            self.log("[env] No profile selected", "error")
            return
        scripts = self._collect_scripts()
        if not scripts:
            self.log("[env] No fix scripts found", "error")
            return
        dlg = EnvFixDialog(scripts, self)
        if dlg.exec() != QDialog.Accepted:
            return
        selected = dlg.selected_scripts()
        if not selected:
            return
        self._run_scripts(selected)

    def _collect_scripts(self) -> dict[str, Path]:
        assert self.profile
        root = self.profile.engine_root
        scripts: dict[str, Path] = {}
        android_dir = root / "Extras" / "Android"
        for name in ("SetupAndroid.bat", "SetupAndroid.cmd", "SetupAndroid.sh"):
            path = android_dir / name
            if path.exists():
                scripts["Android Dependencies"] = path
                break
        scripts.update(self._fetch_remote_scripts())
        return scripts

    def _fetch_remote_scripts(self) -> dict[str, Path]:
        scripts: dict[str, Path] = {}
        try:
            with urllib.request.urlopen(REMOTE_FIX_SCRIPTS_INDEX) as resp:
                data = json.load(resp)
            tmp_dir = Path(tempfile.mkdtemp(prefix="aegis_fix_"))
            for entry in data:
                name = entry.get("name")
                url = entry.get("url")
                if not name or not url:
                    continue
                dest = tmp_dir / Path(url).name
                urllib.request.urlretrieve(url, dest)
                scripts[name] = dest
        except Exception as exc:  # pragma: no cover - network issues
            self.log(f"[env] {exc}", "error")
        return scripts

    def _run_scripts(self, scripts: list[Path]) -> None:
        if not scripts:
            return
        script = scripts[0]
        argv = self._elevated_argv(script)
        self.log(f"[env] {' '.join(argv)}", "info")

        def _on_exit(code: int) -> None:
            self.log(f"[env] exit code {code}", "success" if code == 0 else "error")
            self._run_checks()
            if len(scripts) > 1:
                self._run_scripts(scripts[1:])

        try:
            self.runner.start(
                argv,
                on_stdout=lambda s: self.log(f"[env] {s}", "info"),
                on_stderr=lambda s: self.log(f"[env] {s}", "error"),
                on_exit=_on_exit,
            )
        except Exception as e:  # pragma: no cover - subprocess failures
            self.log(f"[env] {e}", "error")

    def _elevated_argv(self, script: Path) -> list[str]:
        if os.name == "nt":
            ps_cmd = (
                f"$p=Start-Process -FilePath '{script}' -Verb RunAs -Wait -PassThru; "
                "exit $p.ExitCode"
            )
            return ["powershell", "-NoProfile", "-Command", ps_cmd]
        return ["sudo", str(script)]
