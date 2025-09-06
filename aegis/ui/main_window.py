from __future__ import annotations

from pathlib import Path
import sys
import subprocess

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QAction, QDesktopServices, QGuiApplication
from PySide6.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QFileDialog,
    QProgressBar,
    QPushButton,
    QStatusBar,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from aegis.core.settings import settings
from aegis.core.task_runner import TaskRunner
from aegis.ui.key_binding_actions import KeyBindingActions
from aegis.ui.profile_actions import ProfileActions
from aegis.ui.theme_actions import ThemeActions
from aegis.ui.widgets.batch_builder_panel import BatchBuilderPanel
from aegis.ui.widgets.command_editor import CommandEditor
from aegis.ui.widgets.env_doc import EnvDocPanel
from aegis.ui.widgets.feedback_dialog import FeedbackDialog
from aegis.ui.widgets.help_dialog import HelpDialog
from aegis.ui.widgets.log_colors_editor import LogColorsEditor
from aegis.ui.widgets.log_panel import LogPanel
from aegis.ui.widgets.profile_info_bar import ProfileInfoBar
from aegis.ui.widgets.uaft_panel import UaftPanel
from aegis.ui.menu_builder import build_menu


class MainWindow(QMainWindow, KeyBindingActions, ProfileActions, ThemeActions):
    def __init__(self) -> None:
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

        self.command_editor = CommandEditor(self.batch_panel)

        build_tabs = QTabWidget()
        build_tabs.addTab(self.batch_panel, "Tasks")
        build_tabs.addTab(self.command_editor, "Edit Batch Commands")
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
        self.log_panel = LogPanel(self)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.log_panel)

        self.profile = None
        self.actions: dict[str, QAction] = build_menu(self)
        self._apply_key_bindings()
        self._apply_saved_layout()
        self._apply_saved_theme()
        self._load_last_profile()
        QGuiApplication.styleHints().colorSchemeChanged.connect(
            self._on_system_theme_change
        )

    def resizeEvent(self, event):  # type: ignore[override]
        super().resizeEvent(event)
        self.log_panel.reset_size()

    # ----- Log colors -----
    def _edit_log_colors(self) -> None:
        cfg = self.log_panel.log_colors.all()
        orig_levels = cfg["levels"]
        orig_regex = self.log_panel.log_colors.regex_rules()
        dlg = LogColorsEditor(
            orig_levels,
            orig_regex,
            self,
            on_preview=self.log_panel.log_message,
        )
        if dlg.exec():
            levels, regex = dlg.get_config()
            for lvl, col in levels.items():
                self.log_panel.log_colors.set_level_color(lvl, col)
            self.log_panel.log_colors.set_regex_rules(regex)
        else:
            for lvl, col in orig_levels.items():
                self.log_panel.log_colors.set_level_color(lvl, col)
            self.log_panel.log_colors.set_regex_rules(orig_regex)
        self.log_panel.refresh_view()

    def _import_log_colors(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Log Colors", "", "JSON (*.json)"
        )
        if path:
            try:
                self.log_panel.log_colors.import_json(path)
                self.log_panel.refresh_view()
            except Exception as e:
                QMessageBox.critical(self, "Import Error", str(e))

    def _export_log_colors(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Log Colors", "", "JSON (*.json)"
        )
        if path:
            try:
                self.log_panel.log_colors.export_json(path)
            except Exception as e:
                QMessageBox.critical(self, "Export Error", str(e))

    def _reset_log_colors(self) -> None:
        self.log_panel.log_colors.reset()
        self.log_panel.refresh_view()

    def _load_log_colors_file(self, path: Path) -> None:
        try:
            self.log_panel.log_colors.import_json(str(path))
            self.log_panel.refresh_view()
        except Exception as e:
            QMessageBox.critical(self, "Import Error", str(e))

    # ----- Actions -----
    def _new_window(self) -> None:
        argv = [sys.executable, "-m", "aegis.app"]
        try:
            subprocess.Popen(argv, shell=False)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _reset_layout(self) -> None:
        self.addDockWidget(Qt.BottomDockWidgetArea, self.log_panel)
        self.log_panel.show()
        self.log_panel.reset_size()

    def _echo_test(self) -> None:
        argv = [sys.executable, "-c", "print('Aegis OK')"]
        self._log("[echo] Starting…")
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

    def _show_help(self) -> None:
        readme = Path(__file__).resolve().parents[2] / "README.md"
        HelpDialog(readme, self).exec()

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

    def _log(self, message: str, level: str = "info") -> None:
        self.log_panel.log_message(message, level)

    # ----- Tasks -----
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

    def closeEvent(self, ev):  # type: ignore[override]
        settings.save_geometry(self.saveGeometry())
        settings.save_state(self.saveState())
        super().closeEvent(ev)
