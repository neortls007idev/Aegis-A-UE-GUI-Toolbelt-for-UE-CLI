from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QBoxLayout,
    QComboBox,
    QDockWidget,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QMainWindow,
    QWidget,
)

from aegis.core.settings import settings


LOG_LABELS = {
    "info": "Information:",
    "error": "Error:",
    "warning": "Warning:",
    "success": "Success:",
}


class LogPanel(QDockWidget):
    def __init__(
        self, parent: QMainWindow | None = None, dockable: bool = True
    ) -> None:
        super().__init__("Live Log", parent)
        self.setObjectName("dock_live_log")
        self.log_colors = settings.log_colors

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.messages: list[tuple[str, str, str]] = []

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search…")
        self.search.textChanged.connect(self.refresh_view)

        self.filter = QComboBox()
        self.filter.addItems(["All", "Info", "Warning", "Error", "Success"])
        self.filter.currentTextChanged.connect(self.refresh_view)

        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear)

        container = QWidget()
        layout = QVBoxLayout(container)
        row = QHBoxLayout()
        row.addWidget(self.search, 1)
        row.addWidget(self.filter)
        row.addWidget(self.clear_btn)
        layout.addLayout(row)
        layout.addWidget(self.log)
        self.controls = row
        self.setWidget(container)

        self.set_dockable(dockable)
        self.topLevelChanged.connect(lambda _: self.reset_size())
        self.dockLocationChanged.connect(lambda _: self.reset_size())
        self.reset_size()
        self.show()

    def log_message(self, message: str, level: str = "info") -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self.messages.append((ts, message, level))
        if not self.isVisible():
            self.show()
        if self._matches_filters(message, level):
            color = self.log_colors.color_for(message, level)
            label = LOG_LABELS.get(level, f"{level.title()}:")
            self.log.append(
                f"<span style='color:{color};'>{ts} {label} {message}</span>"
            )

    def clear(self) -> None:
        self.log.clear()
        self.messages.clear()

    def _matches_filters(self, message: str, level: str) -> bool:
        level_filter = self.filter.currentText().lower()
        if level_filter != "all" and level != level_filter:
            return False
        query = self.search.text().lower()
        return query in message.lower()

    def refresh_view(self) -> None:
        self.log.clear()
        for ts, message, level in self.messages:
            if self._matches_filters(message, level):
                color = self.log_colors.color_for(message, level)
                label = LOG_LABELS.get(level, f"{level.title()}:")
                self.log.append(
                    f"<span style='color:{color};'>{ts} {label} {message}</span>"
                )

    def reset_size(self) -> None:
        main = self.parentWidget()
        if not isinstance(main, QMainWindow):
            return
        self.setMinimumSize(0, 0)
        self.widget().setMinimumSize(0, 0)
        area = main.dockWidgetArea(self)
        if area in (Qt.LeftDockWidgetArea, Qt.RightDockWidgetArea):
            self.controls.setDirection(QBoxLayout.TopToBottom)
        else:
            self.controls.setDirection(QBoxLayout.LeftToRight)

    def set_dockable(self, dockable: bool) -> None:
        if dockable:
            self.setFeatures(
                QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable
            )
            self.setAllowedAreas(
                Qt.BottomDockWidgetArea
                | Qt.TopDockWidgetArea
                | Qt.LeftDockWidgetArea
                | Qt.RightDockWidgetArea
            )
        else:
            self.setFeatures(QDockWidget.NoDockWidgetFeatures)
            self.setAllowedAreas(Qt.NoDockWidgetArea)
