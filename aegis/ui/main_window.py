"""Main application window coordinating panels and global actions."""

from __future__ import annotations

from pathlib import Path
import sys
import subprocess

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import (
    QAction,
    QDesktopServices,
    QGuiApplication,
    QResizeEvent,
)
from PySide6.QtWidgets import (
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStatusBar,
)

from aegis.core.settings import settings
from aegis.core.preferences import preferences
from aegis.core.task_runner import TaskRunner
from aegis.core.metadata import FEEDBACK_EMAIL, REPO_URL
from aegis.ui.init_tabs import init_tabs
from aegis.ui.key_binding_actions import KeyBindingActions
from aegis.ui.log_color_actions import LogColorActions
from aegis.ui.profile_actions import ProfileActions
from aegis.ui.theme_actions import ThemeActions
from aegis.ui.widgets.feedback_dialog import FeedbackDialog
from aegis.ui.widgets.help_dialog import HelpDialog
from aegis.ui.widgets.log_panel import LogPanel
from aegis.ui.menu_builder import build_menu
from aegis.ui.layout_persistence import (
    clamp_rect_to_available,
    restore_window_geometry,
    save_window_geometry,
)


class MainWindow(
    QMainWindow, KeyBindingActions, ProfileActions, ThemeActions, LogColorActions
):
    def __init__(self) -> None:
        super().__init__()
        self.prefs = preferences
        self.setWindowTitle("Aegis Toolbelt")
        if self.prefs.allow_resizing:
            self.resize(self.prefs.width, self.prefs.height)
        else:
            self.setFixedSize(self.prefs.width, self.prefs.height)

        # Runner
        self.runner = TaskRunner()
        self.runner.started.connect(self._task_started)
        self.runner.finished.connect(lambda _code: self._task_finished())

        self._batch_active = False

        tabs = init_tabs(self.runner, self._log)
        self.tabs = tabs.tabs
        self.env_doc = tabs.env_doc
        self.batch_panel = tabs.batch_panel
        self.command_editor = tabs.command_editor
        self.build_tabs = tabs.build_tabs
        self.uaft_panel = tabs.uaft_panel
        self.pak_panel = tabs.pak_panel
        self.commandlet_runner = tabs.commandlet_runner
        self.info_bar = tabs.info_bar
        self.setCentralWidget(tabs.central)

        self.batch_panel.batch_started.connect(self._batch_started)
        self.batch_panel.batch_progress.connect(self._batch_progress)
        self.batch_panel.batch_finished.connect(self._batch_finished)

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
        self.log_panel = LogPanel(self, dockable=self.prefs.allow_docking)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.log_panel)

        self.profile = None
        self.actions: dict[str, QAction] = build_menu(self)
        self._apply_key_bindings()
        restore_window_geometry(self, settings.s, key_prefix="ui")
        self._apply_saved_theme()
        self._load_last_profile()
        QGuiApplication.styleHints().colorSchemeChanged.connect(
            self._on_system_theme_change
        )
        if self.windowHandle():
            self.windowHandle().screenChanged.connect(
                lambda _: self.setGeometry(
                    clamp_rect_to_available(self.frameGeometry(), self)
                )
            )

    def resizeEvent(self, event: QResizeEvent) -> None:  # type: ignore[override]
        """Ensure log panel width tracks window size."""
        super().resizeEvent(event)
        self.log_panel.reset_size()

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
            QDesktopServices.openUrl(QUrl(f"mailto:{FEEDBACK_EMAIL}?{query}"))

    def _show_about(self) -> None:
        version = self._get_version()
        info = (
            f"<b>Aegis Toolbelt</b><br>Version: {version}<br>"
            "Author: Rahul Gupta<br>"
            f"Repository: <a href='{REPO_URL}'>{REPO_URL}</a><br>"
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
        if self.prefs.allow_resizing and not self.isMaximized():
            self.prefs.width = self.width()
            self.prefs.height = self.height()
        self.prefs.save()
        save_window_geometry(self, settings.s, key_prefix="ui")
        super().closeEvent(ev)

    def _toggle_docking(self, checked: bool) -> None:
        self.prefs.allow_docking = checked
        self.log_panel.set_dockable(checked)
        self.prefs.save()

    def _toggle_resizing(self, checked: bool) -> None:
        self.prefs.allow_resizing = checked
        if checked:
            self.setMinimumSize(0, 0)
            self.setMaximumSize(16777215, 16777215)
            self.resize(self.prefs.width, self.prefs.height)
        else:
            self.prefs.width = self.width()
            self.prefs.height = self.height()
            self.setFixedSize(self.width(), self.height())
        self.prefs.save()

    def _toggle_maximized(self, checked: bool) -> None:
        self.prefs.launch_maximized = checked
        if checked:
            self.showMaximized()
        else:
            self.showNormal()
            if self.prefs.allow_resizing:
                self.resize(self.prefs.width, self.prefs.height)
        self.prefs.save()
