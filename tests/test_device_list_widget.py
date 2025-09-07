import pytest

pytest.importorskip("PySide6")

from aegis.core.task_runner import TaskRunner
from aegis.ui.widgets.device_list_widget import DeviceListWidget
from PySide6.QtWidgets import QTableWidgetItem


def _noop_log(_msg: str, _level: str) -> None:
    pass


def test_selected_devices(qtbot) -> None:
    widget = DeviceListWidget(TaskRunner(), _noop_log)
    qtbot.addWidget(widget)
    widget.table.setRowCount(2)
    widget.table.setItem(0, 0, QTableWidgetItem("A"))
    widget.table.setItem(0, 1, QTableWidgetItem("B"))
    widget.table.setItem(0, 2, QTableWidgetItem("serial1"))
    widget.table.setItem(1, 0, QTableWidgetItem("C"))
    widget.table.setItem(1, 1, QTableWidgetItem("D"))
    widget.table.setItem(1, 2, QTableWidgetItem("serial2"))
    widget.table.selectRow(0)
    assert widget.selected_devices() == ["serial1"]
