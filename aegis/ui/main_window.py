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
    QVBoxLayout,
    QWidget,
    QHBoxLayout,
    QPushButton,
    QProgressBar,
    QStatusBar,
    QLineEdit,
    QComboBox,
)

from aegis.core.profile import Profile
from aegis.core.settings import settings
from aegis.core.task_runner import TaskRunner
from aegis.ui.widgets.profile_editor import ProfileEditor
from aegis.ui.widgets.key_bindings_editor import KeyBindingsEditor
from aegis.ui.widgets.env_doc import EnvDocPanel
from aegis.ui.widgets.profile_info_bar import ProfileInfoBar
from aegis.ui.widgets.uaft_panel import UaftPanel
from aegis.ui.widgets.log_colors_editor import LogColorsEditor


LAYOUT_VERSION = 3


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aegis Toolbelt")
        self.resize(1280, 800)

        # Runner
        self.runner = TaskRunner()
        self.runner.started.connect(self._task_started)
        self.runner.finished.connect(lambda _code: self._task_finished())

        # Center tabs
        self.tabs = QTabWidget()
        self.env_doc = EnvDocPanel(self.runner, self._log)
        self.uaft_panel = UaftPanel(self.runner, self._log)
        self.tabs.addTab(self.env_doc, "EnvDoc")
        self.tabs.addTab(QTextEdit("Build (stub)"), "Build")
        self.tabs.addTab(QTextEdit("Commandlets (stub)"), "Commandlets")
        self.tabs.addTab(QTextEdit("Pak/IoStore (stub)"), "Pak/IoStore")
        self.tabs.addTab(self.uaft_panel, "Devices / UAFT")
        self.tabs.addTab(QTextEdit("Tests (stub)"), "Tests")
        self.tabs.addTab(QTextEdit("Trace Ops (stub)"), "Trace Ops")

        central = QWidget()
        central_layout = QVBoxLayout(central)
        self.info_bar = ProfileInfoBar()
        central_layout.addWidget(self.info_bar)
        central_layout.addWidget(self.tabs)
        self.setCentralWidget(central)

        # Status bar with progress and cancel button
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        self.cancel_tasks = QPushButton("Cancel All Tasks")
        self.cancel_tasks.setVisible(False)
        self.cancel_tasks.clicked.connect(self.runner.cancel)
        self.status.addPermanentWidget(self.progress)
        self.status.addPermanentWidget(self.cancel_tasks)

        # Dock: Live Log
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log_messages: list[tuple[str, str]] = []
        self.log_colors = settings.log_colors
        self.log_search = QLineEdit()
        self.log_search.setPlaceholderText("Search…")
        self.log_search.textChanged.connect(self._refresh_log_view)
        self.log_filter = QComboBox()
        self.log_filter.addItems(["All", "Info", "Warning", "Error", "Success"])
        self.log_filter.currentTextChanged.connect(self._refresh_log_view)
        self.log_clear = QPushButton("Clear")
        self.log_clear.clicked.connect(self._clear_log)
        log_container = QWidget()
        log_layout = QVBoxLayout(log_container)
        row = QHBoxLayout()
        row.addWidget(self.log_search, 1)
        row.addWidget(self.log_filter)
        row.addWidget(self.log_clear)
        log_layout.addLayout(row)
        log_layout.addWidget(self.log)
        self.logDock = QDockWidget("Live Log")
        self.logDock.setWidget(log_container)
        self.logDock.setObjectName("dock_live_log")
        self.addDockWidget(Qt.BottomDockWidgetArea, self.logDock)

        # Dock: Artifacts
        self.artifacts = QTextEdit("Artifacts (stub)")
        self.artDock = QDockWidget("Artifacts")
        self.artDock.setWidget(self.artifacts)
        self.artDock.setObjectName("dock_artifacts")
        self.addDockWidget(Qt.RightDockWidgetArea, self.artDock)

        self.profile: Profile | None = None
        self.actions: dict[str, QAction] = {}
        self._build_menu()
        self._apply_key_bindings()
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
        file_menu.addAction(act_new)
        act_new.triggered.connect(self._new_window)
        self.actions["file.new_window"] = act_new
        act_exit = QAction("Exit", self)
        file_menu.addAction(act_exit)
        act_exit.triggered.connect(self.close)
        self.actions["file.exit"] = act_exit

        view_menu = self.menuBar().addMenu("&View")
        act_reset = QAction("Reset Layout", self)
        view_menu.addAction(act_reset)
        act_reset.triggered.connect(self._reset_layout)
        self.actions["view.reset_layout"] = act_reset

        tools_menu = self.menuBar().addMenu("&Tools")
        act_echo = QAction("Echo Test Command", self)
        tools_menu.addAction(act_echo)
        act_echo.triggered.connect(self._echo_test)

        profile_menu = self.menuBar().addMenu("&Profile")
        act_new_profile = QAction("New", self)
        profile_menu.addAction(act_new_profile)
        act_new_profile.triggered.connect(self._new_profile)
        self.actions["profile.new"] = act_new_profile
        act_open_profile = QAction("Open…", self)
        profile_menu.addAction(act_open_profile)
        act_open_profile.triggered.connect(self._open_profile)
        self.actions["profile.open"] = act_open_profile
        act_save_profile = QAction("Save", self)
        profile_menu.addAction(act_save_profile)
        act_save_profile.triggered.connect(self._save_profile)
        self.actions["profile.save"] = act_save_profile
        act_edit_profile = QAction("Edit…", self)
        profile_menu.addAction(act_edit_profile)
        act_edit_profile.triggered.connect(self._edit_profile)
        self.actions["profile.edit"] = act_edit_profile

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

        log_menu = settings_menu.addMenu("Log Colors")
        act_edit_log = QAction("Edit…", self)
        log_menu.addAction(act_edit_log)
        act_edit_log.triggered.connect(self._edit_log_colors)
        self.actions["settings.log_colors.edit"] = act_edit_log
        act_import_log = QAction("Import…", self)
        log_menu.addAction(act_import_log)
        act_import_log.triggered.connect(self._import_log_colors)
        self.actions["settings.log_colors.import"] = act_import_log
        act_export_log = QAction("Export…", self)
        log_menu.addAction(act_export_log)
        act_export_log.triggered.connect(self._export_log_colors)
        self.actions["settings.log_colors.export"] = act_export_log
        act_reset_log = QAction("Reset to Defaults", self)
        log_menu.addAction(act_reset_log)
        act_reset_log.triggered.connect(self._reset_log_colors)
        self.actions["settings.log_colors.reset"] = act_reset_log

        kb_menu = settings_menu.addMenu("Key Bindings")
        act_edit_keys = QAction("Edit…", self)
        kb_menu.addAction(act_edit_keys)
        act_edit_keys.triggered.connect(self._edit_key_bindings)
        act_import_keys = QAction("Import…", self)
        kb_menu.addAction(act_import_keys)
        act_import_keys.triggered.connect(self._import_key_bindings)
        act_export_keys = QAction("Export…", self)
        kb_menu.addAction(act_export_keys)
        act_export_keys.triggered.connect(self._export_key_bindings)
        act_reset_keys = QAction("Reset to Defaults", self)
        kb_menu.addAction(act_reset_keys)
        act_reset_keys.triggered.connect(self._reset_key_bindings)

        help_menu = self.menuBar().addMenu("&Help")
        act_about = QAction("About", self)
        help_menu.addAction(act_about)
        act_about.triggered.connect(
            lambda: QMessageBox.information(
                self, "About", "Aegis Toolbelt — GUI helper for UE CLIs (and beyond)."
            )
        )

    def _apply_key_bindings(self) -> None:
        kb = settings.key_bindings
        for action_id, act in self.actions.items():
            seq = kb.get(action_id)
            if seq:
                act.setShortcut(seq)

    def _edit_key_bindings(self) -> None:
        dlg = KeyBindingsEditor(settings.key_bindings.all(), self)
        if dlg.exec():
            for action, seq in dlg.get_bindings().items():
                settings.key_bindings.set(action, seq)
            self._apply_key_bindings()

    def _edit_log_colors(self) -> None:
        cfg = self.log_colors.all()
        dlg = LogColorsEditor(cfg["levels"], self.log_colors.regex_rules(), self)
        if dlg.exec():
            levels, regex = dlg.get_config()
            for lvl, col in levels.items():
                self.log_colors.set_level_color(lvl, col)
            self.log_colors.set_regex_rules(regex)
            self._refresh_log_view()

    def _import_log_colors(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Log Colors", "", "JSON (*.json)"
        )
        if path:
            try:
                self.log_colors.import_json(path)
                self._refresh_log_view()
            except Exception as e:
                QMessageBox.critical(self, "Import Error", str(e))

    def _export_log_colors(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Log Colors", "", "JSON (*.json)"
        )
        if path:
            try:
                self.log_colors.export_json(path)
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))

    def _reset_log_colors(self) -> None:
        self.log_colors.reset()
        self._refresh_log_view()

    def _import_key_bindings(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Key Bindings", "", "JSON (*.json)"
        )
        if path:
            try:
                settings.key_bindings.import_json(path)
                self._apply_key_bindings()
            except Exception as e:
                QMessageBox.critical(self, "Import Error", str(e))

    def _export_key_bindings(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Key Bindings", "", "JSON (*.json)"
        )
        if path:
            try:
                settings.key_bindings.export_json(path)
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))

    def _reset_key_bindings(self) -> None:
        settings.key_bindings.reset()
        self._apply_key_bindings()

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
        dlg = ProfileEditor(parent=self)
        if dlg.exec():
            self.profile = dlg.get_profile()
            self._save_profile_as()
            self._profile_changed()

    def _open_profile(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open Profile", "", "JSON (*.json)")
        if path:
            try:
                self.profile = Profile.load(Path(path))
                settings.set_profile_path(path)
                self._profile_changed()
            except Exception as e:
                QMessageBox.critical(self, "Open Error", str(e))

    def _edit_profile(self) -> None:
        if not self.profile:
            QMessageBox.information(self, "No Profile", "No profile to edit.")
            return
        dlg = ProfileEditor(self.profile, self)
        if dlg.exec():
            self.profile = dlg.get_profile()
            self._save_profile()
            self._profile_changed()

    def _save_profile(self) -> None:
        if not getattr(self, "profile", None):
            QMessageBox.information(self, "No Profile", "No profile to save.")
            return
        self._save_profile_as(settings.profile_path())

    def _save_profile_as(self, start_path: str | None = None) -> None:
        if not getattr(self, "profile", None):
            return
        initial = start_path or ""
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Profile", initial, "JSON (*.json)"
        )
        if path:
            try:
                self.profile.save(Path(path))
                settings.set_profile_path(path)
                self._log(f"[profile] Saved to {path}", "success")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", str(e))

    def _load_last_profile(self) -> None:
        path = settings.profile_path()
        if path and Path(path).exists():
            try:
                self.profile = Profile.load(Path(path))
            except Exception:
                self.profile = None
        self._profile_changed()

    def _set_theme(self, mode: str) -> None:
        settings.set_theme_mode(mode)
        self._apply_theme()

    def _create_custom_theme(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select .qss theme", "", "QSS (*.qss)"
        )
        if not path:
            return
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

    def _apply_profile_title(self) -> None:
        base = "Aegis - A UE GUI Toolbelt for UE CLI"
        if self.profile:
            nick = self.profile.nickname.strip()
            proj = self.profile.project_dir.name
            parts = [base]
            if nick:
                parts.append(nick)
            parts.append(proj)
            self.setWindowTitle(" - ".join(parts))
        else:
            self.setWindowTitle(base)

    def _profile_changed(self) -> None:
        self._apply_profile_title()
        self.info_bar.update(self.profile, settings.profile_path())
        self.env_doc.update_profile(self.profile)
        self.uaft_panel.update_profile(self.profile)

    def _log(self, message: str, level: str = "info") -> None:
        self.log_messages.append((message, level))
        if self._log_matches_filters(message, level):
            color = self.log_colors.color_for(message, level)
            self.log.append(f"<span style='color:{color};'>{message}</span>")

    def _clear_log(self) -> None:
        self.log.clear()
        self.log_messages.clear()

    def _log_matches_filters(self, message: str, level: str) -> bool:
        level_filter = self.log_filter.currentText().lower()
        if level_filter != "all" and level != level_filter:
            return False
        query = self.log_search.text().lower()
        return query in message.lower()

    def _refresh_log_view(self) -> None:
        self.log.clear()
        for message, level in self.log_messages:
            if self._log_matches_filters(message, level):
                color = self.log_colors.color_for(message, level)
                self.log.append(f"<span style='color:{color};'>{message}</span>")

    def _task_started(self) -> None:
        self.progress.setVisible(True)
        self.cancel_tasks.setVisible(True)

    def _task_finished(self) -> None:
        self.progress.setVisible(False)
        self.cancel_tasks.setVisible(False)

    def closeEvent(self, ev):
        settings.save_geometry(self.saveGeometry())
        settings.save_state(self.saveState())
        super().closeEvent(ev)
