from pathlib import Path
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QGuiApplication

from PySide6.QtWidgets import (
    QDockWidget,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QTabWidget,
    QTextEdit,
)

from aegis.core.profile import Profile
from aegis.core.settings import settings
from aegis.core.task_runner import TaskRunner


LAYOUT_VERSION = 2


LAYOUT_VERSION = 1


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aegis Toolbelt")
        self.resize(1280, 800)

        # Center tabs (page stubs)
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.tabs.addTab(QTextEdit("Build (stub)"), "Build")
        self.tabs.addTab(QTextEdit("Commandlets (stub)"), "Commandlets")
        self.tabs.addTab(QTextEdit("Pak/IoStore (stub)"), "Pak/IoStore")
        self.tabs.addTab(QTextEdit("Devices / UAFT (stub)"), "Devices / UAFT")
        self.tabs.addTab(QTextEdit("Tests (stub)"), "Tests")
        self.tabs.addTab(QTextEdit("Trace Ops (stub)"), "Trace Ops")

        # Dock: Live Log
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.logDock = QDockWidget("Live Log")
        self.logDock.setWidget(self.log)
        self.logDock.setObjectName("dock_live_log")
        self.addDockWidget(Qt.BottomDockWidgetArea, self.logDock)

        # Dock: Artifacts
        self.artifacts = QTextEdit("Artifacts (stub)")
        self.artDock = QDockWidget("Artifacts")
        self.artDock.setWidget(self.artifacts)
        self.artDock.setObjectName("dock_artifacts")
        self.addDockWidget(Qt.RightDockWidgetArea, self.artDock)

        # Dock: EnvDoc
        from aegis.ui.widgets.env_doc import EnvDocPanel

        self.env_doc = EnvDocPanel()
        self.env_dock = QDockWidget("EnvDoc")
        self.env_dock.setWidget(self.env_doc)
        self.env_dock.setObjectName("dock_env_doc")
        self.addDockWidget(Qt.LeftDockWidgetArea, self.env_dock)

        self.runner = TaskRunner()
        self.profile: Profile | None = None
        self._build_menu()
        self._apply_saved_layout()
        self._apply_saved_theme()
        self._load_last_profile()
        QGuiApplication.styleHints().colorSchemeChanged.connect(
            self._on_system_theme_change
        )

    # ----- Menus -----
    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        act_new = QAction("New Window", self)
        act_new.setShortcut("Ctrl+Shift+N")
        file_menu.addAction(act_new)
        act_new.triggered.connect(self._new_window)
        act_exit = QAction("Exit", self)
        file_menu.addAction(act_exit)
        act_exit.triggered.connect(self.close)

        view_menu = self.menuBar().addMenu("&View")
        act_reset = QAction("Reset Layout", self)
        act_reset.setShortcut("Ctrl+0")
        view_menu.addAction(act_reset)
        act_reset.triggered.connect(self._reset_layout)

        tools_menu = self.menuBar().addMenu("&Tools")
        act_echo = QAction("Echo Test Command", self)
        tools_menu.addAction(act_echo)
        act_echo.triggered.connect(self._echo_test)

        profile_menu = self.menuBar().addMenu("&Profile")
        act_new_profile = QAction("New", self)
        profile_menu.addAction(act_new_profile)
        act_new_profile.triggered.connect(self._new_profile)
        act_open_profile = QAction("Open…", self)
        profile_menu.addAction(act_open_profile)
        act_open_profile.triggered.connect(self._open_profile)
        act_save_profile = QAction("Save", self)
        profile_menu.addAction(act_save_profile)
        act_save_profile.triggered.connect(self._save_profile)

        settings_menu = self.menuBar().addMenu("&Settings")
        theme_menu = settings_menu.addMenu("Load Theme…")
        act_system = QAction("System", self)
        theme_menu.addAction(act_system)
        act_system.triggered.connect(lambda: self._set_theme("system"))
        act_light = QAction("Light", self)
        theme_menu.addAction(act_light)
        act_light.triggered.connect(lambda: self._set_theme("light"))
        act_dark = QAction("Dark", self)
        theme_menu.addAction(act_dark)
        act_dark.triggered.connect(lambda: self._set_theme("dark"))
        act_custom = QAction("Create Custom", self)
        theme_menu.addAction(act_custom)
        act_custom.triggered.connect(self._create_custom_theme)

        help_menu = self.menuBar().addMenu("&Help")
        act_about = QAction("About", self)
        help_menu.addAction(act_about)
        act_about.triggered.connect(
            lambda: QMessageBox.information(
                self,
                "About",
                "Aegis Toolbelt — GUI helper for UE CLIs (and beyond).",
            )
        )

    # ----- Actions -----
    def _new_window(self):
        # launch a new process of this app
        import subprocess

        argv = [sys.executable, "-m", "aegis.app"]
        try:
            subprocess.Popen(argv, shell=False)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _reset_layout(self):
        self.addDockWidget(Qt.BottomDockWidgetArea, self.logDock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.artDock)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.env_dock)

    def _echo_test(self):
        argv = [sys.executable, "-c", "print('Aegis OK')"]
        self._log("[echo] Starting…", "info")
        try:
            self.runner.start(
                argv,
                on_stdout=lambda s: self._log(s, "info"),
                on_stderr=lambda s: self._log(s, "error"),
                on_exit=lambda code: self._log(
                    f"[echo] Exit code: {code}", "success" if code == 0 else "error"
                ),
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _new_profile(self) -> None:
        engine = QFileDialog.getExistingDirectory(self, "Select Engine Root")
        if not engine:
            return
        project = QFileDialog.getExistingDirectory(self, "Select Project Directory")
        if not project:
            return
        self.profile = Profile(Path(engine), Path(project))
        self._save_profile_as()

    def _open_profile(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open Profile", "", "JSON (*.json)")
        if path:
            try:
                self.profile = Profile.load(Path(path))
                settings.set_profile_path(path)
            except Exception as e:
                QMessageBox.critical(self, "Open Error", str(e))

    def _save_profile(self) -> None:
        if not getattr(self, "profile", None):
            QMessageBox.information(self, "No Profile", "No profile to save.")
            return
        path = settings.profile_path()
        if path:
            try:
                self.profile.save(Path(path))
            except Exception as e:
                QMessageBox.critical(self, "Save Error", str(e))
        else:
            self._save_profile_as()

    def _save_profile_as(self) -> None:
        if not getattr(self, "profile", None):
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Profile", "", "JSON (*.json)")
        if path:
            try:
                self.profile.save(Path(path))
                settings.set_profile_path(path)
            except Exception as e:
                QMessageBox.critical(self, "Save Error", str(e))

    def _load_last_profile(self) -> None:
        path = settings.profile_path()
        if path and Path(path).exists():
            try:
                self.profile = Profile.load(Path(path))
            except Exception:
                self.profile = None

    def _set_theme(self, mode: str) -> None:
        settings.set_theme_mode(mode)
        self._apply_theme()

    def _create_custom_theme(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select .qss theme", "", "QSS (*.qss)"
        )
        if path:
            try:
    def _set_theme(self, mode: str) -> None:
        settings.set_theme_mode(mode)
        self._apply_theme()

    def _create_custom_theme(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select .qss theme", "", "QSS (*.qss)"
        )
        if path:
            try:
                settings.set_theme_mode("custom")
                settings.set_custom_theme_path(path)
                self._apply_theme()
            except Exception as e:
                QMessageBox.critical(self, "Theme Error", str(e))

    # ----- Persistence -----
    def _apply_saved_layout(self):
        g = settings.load_geometry()
        if g:
            self.restoreGeometry(g)
        if settings.layout_version() != LAYOUT_VERSION:
            self._reset_layout()
            settings.set_layout_version(LAYOUT_VERSION)
            return
        s = settings.load_state()
        if s:
            self.restoreState(s)

    def _apply_saved_theme(self):
        self._apply_theme()

    def _apply_theme(self, mode: str | None = None) -> None:
        mode = mode or settings.theme_mode()
        theme_dir = Path(__file__).parent / "themes"
        try:
            if mode == "system":
                scheme = QGuiApplication.styleHints().colorScheme()
                fname = "dark.qss" if scheme == Qt.ColorScheme.Dark else "light.qss"
                with open(theme_dir / fname, "r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
            elif mode in ("light", "dark"):
                with open(theme_dir / f"{mode}.qss", "r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
                    self.setStyleSheet(f.read())
            elif mode in ("light", "dark"):
                with open(theme_dir / f"{mode}.qss", "r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
            elif mode == "custom":
                path = settings.custom_theme_path()
                if path:
                    with open(path, "r", encoding="utf-8") as f:
                        self.setStyleSheet(f.read())
        except Exception:
            pass

    def _on_system_theme_change(self) -> None:
        if settings.theme_mode() == "system":
            self._apply_theme("system")

    def _log(self, message: str, level: str = "info") -> None:
        colors = {
            "info": "#888",
            "warning": "#cc0",
            "error": "#b00",
            "success": "#0a0",
        }
        color = colors.get(level, "#888")
        self.log.append(f"<span style='color:{color};'>{message}</span>")

    def closeEvent(self, ev):
        settings.save_geometry(self.saveGeometry())
        settings.save_state(self.saveState())
        super().closeEvent(ev)
