"""Helpers to build the main window tab layout."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtWidgets import QTabWidget, QTextEdit, QVBoxLayout, QWidget

from aegis.core.task_runner import TaskRunner
from aegis.ui.widgets.batch_builder_panel import BatchBuilderPanel
from aegis.ui.widgets.command_editor import CommandEditor
from aegis.ui.widgets.env_doc import EnvDocPanel
from aegis.ui.widgets.profile_info_bar import ProfileInfoBar
from aegis.ui.widgets.uaft_panel import UaftPanel
from aegis.ui.widgets.pak_iostore_panel import PakIoStorePanel


@dataclass
class TabSetup:
    central: QWidget
    tabs: QTabWidget
    info_bar: ProfileInfoBar
    env_doc: EnvDocPanel
    batch_panel: BatchBuilderPanel
    command_editor: CommandEditor
    build_tabs: QTabWidget
    uaft_panel: UaftPanel


def init_tabs(runner: TaskRunner, log_cb: Callable[[str, str], None]) -> TabSetup:
    """Create the main tab widget and its child panels."""

    tabs = QTabWidget()

    env_doc = EnvDocPanel(runner, log_cb)
    env_container = QWidget()
    env_layout = QVBoxLayout(env_container)
    env_layout.addWidget(env_doc, 1)

    batch_panel = BatchBuilderPanel(runner, log_cb)
    command_editor = CommandEditor(batch_panel)
    build_tabs = QTabWidget()
    build_tabs.addTab(batch_panel, "Tasks")
    build_tabs.addTab(command_editor, "Edit Batch Commands")
    build_container = QWidget()
    build_layout = QVBoxLayout(build_container)
    build_layout.addWidget(build_tabs, 1)

    uaft_panel = UaftPanel(runner, log_cb)
    uaft_container = QWidget()
    uaft_layout = QVBoxLayout(uaft_container)
    uaft_layout.addWidget(uaft_panel, 1)

    tabs.addTab(env_container, "EnvDoc")
    tabs.addTab(build_container, "Build")
    tabs.addTab(QTextEdit("Commandlets (stub)"), "Commandlets")
    tabs.addTab(PakIoStorePanel(), "Pak / IoStore")
    tabs.addTab(uaft_container, "Devices / UAFT")
    tabs.addTab(QTextEdit("Tests (stub)"), "Tests")
    tabs.addTab(QTextEdit("Trace Ops (stub)"), "Trace Ops")

    info_bar = ProfileInfoBar()
    central = QWidget()
    central_layout = QVBoxLayout(central)
    central_layout.addWidget(info_bar)
    central_layout.addWidget(tabs)

    return TabSetup(
        central=central,
        tabs=tabs,
        info_bar=info_bar,
        env_doc=env_doc,
        batch_panel=batch_panel,
        command_editor=command_editor,
        build_tabs=build_tabs,
        uaft_panel=uaft_panel,
    )
