from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

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
    exe_le: QLineEdit
    proj_le: QLineEdit


def create_paths_group(browse_cb: Callable[[QLineEdit, bool], None]) -> PathsGroup:
    exe_le = QLineEdit()
    exe_le.setObjectName("exe_le")
    proj_le = QLineEdit()
    proj_le.setObjectName("uproject_le")
    btn_exe = QPushButton("Browse…")
    btn_exe.clicked.connect(lambda: browse_cb(exe_le, False))
    btn_proj = QPushButton("Browse…")
    btn_proj.clicked.connect(lambda: browse_cb(proj_le, True))
    grid = QGridLayout()
    grid.addWidget(QLabel("UnrealEditor-Cmd.exe:"), 0, 0)
    grid.addWidget(exe_le, 0, 1)
    grid.addWidget(btn_exe, 0, 2)
    grid.addWidget(QLabel("Project:"), 0, 3)
    grid.addWidget(proj_le, 0, 4)
    grid.addWidget(btn_proj, 0, 5)
    box = QGroupBox("Paths & Target")
    box.setLayout(grid)
    return PathsGroup(box, exe_le, proj_le)


@dataclass
class ScopeGroup:
    box: QGroupBox
    cmdlet_cb: QComboBox
    add_btn: QPushButton
    edit_btn: QPushButton
    remove_btn: QPushButton
    packages_le: QLineEdit
    maps_le: QLineEdit
    collection_le: QLineEdit


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
    packages_le = QLineEdit()
    maps_le = QLineEdit()
    collection_le = QLineEdit()
    form = QFormLayout()
    form.addRow("Commandlet:", row_cmdlet)
    form.addRow("Packages/Paths (;)", packages_le)
    form.addRow("Maps (;)", maps_le)
    form.addRow("Collection", collection_le)
    box = QGroupBox("Commandlet & Scope")
    box.setLayout(form)
    return ScopeGroup(
        box,
        cmdlet_cb,
        add_btn,
        edit_btn,
        remove_btn,
        packages_le,
        maps_le,
        collection_le,
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
    flag_unatt.setChecked(True)
    flag_nop4 = QCheckBox("-nop4")
    flag_nop4.setChecked(True)
    flag_nullrhi = QCheckBox("-NullRHI")
    flag_stdout = QCheckBox("-stdout")
    flag_stdout.setChecked(True)
    flag_utf8 = QCheckBox("-UTF8Output")
    flag_utf8.setChecked(True)
    extra_le = QLineEdit()
    grid = QGridLayout()
    grid.setHorizontalSpacing(5)
    grid.setVerticalSpacing(5)
    grid.addWidget(flag_unatt, 0, 0)
    grid.addWidget(flag_nop4, 0, 1)
    grid.addWidget(flag_nullrhi, 0, 2)
    grid.addWidget(flag_stdout, 1, 0)
    grid.addWidget(flag_utf8, 1, 1)
    grid.addWidget(QLabel("Extra Args"), 2, 0)
    grid.addWidget(extra_le, 2, 1, 1, 2)
    box = QGroupBox("Behavior Flags")
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
    preview_le.setReadOnly(True)
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
