from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from aegis.modules.commandlets import DEFAULT_COMMANDLETS


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

    def _col(label: str, le: QLineEdit, btn: QPushButton) -> QVBoxLayout:
        row = QHBoxLayout()
        row.addWidget(le)
        row.addWidget(btn)
        col = QVBoxLayout()
        col.addWidget(QLabel(label))
        col.addLayout(row)
        return col

    row = QHBoxLayout()
    row.addLayout(_col("UnrealEditor-Cmd.exe", exe_le, btn_exe))
    row.addLayout(_col("Project", proj_le, btn_proj))
    box = QGroupBox("Paths & Target")
    box.setLayout(row)
    return PathsGroup(box, exe_le, proj_le)


@dataclass
class ScopeGroup:
    box: QGroupBox
    cmdlet_cb: QComboBox
    add_btn: QPushButton
    packages_le: QLineEdit
    maps_le: QLineEdit
    collection_le: QLineEdit


def create_scope_group(add_cb: Callable[[], None]) -> ScopeGroup:
    cmdlet_cb = QComboBox()
    cmdlet_cb.addItems(DEFAULT_COMMANDLETS)
    cmdlet_cb.setObjectName("cmdlet_cb")
    add_btn = QPushButton("Add…")
    add_btn.clicked.connect(add_cb)
    row_cmd = QHBoxLayout()
    row_cmd.addWidget(cmdlet_cb)
    row_cmd.addWidget(add_btn)
    packages_le = QLineEdit()
    maps_le = QLineEdit()
    collection_le = QLineEdit()
    form = QFormLayout()
    form.addRow("Commandlet:", row_cmd)
    form.addRow("Packages/Paths (;)", packages_le)
    form.addRow("Maps (;)", maps_le)
    form.addRow("Collection", collection_le)
    box = QGroupBox("Commandlet & Scope")
    box.setLayout(form)
    return ScopeGroup(box, cmdlet_cb, add_btn, packages_le, maps_le, collection_le)


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
    cbs = (flag_unatt, flag_nop4, flag_nullrhi, flag_stdout, flag_utf8)
    for i, cb in enumerate(cbs):
        grid.addWidget(cb, i // 3, i % 3)
    row_extra = QHBoxLayout()
    row_extra.addWidget(QLabel("Extra Args"))
    row_extra.addWidget(extra_le)
    box = QGroupBox("Behavior Flags")
    lay = QVBoxLayout(box)
    lay.addLayout(grid)
    lay.addLayout(row_extra)
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
