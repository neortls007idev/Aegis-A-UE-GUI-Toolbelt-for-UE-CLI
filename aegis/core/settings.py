from PySide6.QtCore import QSettings, QByteArray

ORG = "Aegis"
APP = "AegisToolbelt"

class Settings:
    def __init__(self):
        self.s = QSettings(ORG, APP)

    # theme
    def theme_path(self) -> str | None:
        return self.s.value("appearance/theme_path", None, type=str)

    def set_theme_path(self, path: str | None):
        if path is None:
            self.s.remove("appearance/theme_path")
        else:
            self.s.setValue("appearance/theme_path", path)

    # geometry & layout
    def save_geometry(self, data: QByteArray):
        self.s.setValue("ui/geometry", data)

    def load_geometry(self) -> QByteArray | None:
        v = self.s.value("ui/geometry", None)
        return QByteArray(v) if v is not None else None

    def save_state(self, data: QByteArray):
        self.s.setValue("ui/state", data)

    def load_state(self) -> QByteArray | None:
        v = self.s.value("ui/state", None)
        return QByteArray(v) if v is not None else None

settings = Settings()
