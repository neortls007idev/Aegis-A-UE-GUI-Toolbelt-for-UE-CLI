"""Widget for editing BuildCookRun overrides for UAT."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QDialog,
)

from aegis.ui.widgets.manual_override_dialog import (
    ManualOverrideDialog,
    BUILD_COOK_RUN_SWITCHES,
)


class UatOverrideWidget(QGroupBox):
    """Table and controls for configuring UAT BuildCookRun switches."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("UAT (BuildCookRun)", parent)
        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 2)
        self.table.setObjectName("uat_override_table")
        self.table.setHorizontalHeaderLabels(["Switch", "Value"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        row = QHBoxLayout()
        self.add_btn = QPushButton("Add…")
        self.add_btn.setObjectName("add_override_btn")
        self.add_btn.clicked.connect(self._add_override)
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.setObjectName("remove_override_btn")
        self.remove_btn.clicked.connect(self._remove_override)
        row.addWidget(self.add_btn)
        row.addWidget(self.remove_btn)
        layout.addLayout(row)

    def clear(self) -> None:
        """Remove all overrides."""
        self.table.setRowCount(0)

    def _add_override(self) -> None:
        dialog = ManualOverrideDialog(self)
        if dialog.exec() != QDialog.Accepted:
            return
        for switch, value in dialog.selected_overrides():
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(switch))
            self.table.setItem(row, 1, QTableWidgetItem(value))
            hint = BUILD_COOK_RUN_SWITCHES.get(switch, "")
            self.table.item(row, 0).setToolTip(hint)
            self.table.item(row, 1).setToolTip(hint)

    def _remove_override(self) -> None:
        row = self.table.currentRow()
        if row != -1:
            self.table.removeRow(row)

    def manual_args(self) -> list[str]:
        """Serialize overrides into CLI arguments."""
        args: list[str] = []
        for row in range(self.table.rowCount()):
            key_item = self.table.item(row, 0)
            if not key_item:
                continue
            switch_text = key_item.text().strip()
            if not switch_text:
                continue
            inline_value = ""
            if "=" in switch_text:
                switch_part, inline_value = switch_text.split("=", 1)
            else:
                switch_part = switch_text
            switch = "-" + switch_part.lstrip("-")
            val_item = self.table.item(row, 1)
            value = val_item.text().strip() if val_item else ""
            if not value:
                value = inline_value.strip()
            if value:
                args.append(f"{switch}={value}")
            else:
                args.append(switch)
        return args
