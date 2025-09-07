"""Mixin that adds import/export actions for log colors."""

from __future__ import annotations

from pathlib import Path
from typing import cast

from PySide6.QtWidgets import QFileDialog, QMessageBox

from aegis.ui.widgets.log_colors_editor import LogColorsEditor
from aegis.ui.widgets.log_panel import LogPanel


class LogColorActions:
    """Actions for editing and persisting log color settings."""

    log_panel: LogPanel

    def _edit_log_colors(self) -> None:
        cfg = self.log_panel.log_colors.all()
        orig_levels = cast(dict[str, str], cfg["levels"])
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
