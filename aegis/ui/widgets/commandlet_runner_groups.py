from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)


@dataclass
class PathsGroup:
    box: QGroupBox
    exe_lbl: QLabel
    rebuild_btn: QPushButton


def create_paths_group() -> PathsGroup:
    exe_lbl = QLabel("(no profile)")
    exe_lbl.setObjectName("editor_cmd_lbl")
    exe_lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
    rebuild_btn = QPushButton("Rebuild & Fix")
    rebuild_btn.setObjectName("rebuild_editor_btn")
    row = QHBoxLayout()
    row.setContentsMargins(2, 2, 2, 2)
    row.setSpacing(2)
    row.addWidget(QLabel("UnrealEditor-Cmd.exe:"))
    row.addWidget(exe_lbl, 1)
    row.addWidget(rebuild_btn)
    box = QGroupBox("Paths & Target")
    box.setObjectName("paths_target_box")
    box.setLayout(row)
    return PathsGroup(box, exe_lbl, rebuild_btn)


@dataclass
class ScopeGroup:
    box: QGroupBox
    cmdlet_cb: QComboBox
    add_btn: QPushButton
    edit_btn: QPushButton
    remove_btn: QPushButton
    project_le: QLineEdit
    project_browse_btn: QPushButton
    packages_le: QLineEdit
    packages_browse_btn: QPushButton
    maps_le: QLineEdit
    maps_browse_btn: QPushButton
    collection_le: QLineEdit
    collection_browse_btn: QPushButton


def create_scope_group(commandlets: list[str]) -> ScopeGroup:
    cmdlet_cb = QComboBox()
    cmdlet_cb.addItems(commandlets)
    cmdlet_cb.setObjectName("cmdlet_cb")
    add_btn = QPushButton("Add")
    add_btn.setObjectName("add_cmdlet_btn")
    edit_btn = QPushButton("Edit")
    edit_btn.setObjectName("edit_cmdlet_btn")
    remove_btn = QPushButton("Remove")
    remove_btn.setObjectName("remove_cmdlet_btn")
    row_cmdlet = QHBoxLayout()
    row_cmdlet.addWidget(cmdlet_cb)
    row_cmdlet.addWidget(add_btn)
    row_cmdlet.addWidget(edit_btn)
    row_cmdlet.addWidget(remove_btn)
    project_le = QLineEdit()
    project_browse = QPushButton("Browse")
    row_project = QHBoxLayout()
    row_project.addWidget(project_le, 1)
    row_project.addWidget(project_browse)
    packages_le = QLineEdit()
    packages_browse = QPushButton("Browse")
    row_packages = QHBoxLayout()
    row_packages.addWidget(packages_le, 1)
    row_packages.addWidget(packages_browse)
    maps_le = QLineEdit()
    maps_browse = QPushButton("Browse")
    row_maps = QHBoxLayout()
    row_maps.addWidget(maps_le, 1)
    row_maps.addWidget(maps_browse)
    collection_le = QLineEdit()
    collection_browse = QPushButton("Browse")
    row_collection = QHBoxLayout()
    row_collection.addWidget(collection_le, 1)
    row_collection.addWidget(collection_browse)
    form = QFormLayout()
    form.addRow("Commandlet:", row_cmdlet)
    form.addRow("Project", row_project)
    form.addRow("Packages/Paths (;)", row_packages)
    form.addRow("Maps (;)", row_maps)
    form.addRow("Collection", row_collection)
    box = QGroupBox("Commandlet & Scope")
    box.setLayout(form)
    return ScopeGroup(
        box,
        cmdlet_cb,
        add_btn,
        edit_btn,
        remove_btn,
        project_le,
        project_browse,
        packages_le,
        packages_browse,
        maps_le,
        maps_browse,
        collection_le,
        collection_browse,
    )


@dataclass
class FlagsGroup:
    box: QGroupBox
    flag_unatt: QCheckBox
    flag_nop4: QCheckBox
    flag_nullrhi: QCheckBox
    flag_stdout: QCheckBox
    flag_utf8: QCheckBox
    extra_le: QLineEdit


