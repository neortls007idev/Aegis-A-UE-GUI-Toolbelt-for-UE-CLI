from PySide6.QtCore import QByteArray, QSettings

ORG = "Aegis"
APP = "AegisToolbelt"


class Settings:
    def __init__(self) -> None:
        self.s = QSettings(ORG, APP)

    # theme
    def theme_mode(self) -> str:
        """Return the stored theme mode (system, light, dark, custom)."""
        return self.s.value("appearance/theme_mode", "system", type=str)

    def set_theme_mode(self, mode: str) -> None:
        self.s.setValue("appearance/theme_mode", mode)

    def custom_theme_path(self) -> str | None:
        return self.s.value("appearance/custom_theme_path", None, type=str)

    def set_custom_theme_path(self, path: str | None) -> None:
        if path is None:
            self.s.remove("appearance/custom_theme_path")
        else:
            self.s.setValue("appearance/custom_theme_path", path)

    # geometry & layout
    def save_geometry(self, data: QByteArray) -> None:
        self.s.setValue("ui/geometry", data)

    def load_geometry(self) -> QByteArray | None:
        v = self.s.value("ui/geometry", None)
        return QByteArray(v) if v is not None else None

    def save_state(self, data: QByteArray) -> None:
        self.s.setValue("ui/state", data)

    def load_state(self) -> QByteArray | None:
        v = self.s.value("ui/state", None)
        return QByteArray(v) if v is not None else None


settings = Settings()