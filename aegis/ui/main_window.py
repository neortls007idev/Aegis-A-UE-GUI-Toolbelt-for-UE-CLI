from pathlib import Path
import sys
import subprocess
from datetime import datetime

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QAction, QDesktopServices, QGuiApplication
from PySide6.QtWidgets import (
    QDockWidget,
    QBoxLayout,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QMenu,
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
    QPlainTextEdit,
)

from aegis.core.profile import Profile
from aegis.core.settings import settings
from aegis.core.task_runner import TaskRunner
from aegis.core.app_preferences import (
    list_profiles,
    list_themes,
    list_log_colors,
    list_keybindings,
)
from aegis.ui.widgets.profile_editor import ProfileEditor
from aegis.ui.widgets.key_bindings_editor import KeyBindingsEditor
from aegis.ui.widgets.env_doc import EnvDocPanel
from aegis.ui.widgets.profile_info_bar import ProfileInfoBar
from aegis.ui.widgets.uaft_panel import UaftPanel
from aegis.ui.widgets.log_colors_editor import LogColorsEditor
from aegis.ui.widgets.feedback_dialog import FeedbackDialog
from aegis.ui.widgets.help_dialog import HelpDialog
from aegis.ui.widgets.batch_builder_panel import BatchBuilderPanel


LAYOUT_VERSION = 4
LOG_LABELS = {
    "info": "Information:",
    "error": "Error:",
    "warning": "Warning:",
    "success": "Success:",
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Aegis Toolbelt")
        self.resize(1280, 800)

        # Runner
        self.runner = TaskRunner()
        self.runner.started.connect(self._task_started)
        self.runner.finished.connect(lambda _code: self._task_finished())

        self._batch_active = False

        # Center tabs
        self.tabs = QTabWidget()
        self.env_doc = EnvDocPanel(self.runner, self._log)
        env_container = QWidget()
        env_layout = QVBoxLayout(env_container)
        env_layout.addWidget(self.env_doc, 1)
        self.batch_panel = BatchBuilderPanel(self.runner, self._log)
        self.batch_panel.batch_started.connect(self._batch_started)
        self.batch_panel.batch_progress.connect(self._batch_progress)
        self.batch_panel.batch_finished.connect(self._batch_finished)
        self.command_edit = QPlainTextEdit()
        self.command_edit.textChanged.connect(self._command_preview_changed)
        build_tabs = QTabWidget()
        build_tabs.addTab(self.batch_panel, "Tasks")
        build_tabs.addTab(self.command_edit, "Edit Batch Commands")
        self.batch_panel.tasks_changed.connect(self._refresh_command_edit)
        self._refresh_command_edit()
        build_container = QWidget()
        build_layout = QVBoxLayout(build_container)
        build_layout.addWidget(build_tabs, 1)
        self.build_tabs = build_tabs
        self.uaft_panel = UaftPanel(self.runner, self._log)
        uaft_container = QWidget()
        uaft_layout = QVBoxLayout(uaft_container)
        uaft_layout.addWidget(self.uaft_panel, 1)
        self.tabs.addTab(env_container, "EnvDoc")
        self.tabs.addTab(build_container, "Build")
        self.tabs.addTab(QTextEdit("Commandlets (stub)"), "Commandlets")
        self.tabs.addTab(QTextEdit("Pak/IoStore (stub)"), "Pak/IoStore")
        self.tabs.addTab(uaft_container, "Devices / UAFT")
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
        self.cancel_tasks.clicked.connect(self._cancel_tasks)
        self.status.addPermanentWidget(self.progress)
        self.status.addPermanentWidget(self.cancel_tasks)

        # Dock: Live Log
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log_messages: list[tuple[str, str, str]] = []
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
        self.log_controls = row
        self.logDock = QDockWidget("Live Log")
        self.logDock.setWidget(log_container)
        self.logDock.setObjectName("dock_live_log")
        self.addDockWidget(Qt.BottomDockWidgetArea, self.logDock)
        self.logDock.setFeatures(
            QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable
        )
        self.logDock.setAllowedAreas(
            Qt.BottomDockWidgetArea
            | Qt.TopDockWidgetArea
            | Qt.LeftDockWidgetArea
            | Qt.RightDockWidgetArea
        )
        self.logDock.topLevelChanged.connect(lambda _t: self._reset_log_dock_size())
        self.logDock.dockLocationChanged.connect(
            lambda _area: self._reset_log_dock_size()
        )
        self._reset_log_dock_size()
        self.logDock.show()

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

    def resizeEvent(self, event):  # type: ignore[override]
        super().resizeEvent(event)
        self._reset_log_dock_size()

    def _reset_log_dock_size(self) -> None:
        self.logDock.setMinimumSize(0, 0)
        self.logDock.widget().setMinimumSize(0, 0)
        area = self.dockWidgetArea(self.logDock)
        if area in (Qt.LeftDockWidgetArea, Qt.RightDockWidgetArea):
            self.log_controls.setDirection(QBoxLayout.TopToBottom)
        else:
            self.log_controls.setDirection(QBoxLayout.LeftToRight)

    def _refresh_command_edit(self) -> None:
        cmds = self.batch_panel.all_command_previews()
        lines: list[str] = []
        for i, cmd in enumerate(cmds, start=1):
            prefix = f"{i}: "
            if not self.batch_panel.task_is_editable(i - 1):
                prefix += "[locked] "
            lines.append(prefix + cmd)
        text = "\n".join(lines)
        self.command_edit.blockSignals(True)
        self.command_edit.setPlainText(text)
        self.command_edit.blockSignals(False)

    def _command_preview_changed(self) -> None:
        lines = self.command_edit.toPlainText().splitlines()
        for i, line in enumerate(lines):
            if ":" in line:
                _, cmd_part = line.split(":", 1)
                cmd = cmd_part.strip()
            else:
                cmd = line.strip()
            if self.batch_panel.task_is_editable(i):
                self.batch_panel.set_command_override(i, cmd, emit=False)
        self.batch_panel.tasks_changed.emit()

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
        self._populate_profile_menu(profile_menu)

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
        self._populate_theme_menu(theme_menu)

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
        self._populate_log_colors_menu(log_menu)

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
        self._populate_keybindings_menu(kb_menu)

        help_menu = self.menuBar().addMenu("&Help")
        act_help = QAction("Help", self)
        help_menu.addAction(act_help)
        act_help.triggered.connect(self._show_help)
        self.actions["help.contents"] = act_help

        act_feedback = QAction("Provide Feedback", self)
        help_menu.addAction(act_feedback)
        act_feedback.triggered.connect(self._send_feedback)
        self.actions["help.feedback"] = act_feedback

        act_about = QAction("About", self)
        help_menu.addAction(act_about)
        act_about.triggered.connect(self._show_about)
        self.actions["help.about"] = act_about

    def _populate_profile_menu(self, menu: QMenu) -> None:
        paths = list_profiles()
        if paths:
            menu.addSeparator()
            for path in paths:
                act = QAction(path.stem, self)
                act.triggered.connect(
                    lambda _checked=False, p=path: self._open_profile_file(p)
                )
                menu.addAction(act)

    def _populate_theme_menu(self, menu: QMenu) -> None:
        paths = list_themes()
        if paths:
            menu.addSeparator()
            for path in paths:
                act = QAction(path.stem, self)
                act.triggered.connect(
                    lambda _checked=False, p=path: self._load_theme_file(p)
                )
                menu.addAction(act)

    def _populate_log_colors_menu(self, menu: QMenu) -> None:
        paths = list_log_colors()
        if paths:
            menu.addSeparator()
            for path in paths:
                act = QAction(path.stem, self)
                act.triggered.connect(
                    lambda _checked=False, p=path: self._load_log_colors_file(p)
                )
                menu.addAction(act)

    def _populate_keybindings_menu(self, menu: QMenu) -> None:
        paths = list_keybindings()
        if paths:
            menu.addSeparator()
            for path in paths:
                act = QAction(path.stem, self)
                act.triggered.connect(
                    lambda _checked=False, p=path: self._load_key_bindings_file(p)
                )
                menu.addAction(act)

    def _show_help(self) -> None:
        readme = Path(__file__).resolve().parents[2] / "README.md"
        dlg = HelpDialog(readme, self)
        dlg.exec()

    def _send_feedback(self) -> None:
        dlg = FeedbackDialog(self)
        if dlg.exec():
            subject, body = dlg.get_feedback()
            import urllib.parse

            query = urllib.parse.urlencode({"subject": subject, "body": body})
            QDesktopServices.openUrl(
                QUrl(f"mailto:rahulguptagamedev@gmail.com?{query}")
            )

    def _show_about(self) -> None:
        version = self._get_version()
        repo_url = (
            "https://github.com/rahulguptagamedev/Aegis-A-UE-GUI-Toolbelt-for-UE-CLI"
        )
        info = (
            f"<b>Aegis Toolbelt</b><br>Version: {version}<br>"
            "Author: Rahul Gupta<br>"
            f"Repository: <a href='{repo_url}'>{repo_url}</a><br>"
            "A UE GUI toolbelt for Unreal Engine command-line tools.<br>"
            "Licensed under the <a href='https://www.apache.org/licenses/LICENSE-2.0'>Apache 2.0 License</a>."
        )
        msg = QMessageBox(self)
        msg.setWindowTitle("About")
        msg.setTextFormat(Qt.RichText)
        msg.setTextInteractionFlags(Qt.TextBrowserInteraction)
        msg.setText(info)
        msg.exec()

    def _get_version(self) -> str:
        try:
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except Exception:
            return "unknown"

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
        orig_levels = cfg["levels"]
        orig_regex = self.log_colors.regex_rules()
        dlg = LogColorsEditor(
            orig_levels,
            orig_regex,
            self,
            on_preview=self._preview_log_color,
        )
        if dlg.exec():
            levels, regex = dlg.get_config()
            for lvl, col in levels.items():
                self.log_colors.set_level_color(lvl, col)
            self.log_colors.set_regex_rules(regex)
        else:
            for lvl, col in orig_levels.items():
                self.log_colors.set_level_color(lvl, col)
            self.log_colors.set_regex_rules(orig_regex)
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

    def _load_log_colors_file(self, path: Path) -> None:
        try:
            self.log_colors.import_json(str(path))
            self._refresh_log_view()
        except Exception as e:
            QMessageBox.critical(self, "Import Error", str(e))

    def _preview_log_color(self, level: str, color: str) -> None:
        self.log_colors.set_level_color(level, color)
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

    def _load_key_bindings_file(self, path: Path) -> None:
        try:
            settings.key_bindings.import_json(str(path))
            self._apply_key_bindings()
        except Exception as e:
            QMessageBox.critical(self, "Import Error", str(e))

    # ----- Actions -----
    def _new_window(self):
        # launch a new process of this app
        argv = [sys.executable, "-m", "aegis.app"]
        try:
            subprocess.Popen(argv, shell=False)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _reset_layout(self):
        self.addDockWidget(Qt.BottomDockWidgetArea, self.logDock)
        self.logDock.show()
        self._reset_log_dock_size()

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

    def _open_profile_file(self, path: Path) -> None:
        try:
            self.profile = Profile.load(path)
            settings.set_profile_path(str(path))
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

    def _load_theme_file(self, path: Path) -> None:
        try:
            settings.set_theme_mode("custom")
            settings.set_custom_theme_path(str(path))
            self._apply_theme()
        except Exception as e:
            QMessageBox.critical(self, "Theme Error", str(e))

    # ----- Persistence -----
    def _apply_saved_layout(self):
        g = settings.load_geometry()
        if g:
            self.restoreGeometry(g)
        else:
            self.setWindowState(self.windowState() | Qt.WindowMaximized)
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
        self.batch_panel.update_profile(self.profile)
        self.uaft_panel.update_profile(self.profile)

    def _log(self, message: str, level: str = "info") -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_messages.append((ts, message, level))
        if not self.logDock.isVisible():
            self.logDock.show()
        if self._log_matches_filters(message, level):
            color = self.log_colors.color_for(message, level)
            label = LOG_LABELS.get(level, f"{level.title()}:")
            self.log.append(
                f"<span style='color:{color};'>{ts} {label} {message}</span>"
            )

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
        for ts, message, level in self.log_messages:
            if self._log_matches_filters(message, level):
                color = self.log_colors.color_for(message, level)
                label = LOG_LABELS.get(level, f"{level.title()}:")
                self.log.append(
                    f"<span style='color:{color};'>{ts} {label} {message}</span>"
                )

    def _task_started(self) -> None:
        self.progress.setVisible(True)
        self.cancel_tasks.setVisible(True)

    def _task_finished(self) -> None:
        if not self._batch_active:
            self.progress.setVisible(False)
            self.cancel_tasks.setVisible(False)

    def _batch_started(self, total: int) -> None:
        self._batch_active = True
        self.progress.setRange(0, total)
        self.progress.setValue(0)
        self.progress.setVisible(True)
        self.cancel_tasks.setVisible(True)

    def _batch_progress(self, value: int) -> None:
        self.progress.setValue(value)

    def _batch_finished(self) -> None:
        self._batch_active = False
        self.progress.setVisible(False)
        self.cancel_tasks.setVisible(False)
        self.progress.setRange(0, 0)

    def _cancel_tasks(self) -> None:
        self.runner.cancel()
        self.batch_panel.cancel_batch()

    def closeEvent(self, ev):
        settings.save_geometry(self.saveGeometry())
        settings.save_state(self.saveState())
        super().closeEvent(ev)
