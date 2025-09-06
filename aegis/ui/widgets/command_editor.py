from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem

from .batch_builder_panel import BatchBuilderPanel


class CommandEditor(QTableWidget):
    def __init__(self, batch_panel: BatchBuilderPanel) -> None:
        super().__init__(0, 3)
        self.batch_panel = batch_panel
        self.setHorizontalHeaderLabels(["#", "", "Command"])
        self.horizontalHeader().setStretchLastSection(True)
        self.setColumnWidth(0, 32)
        self.setColumnWidth(1, 24)
        self.setShowGrid(False)
        self.itemChanged.connect(self._on_item_changed)
        self.batch_panel.tasks_changed.connect(self.refresh)
        self.refresh()

    def refresh(self) -> None:
        cmds = self.batch_panel.all_command_previews()
        self.blockSignals(True)
        self.setRowCount(len(cmds))
        for i, cmd in enumerate(cmds):
            num_item = QTableWidgetItem(str(i + 1))
            num_item.setFlags(Qt.ItemIsEnabled)
            num_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            icon_text = "✎" if self.batch_panel.task_is_editable(i) else "🔒"
            icon_item = QTableWidgetItem(icon_text)
            icon_item.setFlags(Qt.ItemIsEnabled)
            icon_item.setTextAlignment(Qt.AlignCenter)

            cmd_item = QTableWidgetItem(cmd)
            if self.batch_panel.task_is_editable(i):
                cmd_item.setFlags(
                    Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
                )
            else:
                cmd_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                cmd_item.setForeground(Qt.gray)

            self.setItem(i, 0, num_item)
            self.setItem(i, 1, icon_item)
            self.setItem(i, 2, cmd_item)
        self.blockSignals(False)

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        if item.column() != 2:
            return
        row = item.row()
        cmd = item.text().strip()
        if self.batch_panel.task_is_editable(row):
            self.batch_panel.set_command_override(row, cmd, emit=False)
        else:
            self.blockSignals(True)
            item.setText(self.batch_panel.command_preview(row))
            self.blockSignals(False)
        self.batch_panel.tasks_changed.emit()