def create_flags_group() -> FlagsGroup:
    flag_unatt = QCheckBox("-unattended")
    flag_unatt.setObjectName("unattended_chk")
    flag_unatt.setChecked(True)
    flag_nop4 = QCheckBox("-nop4")
    flag_nop4.setObjectName("nop4_chk")
    flag_nop4.setChecked(True)
    flag_nullrhi = QCheckBox("-NullRHI")
    flag_nullrhi.setObjectName("nullrhi_chk")
    flag_stdout = QCheckBox("-stdout")
    flag_stdout.setObjectName("stdout_chk")
    flag_stdout.setChecked(True)
    flag_utf8 = QCheckBox("-UTF8Output")
    flag_utf8.setObjectName("utf8_chk")
    flag_utf8.setChecked(True)
    extra_le = QLineEdit()
    extra_le.setObjectName("extra_flags_le")
    grid = QGridLayout()
    grid.setContentsMargins(2, 2, 2, 2)
    grid.setHorizontalSpacing(2)
    grid.setVerticalSpacing(2)
    grid.addWidget(flag_unatt, 0, 0)
    grid.addWidget(flag_nop4, 0, 1)
    grid.addWidget(flag_nullrhi, 0, 2)
    grid.addWidget(flag_stdout, 0, 3)
    grid.addWidget(flag_utf8, 0, 4)
    grid.addWidget(QLabel("Extra Args"), 1, 0)
    grid.addWidget(extra_le, 1, 1, 1, 4)
    box = QGroupBox("Behavior Flags")
    box.setObjectName("behavior_flags_box")
    box.setLayout(grid)
    return FlagsGroup(
        box,
        flag_unatt,
        flag_nop4,
        flag_nullrhi,
        flag_stdout,
        flag_utf8,
        extra_le,
    )


@dataclass
class RunControls:
    box: QGroupBox
    preview_le: QLineEdit
    dry_run_btn: QPushButton
    run_btn: QPushButton
    stop_btn: QPushButton


def create_run_controls(
    copy_cb: Callable[[], None],
    dry_cb: Callable[[], None],
    run_cb: Callable[[], None],
    stop_cb: Callable[[], None],
) -> RunControls:
    preview_le = QLineEdit()
    preview_le.setObjectName("preview_le")
    btn_copy = QPushButton("Copy")
    btn_copy.clicked.connect(copy_cb)
    dry_btn = QPushButton("Dry Run")
    dry_btn.clicked.connect(dry_cb)
    run_btn = QPushButton("Run")
    run_btn.clicked.connect(run_cb)
    stop_btn = QPushButton("Stop")
    stop_btn.clicked.connect(stop_cb)
    stop_btn.setEnabled(False)
    row_prev = QHBoxLayout()
    row_prev.addWidget(preview_le, 1)
    row_prev.addWidget(btn_copy)
    row_run = QHBoxLayout()
    row_run.addWidget(dry_btn)
    row_run.addWidget(run_btn)
    row_run.addWidget(stop_btn)
    box = QGroupBox("Run Controls")
    lay = QVBoxLayout(box)
    lay.addLayout(row_prev)
    lay.addLayout(row_run)
    return RunControls(box, preview_le, dry_btn, run_btn, stop_btn)


@dataclass
class RecipeGroup:
    box: QGroupBox
    save_btn: QPushButton
    load_btn: QPushButton


def create_recipe_group(
    save_cb: Callable[[], None],
    load_cb: Callable[[], None],
) -> RecipeGroup:
    save_btn = QPushButton("Save Recipe…")
    save_btn.clicked.connect(save_cb)
    load_btn = QPushButton("Load Recipe…")
    load_btn.clicked.connect(load_cb)
    row = QHBoxLayout()
    row.addWidget(save_btn)
    row.addWidget(load_btn)
    box = QGroupBox("Recipes")
    lay = QVBoxLayout(box)
    lay.addLayout(row)
    return RecipeGroup(box, save_btn, load_btn)
