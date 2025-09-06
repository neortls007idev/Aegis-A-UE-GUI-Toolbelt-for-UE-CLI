from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QFileDialog, QMessageBox

from aegis.core.settings import settings


LAYOUT_VERSION = 4


class ThemeActions:
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

    def _load_theme_file(self, path: Path) -> None:
        try:
            settings.set_theme_mode("custom")
            settings.set_custom_theme_path(str(path))
            self._apply_theme()
        except Exception as e:
            QMessageBox.critical(self, "Theme Error", str(e))

    def _apply_saved_layout(self) -> None:
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

    def _apply_saved_theme(self) -> None:
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
