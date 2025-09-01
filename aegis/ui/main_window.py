from PySide6.QtWidgets import (
    QMainWindow, QDockWidget, QWidget, QTabWidget, QTextEdit,
    QFileDialog, QMessageBox
)
from PySide6.QtGui import QAction            # <-- QAction is in QtGui in PySide6
from PySide6.QtCore import Qt

from aegis.core.settings import settings
from aegis.core.task_runner import TaskRunner
import sys


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
        self.log = QTextEdit(); self.log.setReadOnly(True)
        self.logDock = QDockWidget("Live Log"); self.logDock.setWidget(self.log)
        self.logDock.setObjectName("dock_live_log")
        self.addDockWidget(Qt.RightDockWidgetArea, self.logDock)

        # Dock: Artifacts
        self.artifacts = QTextEdit("Artifacts (stub)")
        self.artDock = QDockWidget("Artifacts"); self.artDock.setWidget(self.artifacts)
        self.artDock.setObjectName("dock_artifacts")
        self.addDockWidget(Qt.RightDockWidgetArea, self.artDock)
        self.tabifyDockWidget(self.logDock, self.artDock)
        self.logDock.raise_()

        # Dock: Command Preview
        self.preview = QTextEdit("Command Preview (stub)"); self.preview.setReadOnly(True)
        self.previewDock = QDockWidget("Command Preview"); self.previewDock.setWidget(self.preview)
        self.previewDock.setObjectName("dock_preview")
        self.addDockWidget(Qt.BottomDockWidgetArea, self.previewDock)

        self.runner = TaskRunner()
        self._build_menu()
        self._apply_saved_layout()
        self._apply_saved_theme()

    # ----- Menus -----
    def _build_menu(self):
        fileMenu = self.menuBar().addMenu("&File")
        actNew = QAction("New Window", self); actNew.setShortcut("Ctrl+Shift+N"); fileMenu.addAction(actNew)
        actNew.triggered.connect(self._new_window)
        actExit = QAction("Exit", self); fileMenu.addAction(actExit); actExit.triggered.connect(self.close)

        viewMenu = self.menuBar().addMenu("&View")
        actReset = QAction("Reset Layout", self); actReset.setShortcut("Ctrl+0"); viewMenu.addAction(actReset)
        actReset.triggered.connect(self._reset_layout)

        toolsMenu = self.menuBar().addMenu("&Tools")
        actEcho = QAction("Echo Test Command", self); toolsMenu.addAction(actEcho)
        actEcho.triggered.connect(self._echo_test)

        settingsMenu = self.menuBar().addMenu("&Settings")
        actTheme = QAction("Load Theme…", self); settingsMenu.addAction(actTheme)
        actTheme.triggered.connect(self._load_theme)

        helpMenu = self.menuBar().addMenu("&Help")
        actAbout = QAction("About", self); helpMenu.addAction(actAbout)
        actAbout.triggered.connect(lambda: QMessageBox.information(self, "About", "Aegis Toolbelt — GUI helper for UE CLIs (and beyond)."))

    # ----- Actions -----
    def _new_window(self):
        # launch a new process of this app
        import subprocess, sys, os
        argv = [sys.executable, "-m", "aegis.app"]
        try:
            subprocess.Popen(argv, shell=False)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _reset_layout(self):
        self.addDockWidget(Qt.RightDockWidgetArea, self.logDock)
        self.addDockWidget(Qt.RightDockWidgetArea, self.artDock)
        self.tabifyDockWidget(self.logDock, self.artDock)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.previewDock)
        self.logDock.raise_()

    def _echo_test(self):
        argv = [sys.executable, "-c", "print('Aegis OK')"]
        self.log.append("[echo] Starting…")
        try:
            self.runner.start(
                argv,
                on_stdout=lambda s: self.log.append(s),
                on_stderr=lambda s: self.log.append(f"<span style='color:#b00;'>{s}</span>"),
                on_exit=lambda code: self.log.append(f"[echo] Exit code: {code}")
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def _load_theme(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select .qss theme", "", "QSS (*.qss)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
                settings.set_theme_path(path)
            except Exception as e:
                QMessageBox.critical(self, "Theme Error", str(e))

    # ----- Persistence -----
    def _apply_saved_layout(self):
        g = settings.load_geometry()
        if g: self.restoreGeometry(g)
        s = settings.load_state()
        if s: self.restoreState(s)

    def _apply_saved_theme(self):
        path = settings.theme_path()
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
            except Exception:
                pass  # ignore if missing/moved

    def closeEvent(self, ev):
        settings.save_geometry(self.saveGeometry())
        settings.save_state(self.saveState())
        super().closeEvent(ev)
