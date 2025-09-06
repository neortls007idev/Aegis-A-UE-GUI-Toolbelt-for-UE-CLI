import pytest

pytest.importorskip("PySide6")

from PySide6.QtWidgets import QApplication, QTableWidgetItem

from aegis.ui.widgets.uat_override_widget import UatOverrideWidget


def ensure_app() -> None:
    if QApplication.instance() is None:
        QApplication([])


def test_manual_args_round_trip() -> None:
    ensure_app()
    widget = UatOverrideWidget()
    widget.table.insertRow(0)
    widget.table.setItem(0, 0, QTableWidgetItem("cook"))
    widget.table.setItem(0, 1, QTableWidgetItem("Dir"))
    assert widget.manual_args() == ["-cook=Dir"]


def test_manual_args_inline_value() -> None:
    ensure_app()
    widget = UatOverrideWidget()
    widget.table.insertRow(0)
    widget.table.setItem(0, 0, QTableWidgetItem("cook=Dir"))
    assert widget.manual_args() == ["-cook=Dir"]
