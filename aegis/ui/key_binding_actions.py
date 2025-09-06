from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QMessageBox

from aegis.core.settings import settings
from aegis.ui.widgets.key_bindings_editor import KeyBindingsEditor


class KeyBindingActions:
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
