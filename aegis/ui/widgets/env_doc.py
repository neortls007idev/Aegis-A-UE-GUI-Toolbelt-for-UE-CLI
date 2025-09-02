from __future__ import annotations

from typing import Callable, Optional
import configparser
import os
import sys
from pathlib import Path

from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QPushButton,
    QWidget,
)

from aegis.core.profile import Profile
from aegis.core.task_runner import TaskRunner


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

        components = {
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

        for row, (name, parts) in enumerate(components.items()):
            default = self.profile.engine_root.joinpath(*parts)
            candidates = [default]
            ini_val = ini_values.get(name)
            if ini_val:
                candidates.append(Path(ini_val))
            for var in env_vars.get(name, []):
                p = os.environ.get(var)
                if p:
                    candidates.append(Path(p))
            path = next((p for p in candidates if p.exists()), default)
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
        script_name = (
            "SetupAndroid.cmd" if sys.platform == "win32" else "SetupAndroid.sh"
        )
        script = self.profile.engine_root / "Extras" / "Android" / script_name
        if not script.exists():
            self.log(f"[env] Fix script not found: {script}", "error")
            return
        argv = [str(script)]
        self.log(f"[env] {' '.join(argv)}", "info")
        try:
            self.runner.start(
                argv,
                on_stdout=lambda s: self.log(f"[env] {s}", "info"),
                on_stderr=lambda s: self.log(f"[env] {s}", "error"),
                on_exit=lambda code: self.log(
                    f"[env] exit code {code}", "success" if code == 0 else "error"
                ),
            )
        except Exception as e:  # pragma: no cover - subprocess failures
            self.log(f"[env] {e}", "error")
