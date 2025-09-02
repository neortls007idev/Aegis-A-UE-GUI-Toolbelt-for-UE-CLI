from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QLineEdit,
    QInputDialog,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from aegis.core.profile import Profile
from aegis.core.task_runner import TaskRunner
from aegis.modules.uaft import Uaft


DEFAULT_CMD_FILE = Path(__file__).resolve().parents[3] / "UECommandline.txt"
if DEFAULT_CMD_FILE.exists():
    DEFAULT_TRACE_ARGS = DEFAULT_CMD_FILE.read_text(encoding="utf-8").strip()
else:
    DEFAULT_TRACE_ARGS = (
        "-tracehost=127.0.0.1 -trace=Bookmark,Frame,CPU,GPU,LoadTime,File "
        "-cpuprofilertrace -statnamedevents -filetrace -loadtimetrace"
    )
MEMORY_TRACE_HINT = "Add -trace=default,memory for Memory Insights (Dev build)"


class UaftPanel(QWidget):
    """UI helper around UnrealAndroidFileTool."""

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
        self.uaft_path: Path | None = None
        self.insights_path: Path | None = None
        self.uaft: Uaft | None = None

        # Paths
        self.uaft_label = QLabel("UAFT: (not found)")
        self.uaft_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.insights_label = QLabel("Unreal Insights: (not found)")
        self.insights_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.build_uaft_btn = QPushButton("Build UAFT")
        self.build_uaft_btn.clicked.connect(self._build_uaft)
        self.build_insights_btn = QPushButton("Build Unreal Insights")
        self.build_insights_btn.clicked.connect(self._build_insights)

        # Connection + packages
        self.security_token = QLineEdit()
        self.port = QLineEdit()
        self.port.setPlaceholderText("57099")
        self.serial = QLineEdit()
        self.serial.setPlaceholderText("auto from device list")
        self.ip = QLineEdit("127.0.0.1")
        self.package = QLineEdit()
        self.package.setPlaceholderText("e.g. com.company.game")

        self.btn_list_devices = QPushButton("List Devices")
        self.btn_list_packages = QPushButton("List Packages")

        self.device_table = QTableWidget(0, 3)
        self.device_table.setHorizontalHeaderLabels(["Make", "Model", "Serial"])
        self.device_table.horizontalHeader().setStretchLastSection(True)
        self.device_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.device_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.device_table.setMinimumHeight(160)

        self.pkg_list = QListWidget()
        self.pkg_list.setSelectionMode(QListWidget.SingleSelection)
        self.pkg_list.setMinimumHeight(120)

        # Trace args
        self.trace_args = QTextEdit()
        self.trace_args.setPlainText(DEFAULT_TRACE_ARGS)
        self.trace_args.setPlaceholderText(MEMORY_TRACE_HINT)
        self.trace_args.setToolTip(MEMORY_TRACE_HINT)
        self.btn_write_cmd = QPushButton("Generate and Push UECommandLine.txt")

        # Traces
        self.btn_refresh_traces = QPushButton("Refresh Traces")
        self.trace_list = QListWidget()
        self.trace_list.setSelectionMode(QListWidget.SingleSelection)
        self.trace_list.setMinimumHeight(160)
        self.pull_dir = QLineEdit(str(Path.home() / "UnrealTraces"))
        self.btn_choose_dir = QPushButton("Choose Folder…")
        self.btn_pull = QPushButton("Pull Selected Trace")
        self.chk_open_insights = QCheckBox("Open in Unreal Insights after pull")

        self._build_layout()
        self._connect_signals()
        self.build_uaft_btn.hide()
        self.build_insights_btn.hide()

    # ----- Layout helpers -----
    def _build_layout(self) -> None:
        root = QVBoxLayout(self)
        root.addWidget(self.uaft_label)
        root.addWidget(self.build_uaft_btn)
        root.addSpacing(8)
        root.addWidget(self.insights_label)
        root.addWidget(self.build_insights_btn)

        box_conn = QGroupBox("Connection")
        lc = QVBoxLayout()
        lc.addLayout(
            self._row(
                [
                    QLabel("Security Token:"),
                    self.security_token,
                    QLabel("Port:"),
                    self.port,
                ]
            )
        )
        lc.addLayout(
            self._row(
                [
                    QLabel("Device Serial:"),
                    self.serial,
                    QLabel("or IP:"),
                    self.ip,
                    QLabel("Package:"),
                    self.package,
                ]
            )
        )
        lc.addLayout(self._row([self.btn_list_devices, self.btn_list_packages]))
        lc.addWidget(self.device_table)
        lc.addWidget(self.pkg_list)
        box_conn.setLayout(lc)
        root.addWidget(box_conn)

        box_args = QGroupBox("Command Line Arguments/Trace Arguments")
        la = QVBoxLayout()
        la.addWidget(self.trace_args)
        la.addWidget(self.btn_write_cmd)
        box_args.setLayout(la)
        root.addWidget(box_args)

        box_traces = QGroupBox("Traces on Device")
        lt = QVBoxLayout()
        lt.addWidget(self.btn_refresh_traces)
        lt.addWidget(self.trace_list)
        lt.addLayout(
            self._row(
                [
                    QLabel("Pull to:"),
                    self.pull_dir,
                    self.btn_choose_dir,
                    self.btn_pull,
                    self.chk_open_insights,
                ]
            )
        )
        box_traces.setLayout(lt)
        root.addWidget(box_traces)
        root.addStretch(1)

    def _row(self, widgets: list[QWidget]) -> QHBoxLayout:
        h = QHBoxLayout()
        for w in widgets:
            h.addWidget(w)
        h.addStretch(1)
        return h

    def _connect_signals(self) -> None:
        self.btn_list_devices.clicked.connect(self._list_devices)
        self.btn_list_packages.clicked.connect(self._list_packages)
        self.device_table.itemSelectionChanged.connect(self._device_selected)
        self.pkg_list.itemClicked.connect(lambda it: self.package.setText(it.text()))
        self.btn_write_cmd.clicked.connect(self._write_cmd)
        self.btn_refresh_traces.clicked.connect(self._refresh_traces)
        self.btn_choose_dir.clicked.connect(self._choose_dir)
        self.btn_pull.clicked.connect(self._pull_trace)

    # ----- Profile -----
    def update_profile(self, profile: Optional[Profile]) -> None:
        self.profile = profile
        self._scan()
        self._apply_project_prefix()
        self._load_security_token()

    def _apply_project_prefix(self) -> None:
        if not self.profile:
            self.trace_args.setPlainText(DEFAULT_TRACE_ARGS)
            return
        proj = self.profile.project_dir.name
        prefix = f"../../../{proj}/{proj}.uproject "
        self.trace_args.setPlainText(prefix + DEFAULT_TRACE_ARGS)

    def _load_security_token(self) -> None:
        self.security_token.clear()
        if not self.profile:
            return
        cfg = self.profile.project_dir / "Config" / "DefaultGame.ini"
        if not cfg.exists():
            return
        for line in cfg.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("SecurityToken="):
                token = line.split("=", 1)[1].strip()
                if token:
                    self.security_token.setText(token)
                break

    def _scan(self) -> None:
        self.uaft_path = None
        self.insights_path = None
        self.uaft = None
        if not self.profile:
            self.uaft_label.setText("UAFT: (no profile)")
            self.insights_label.setText("Unreal Insights: (no profile)")
            self.build_uaft_btn.hide()
            self.build_insights_btn.hide()
            return

        engine_root = self.profile.engine_root
        self.uaft_path = next(engine_root.rglob("UnrealAndroidFileTool.exe"), None)
        if not self.uaft_path:
            self.uaft_path = next(engine_root.rglob("UnrealAndroidFileTool"), None)
        self.insights_path = next(engine_root.rglob("UnrealInsights.exe"), None)
        if not self.insights_path:
            self.insights_path = next(engine_root.rglob("UnrealInsights"), None)

        self.uaft = Uaft(self.uaft_path) if self.uaft_path else None
        self.uaft_label.setText(
            f"UAFT: {self.uaft_path}" if self.uaft_path else "UAFT: (not found)"
        )
        self.insights_label.setText(
            f"Unreal Insights: {self.insights_path}"
            if self.insights_path
            else "Unreal Insights: (not found)"
        )
        self.build_uaft_btn.setVisible(self.uaft_path is None)
        self.build_insights_btn.setVisible(self.insights_path is None)

    # ----- Helpers -----
    def _require_uaft(self) -> Uaft | None:
        if not self.uaft:
            self.log("[uaft] UAFT not found", "error")
            return None
        return self.uaft

    def _log_cmd(self, argv: list[str], token: str | None) -> None:
        shown = ["<redacted>" if token and a == token else a for a in argv]
        self.log(f"[uaft] {' '.join(shown)}", "info")

    def _adb_device_info(self, serial: str) -> tuple[str, str]:
        try:
            make = subprocess.run(
                ["adb", "-s", serial, "shell", "getprop", "ro.product.manufacturer"],
                capture_output=True,
                text=True,
                check=False,
            ).stdout.strip()
            model = subprocess.run(
                ["adb", "-s", serial, "shell", "getprop", "ro.product.model"],
                capture_output=True,
                text=True,
                check=False,
            ).stdout.strip()
            return make or "?", model or serial
        except Exception:
            return "?", serial

    # ----- Actions -----
    def _list_devices(self) -> None:
        uaft = self._require_uaft()
        if not uaft:
            return
        lines: list[str] = []
        argv = uaft.devices_argv()
        self.log(f"[uaft] {' '.join(argv)}", "info")
        try:
            self.runner.start(
                argv,
                on_stdout=lines.append,
                on_stderr=lambda s: self.log(f"[uaft] {s}", "error"),
                on_exit=lambda code: self._on_devices_exit(code, lines),
            )
        except Exception as e:  # pragma: no cover - subprocess failures
            self.log(f"[uaft] {e}", "error")

    def _on_devices_exit(self, code: int, lines: list[str]) -> None:
        if code != 0:
            self.log(f"[uaft] exit code {code}", "error")
            return
        devs = Uaft.parse_devices(lines)
        self.device_table.setRowCount(0)
        for serial in devs:
            make, model = self._adb_device_info(serial)
            row = self.device_table.rowCount()
            self.device_table.insertRow(row)
            self.device_table.setItem(row, 0, QTableWidgetItem(make))
            self.device_table.setItem(row, 1, QTableWidgetItem(model))
            self.device_table.setItem(row, 2, QTableWidgetItem(serial))
        if devs:
            self.device_table.selectRow(0)
            self.serial.setText(devs[0])
        self.log(f"[uaft] found {len(devs)} device(s)", "info")

    def _device_selected(self) -> None:
        row = self.device_table.currentRow()
        if row >= 0:
            serial = self.device_table.item(row, 2).text()
            self.serial.setText(serial)

    def _list_packages(self) -> None:
        uaft = self._require_uaft()
        if not uaft:
            return
        dev = self.serial.text().strip() or None
        lines: list[str] = []
        argv = uaft.packages_argv(dev)
        self.log(f"[uaft] {' '.join(argv)}", "info")
        try:
            self.runner.start(
                argv,
                on_stdout=lines.append,
                on_stderr=lambda s: self.log(f"[uaft] {s}", "error"),
                on_exit=lambda code: self._on_packages_exit(code, lines),
            )
        except Exception as e:
            self.log(f"[uaft] {e}", "error")

    def _on_packages_exit(self, code: int, lines: list[str]) -> None:
        if code != 0:
            self.log(f"[uaft] exit code {code}", "error")
            return
        pkgs = Uaft.parse_packages(lines)
        self.pkg_list.clear()
        for p in pkgs:
            self.pkg_list.addItem(QListWidgetItem(p))
        if pkgs:
            self.pkg_list.setCurrentRow(0)
            self.package.setText(pkgs[0])
        self.log(f"[uaft] found {len(pkgs)} package(s)", "info")

    def _write_cmd(self) -> None:
        uaft = self._require_uaft()
        if not uaft:
            return
        serial = self.serial.text().strip() or None
        ip = None if serial else (self.ip.text().strip() or None)
        port = self.port.text().strip() or None
        pkg = self.package.text().strip()
        token = self.security_token.text().strip() or None
        if not token:
            token, ok = QInputDialog.getText(
                self,
                "Security Token Required",
                (
                    "Security token not configured.\n"
                    "Enter the token from Project Settings → Plugins → Android File Server"
                    " → Packaging or Config/DefaultGame.ini"
                ),
            )
            if not ok or not token:
                self.log("[uaft] Security token required", "error")
                return
            self.security_token.setText(token)
        if not pkg:
            self.log("[uaft] Package is required", "error")
            return
        content = self.trace_args.toPlainText().strip()
        if not content:
            self.log("[uaft] Trace arguments required", "error")
            return
        tmp = Path.home() / "UECommandLine.txt"
        tmp.write_text(content, encoding="utf-8")
        argv = uaft.push_commandfile_argv(serial, ip, port, pkg, token, str(tmp))
        self._log_cmd(argv, token)
        try:
            self.runner.start(
                argv,
                on_stdout=lambda s: self.log(f"[uaft] {s}", "info"),
                on_stderr=lambda s: self.log(f"[uaft] {s}", "error"),
                on_exit=lambda code: self.log(
                    f"[uaft] exit code {code}", "success" if code == 0 else "error"
                ),
            )
        except Exception as e:
            self.log(f"[uaft] {e}", "error")

    def _refresh_traces(self) -> None:
        uaft = self._require_uaft()
        if not uaft:
            return
        serial = self.serial.text().strip() or None
        ip = None if serial else (self.ip.text().strip() or None)
        port = self.port.text().strip() or None
        pkg = self.package.text().strip()
        token = self.security_token.text().strip() or None
        if not pkg:
            self.log("[uaft] Package is required", "error")
            return
        lines: list[str] = []
        argv = uaft.list_traces_argv(serial, ip, port, pkg, token)
        self._log_cmd(argv, token)
        try:
            self.runner.start(
                argv,
                on_stdout=lines.append,
                on_stderr=lambda s: self.log(f"[uaft] {s}", "error"),
                on_exit=lambda code: self._on_traces_exit(code, lines),
            )
        except Exception as e:
            self.log(f"[uaft] {e}", "error")

    def _on_traces_exit(self, code: int, lines: list[str]) -> None:
        if code != 0:
            self.log(f"[uaft] exit code {code}", "error")
            return
        traces = Uaft.parse_traces(lines)
        self.trace_list.clear()
        for f in traces:
            self.trace_list.addItem(QListWidgetItem(f))
        self.log(f"[uaft] found {len(traces)} trace(s)", "info")

    def _choose_dir(self) -> None:
        d = QFileDialog.getExistingDirectory(
            self, "Choose destination folder", self.pull_dir.text()
        )
        if d:
            self.pull_dir.setText(d)

    def _pull_trace(self) -> None:
        uaft = self._require_uaft()
        if not uaft:
            return
        item = self.trace_list.currentItem()
        if not item:
            self.log("[uaft] Select a trace first", "error")
            return
        serial = self.serial.text().strip() or None
        ip = None if serial else (self.ip.text().strip() or None)
        port = self.port.text().strip() or None
        pkg = self.package.text().strip()
        token = self.security_token.text().strip() or None
        remote = item.text()
        dest = Path(self.pull_dir.text().strip())
        argv = uaft.pull_trace_argv(serial, ip, port, pkg, token, remote, dest)
        local_path = dest / Path(remote).name
        self._log_cmd(argv, token)
        try:
            self.runner.start(
                argv,
                on_stdout=lambda s: self.log(f"[uaft] {s}", "info"),
                on_stderr=lambda s: self.log(f"[uaft] {s}", "error"),
                on_exit=lambda code: self._on_pull_exit(code, local_path),
            )
        except Exception as e:
            self.log(f"[uaft] {e}", "error")

    def _on_pull_exit(self, code: int, local: Path) -> None:
        if code != 0:
            self.log(f"[uaft] exit code {code}", "error")
            return
        self.log(f"[uaft] Pulled {local}", "success")
        if self.chk_open_insights.isChecked() and self.insights_path:
            self._open_insights(local)

    def _open_insights(self, trace_path: Path) -> None:
        exe = self.insights_path
        if not exe or not exe.exists():
            self.log("[insights] Unreal Insights not found", "error")
            return
        try:
            subprocess.Popen([str(exe), str(trace_path)], shell=False)
            self.log("[insights] Launched Unreal Insights", "info")
        except Exception as e:  # pragma: no cover - external tool failures
            self.log(f"[insights] {e}", "error")

    # ----- Build -----
    def _build_uaft(self) -> None:
        if not self.profile:
            self.log("[uaft] No profile selected", "error")
            return
        script_name = "RunUAT.bat" if sys.platform == "win32" else "RunUAT.sh"
        script = (
            self.profile.engine_root / "Engine" / "Build" / "BatchFiles" / script_name
        )
        argv = [str(script), "BuildUAFT"]
        self._run(argv, "uaft")

    def _build_insights(self) -> None:
        if not self.profile:
            self.log("[insights] No profile selected", "error")
            return
        script_name = "RunUAT.bat" if sys.platform == "win32" else "RunUAT.sh"
        script = (
            self.profile.engine_root / "Engine" / "Build" / "BatchFiles" / script_name
        )
        argv = [str(script), "BuildUnrealInsights"]
        self._run(argv, "insights")

    def _run(self, argv: list[str], tag: str) -> None:
        self.log(f"[{tag}] {' '.join(argv)}", "info")
        try:
            self.runner.start(
                argv,
                on_stdout=lambda s: self.log(f"[{tag}] {s}", "info"),
                on_stderr=lambda s: self.log(f"[{tag}] {s}", "error"),
                on_exit=lambda code: self.log(
                    f"[{tag}] exit code {code}", "success" if code == 0 else "error"
                ),
            )
        except Exception as e:  # pragma: no cover - subprocess failures
            self.log(f"[{tag}] {e}", "error")
