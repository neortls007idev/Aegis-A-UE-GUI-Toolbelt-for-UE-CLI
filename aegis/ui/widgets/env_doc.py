from __future__ import annotations

import configparser
import difflib
import json
import os
import shutil
import subprocess
import tempfile
import urllib.request
from pathlib import Path
from typing import Callable, Optional

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
from aegis.core.ini_parser import parse_ini
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
        self.sdk_path: Path | None = None

        layout = QVBoxLayout(self)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            [
                "Component",
                "Path",
                "Version",
                "Status",
                "Test",
                "Actions",
            ]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.test_button = QPushButton("Test SDK")
        self.test_button.clicked.connect(self._test_sdk)
        layout.addWidget(self.test_button)

        self.test_compat_button = QPushButton("Test SDK (Engine Compatibility)")
        self.test_compat_button.clicked.connect(lambda: self._test_sdk(True))
        layout.addWidget(self.test_compat_button)

        self.fix_button = QPushButton("Fix Env")
        self.fix_button.clicked.connect(self._fix_env)
        layout.addWidget(self.fix_button)

        self.component_paths: dict[str, Path | None] = {}

    # ----- Profile -----
    def update_profile(self, profile: Optional[Profile]) -> None:
        self.profile = profile
        self._run_checks()

    # ----- Checks -----
    def _detect_version(self, component: str, path: Path) -> tuple[str, QColor | None]:
        """Return version string and optional color for warning."""
        try:
            if component in {"Android SDK", "Android NDK"}:
                prop = path / "source.properties"
                if prop.exists():
                    for line in prop.read_text(encoding="utf-8").splitlines():
                        if line.startswith("Pkg.Revision="):
                            return line.split("=", 1)[1].strip(), None
            elif component == "JDK":
                rel = path / "release"
                if rel.exists():
                    for line in rel.read_text(encoding="utf-8").splitlines():
                        if line.startswith("JAVA_VERSION="):
                            return line.split("=", 1)[1].strip().strip('"'), None
            elif component == "Vulkan SDK":
                ver_file = path / "version.txt"
                if ver_file.exists():
                    return ver_file.read_text(encoding="utf-8").strip(), None
        except Exception:  # pragma: no cover - best effort
            pass
        return "Version Unknown", QColor("#c80")

    def _version_from_cmd(self, argv: list[str]) -> str | None:
        try:
            out = subprocess.run(
                argv,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            first = out.stdout.splitlines()
            return first[0].strip() if first else None
        except Exception:  # pragma: no cover - external tool
            return None

    def _run_checks(self) -> None:
        self.table.setRowCount(0)
        self.component_paths = {}
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

        optional_required = {"Vulkan SDK"}
        self.sdk_path = None
        row = 0
        for name, parts in components.items():
            default = self.profile.engine_root.joinpath(*parts)
            candidates: list[Path] = [default]
            ini_val = ini_values.get(name)
            if ini_val:
                candidates.append(Path(ini_val))
            for var in env_vars.get(name, []):
                p = os.environ.get(var)
                if p:
                    candidates.append(Path(p))
            if name == "Android NDK" and self.sdk_path:
                ndk_dir = self.sdk_path / "ndk"
                if ndk_dir.exists():
                    subdirs = sorted(
                        [p for p in ndk_dir.iterdir() if p.is_dir()], reverse=True
                    )
                    if subdirs:
                        candidates.insert(0, subdirs[0])
                    candidates.append(ndk_dir)
            path = next((p for p in candidates if p.exists()), default)
            if name == "Android SDK":
                self.sdk_path = path
            self.component_paths[name] = path
            self.table.insertRow(row)
            display = f"{name} (optional)" if name in optional_required else name
            self.table.setItem(row, 0, QTableWidgetItem(display))
            self.table.setItem(row, 1, QTableWidgetItem(str(path)))
            version_item = QTableWidgetItem("")
            if path.is_dir():
                ver, color = self._detect_version(name, path)
                version_item.setText(ver)
                if color:
                    version_item.setForeground(color)
                status_item = QTableWidgetItem("Found")
                status_item.setForeground(QColor("#0a0"))
            elif path.exists():
                status_item = QTableWidgetItem("Mismatch")
                status_item.setForeground(QColor("#c80"))
            else:
                status_item = QTableWidgetItem("Missing")
                color = "#c80" if name in optional_required else "#a00"
                status_item.setForeground(QColor(color))
            self.table.setItem(row, 2, version_item)
            self.table.setItem(row, 3, status_item)
            test_btn = QPushButton("Test")
            test_btn.clicked.connect(lambda _, comp=name: self._test_component(comp))
            self.table.setCellWidget(row, 4, test_btn)
            fix_btn = QPushButton("Fix")
            fix_btn.clicked.connect(lambda _, comp=name: self._fix_component(comp))
            self.table.setCellWidget(row, 5, fix_btn)
            row += 1

        optional_tools = {
            "CMake": "cmake",
            "NMake": "nmake",
            ".NET SDK": "dotnet",
            "VS Build Tools": "msbuild",
            "Clang-Format": "clang-format",
            "ADB": "adb",
        }
        for name, exe in optional_tools.items():
            path_str = shutil.which(exe) or ""
            status = "Missing"
            ok = False
            version = ""
            ver_color: QColor | None = None
            if path_str:
                ok = True
                if name == ".NET SDK":
                    try:
                        out = subprocess.run(
                            ["dotnet", "--list-sdks"],
                            capture_output=True,
                            text=True,
                            timeout=5,
                            check=False,
                        )
                        versions = [
                            ln.split()[0] for ln in out.stdout.splitlines() if ln
                        ]
                        ok = any(3 <= int(v.split(".")[0]) <= 9 for v in versions)
                        if versions:
                            version = versions[0]
                        else:
                            version = "Version Unknown"
                            ver_color = QColor("#c80")
                    except Exception:  # pragma: no cover - external tool
                        version = "Version Unknown"
                        ver_color = QColor("#c80")
                elif name in {"CMake", "Clang-Format"}:
                    v = self._version_from_cmd([exe, "--version"])
                    if v:
                        version = v
                    else:
                        version = "Version Unknown"
                        ver_color = QColor("#c80")
                elif name == "ADB":
                    v = self._version_from_cmd([exe, "version"])
                    if v:
                        version = v
                    else:
                        version = "Version Unknown"
                        ver_color = QColor("#c80")
                else:
                    version = "Version Unknown"
                    ver_color = QColor("#c80")
                status = "Found" if ok else "Missing"
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(f"{name} (optional)"))
            self.table.setItem(row, 1, QTableWidgetItem(path_str))
            ver_item = QTableWidgetItem(version)
            if ver_color:
                ver_item.setForeground(ver_color)
            self.table.setItem(row, 2, ver_item)
            item = QTableWidgetItem(status)
            item.setForeground(QColor("#0a0" if ok else "#c80"))
            self.table.setItem(row, 3, item)
            self.component_paths[name] = Path(path_str) if path_str else None
            test_btn = QPushButton("Test")
            test_btn.clicked.connect(lambda _, comp=name: self._test_component(comp))
            self.table.setCellWidget(row, 4, test_btn)
            row += 1

    # ----- Fix -----
    def _fix_component(self, component: str) -> None:
        if not self.profile:
            self.log("[env] No profile selected", "error")
            return
        scripts = self._collect_scripts()
        for name, path in scripts.items():
            if component.split()[0].lower() in name.lower():
                self._run_scripts([path])
                return
        self.log(f"[env] No fix script for {component}", "error")

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

    def _find_platforms_dir(self) -> Path | None:
        if not self.sdk_path:
            return None
        direct = self.sdk_path / "platforms"
        if direct.exists():
            return direct
        for p in self.sdk_path.rglob("platforms"):
            parts = [s.lower() for s in p.parts[-3:]]
            if parts[-1] == "platforms" and "sdk" in parts:
                return p
        return None

    def _test_sdk(self, engine_compat: bool = False) -> None:
        if not (self.profile and self.sdk_path):
            self.log("[env] No SDK path", "error")
            return
        cfg_path = None
        for folder in ("Config", "Configs"):
            p = self.profile.project_dir / folder / "DefaultEngine.ini"
            if p.exists():
                cfg_path = p
                break
        if not cfg_path:
            self.log("[env] DefaultEngine.ini not found", "error")
            return
        data = parse_ini(cfg_path)
        section = data.get("/Script/AndroidRuntimeSettings.AndroidRuntimeSettings", {})
        min_sdk = section.get("MinSDKVersion")
        target_sdk = section.get("TargetSDKVersion")
        sdk_override = section.get("SDKAPILevelOverride")
        ndk_override = section.get("NDKAPILevelOverride")
        build_tools_req = section.get("BuildToolsVersion")
        platforms = self._find_platforms_dir()
        installed: list[int] = []
        if platforms and platforms.exists():
            installed = sorted(
                int(p.name.split("-")[1])
                for p in platforms.iterdir()
                if p.name.startswith("android-")
            )
        else:
            self.log("[env] Android SDK platforms not found", "warning")
        highest = max(installed) if installed else 0
        bt_dir = self.sdk_path / "build-tools"
        bt_versions = []
        if bt_dir.exists():
            bt_versions = [p.name for p in bt_dir.iterdir() if p.is_dir()]
            bt_versions.sort(key=lambda s: [int(x) for x in s.split(".")])
        highest_bt = bt_versions[-1] if bt_versions else ""
        all_ok = True
        if engine_compat:
            required_lines: list[str] = []
            installed_lines: list[str] = []
            if min_sdk:
                req = min_sdk
                inst = str(highest)
                required_lines.append(f"MinSDKVersion={req}")
                installed_lines.append(f"MinSDKVersion={inst}")
                if req.lower() != "latest" and int(req) > highest:
                    self.log(
                        f"[env] Installed SDK {highest} < MinSDK {req}",
                        "warning",
                    )
                    all_ok = False
                else:
                    self.log(f"[env] MinSDK {req} OK", "success")
            if target_sdk and target_sdk != min_sdk:
                req = target_sdk
                inst = str(highest)
                required_lines.append(f"TargetSDKVersion={req}")
                installed_lines.append(f"TargetSDKVersion={inst}")
                if req.lower() != "latest" and int(req) > highest:
                    self.log(
                        f"[env] Installed SDK {highest} < TargetSDK {req}",
                        "warning",
                    )
                    all_ok = False
                else:
                    self.log(f"[env] TargetSDK {req} OK", "success")
            if sdk_override:
                req = sdk_override
                inst = str(highest)
                required_lines.append(f"SDKAPILevelOverride={req}")
                installed_lines.append(f"SDKAPILevelOverride={inst}")
                if req.lower() != "latest" and int(req) > highest:
                    self.log(
                        f"[env] Installed SDK {highest} < SDKAPI {req}",
                        "warning",
                    )
                    all_ok = False
                else:
                    self.log(f"[env] SDKAPI {req} OK", "success")
            if ndk_override:
                req = ndk_override
                inst = str(highest)
                required_lines.append(f"NDKAPILevelOverride={req}")
                installed_lines.append(f"NDKAPILevelOverride={inst}")
                if req.lower() != "latest" and int(req) > highest:
                    self.log(
                        f"[env] Installed SDK {highest} < NDKAPI {req}",
                        "warning",
                    )
                    all_ok = False
                else:
                    self.log(f"[env] NDKAPI {req} OK", "success")
            if build_tools_req:
                req = build_tools_req
                inst = highest_bt
                required_lines.append(f"BuildToolsVersion={req}")
                installed_lines.append(f"BuildToolsVersion={inst}")
                if req.lower() != "latest" and inst:

                    def parse(v: str) -> list[int]:
                        return [int(x) for x in v.split(".") if x.isdigit()]

                    if parse(inst) < parse(req):
                        self.log(
                            f"[env] Build-tools {inst} < required {req}",
                            "warning",
                        )
                        all_ok = False
                    else:
                        self.log(f"[env] Build-tools {req} OK", "success")
                elif not inst:
                    self.log("[env] Build-tools not found", "warning")
                    all_ok = False
            diff = "\n".join(
                difflib.unified_diff(
                    required_lines,
                    installed_lines,
                    "engine",
                    "installed",
                    lineterm="",
                )
            )
            if diff:
                self.log(f"[env]\n{diff}", "info")
            if all_ok:
                self.log("[env] SDKs are Engine compatible", "success")
        else:
            if min_sdk:
                p = (platforms / f"android-{min_sdk}") if platforms else None
                if p and p.exists():
                    self.log(f"[env] MinSDK {min_sdk} OK", "success")
                else:
                    self.log(f"[env] Missing platform android-{min_sdk}", "warning")
                    all_ok = False
            if target_sdk and target_sdk != min_sdk:
                p = (platforms / f"android-{target_sdk}") if platforms else None
                if p and p.exists():
                    self.log(f"[env] TargetSDK {target_sdk} OK", "success")
                else:
                    self.log(f"[env] Missing platform android-{target_sdk}", "warning")
                    all_ok = False
        ndk_dir = self.sdk_path / "ndk"
        if not ndk_dir.exists() or not any(ndk_dir.iterdir()):
            self.log("[env] NDK missing", "warning")
            all_ok = False
        build_tools = self.sdk_path / "build-tools"
        if not build_tools.exists() or not any(build_tools.iterdir()):
            self.log("[env] Build-tools missing", "warning")
            all_ok = False
        if not engine_compat and all_ok:
            self.log("[env] Environment configuration functional", "success")

    def _test_component(self, component: str) -> None:
        path = self.component_paths.get(component)
        if component == "Android SDK":
            self._test_sdk()
            return
        if path and path.exists():
            self.log(f"[env] {component} OK", "success")
        else:
            self.log(f"[env] {component} missing", "warning")

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
