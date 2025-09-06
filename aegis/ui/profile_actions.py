from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QMessageBox

from aegis.core.profile import Profile
from aegis.core.settings import settings
from aegis.ui.widgets.profile_editor import ProfileEditor


class ProfileActions:
    profile: Profile | None

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
        if not self.profile:
            QMessageBox.information(self, "No Profile", "No profile to save.")
            return
        self._save_profile_as(settings.profile_path())

    def _save_profile_as(self, start_path: str | None = None) -> None:
        if not self.profile:
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
