"""Panel for running Unreal commandlets with previews and recipes."""

from __future__ import annotations

from pathlib import Path
from typing import Callable
import shlex
import sys

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QFileDialog, QInputDialog, QVBoxLayout, QWidget

from aegis.core.profile import Profile
from aegis.core.task_runner import TaskRunner
from aegis.modules.commandlets import (
    DEFAULT_COMMANDLETS,
    CommandletFlags,
    CommandletRecipe,
    build_argv,
    load_commandlets,
    load_recipe,
    preview_command,
    recipes_dir,
    save_commandlets,
    save_recipe,
)
from aegis.modules.ubt import Ubt
from . import commandlet_runner_groups as crg


class CommandletRunnerWidget(QWidget):
    def __init__(
        self,
        runner: TaskRunner,
        log_cb: Callable[[str, str], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.runner = runner
        self.log = log_cb
        self.profile: Profile | None = None
        self.exe_path: Path | None = None
        self.uproject: Path | None = None

        self.paths: crg.PathsGroup = crg.create_paths_group()
        self.paths.rebuild_btn.clicked.connect(self._rebuild_editor)
        self.scope: crg.ScopeGroup = crg.create_scope_group(load_commandlets(None))
        self.scope.add_btn.clicked.connect(self._add_cmdlet)
        self.scope.edit_btn.clicked.connect(self._edit_cmdlet)
        self.scope.remove_btn.clicked.connect(self._remove_cmdlet)
        self.flags: crg.FlagsGroup = crg.create_flags_group()
        self.controls: crg.RunControls = crg.create_run_controls(
            lambda: QGuiApplication.clipboard().setText(
                self.controls.preview_le.text()
            ),
            self._dry_run,
            self._run,
            self.runner.cancel,
        )
        self.recipes: crg.RecipeGroup = crg.create_recipe_group(
            self._save_recipe, self._load_recipe
        )

        self.inputs = [
            self.scope.cmdlet_cb,
            self.scope.packages_le,
            self.scope.maps_le,
            self.scope.collection_le,
            self.scope.add_btn,
            self.scope.edit_btn,
            self.scope.remove_btn,
            self.flags.flag_unatt,
            self.flags.flag_nop4,
            self.flags.flag_nullrhi,
            self.flags.flag_stdout,
            self.flags.flag_utf8,
            self.flags.extra_le,
            self.recipes.save_btn,
            self.recipes.load_btn,
            self.controls.preview_le,
            self.controls.dry_run_btn,
            self.controls.run_btn,
        ]

        root = QVBoxLayout(self)
        for box in (
            self.paths.box,
            self.scope.box,
            self.flags.box,
            self.controls.box,
            self.recipes.box,
        ):
            root.addWidget(box)

    def _load_cmdlets(self) -> None:
        proj = self.uproject
        cmdlets = load_commandlets(proj) if proj else load_commandlets(None)
        current = self.scope.cmdlet_cb.currentText()
        self.scope.cmdlet_cb.clear()
        self.scope.cmdlet_cb.addItems(cmdlets)
        if current in cmdlets:
            self.scope.cmdlet_cb.setCurrentText(current)

    def _add_cmdlet(self) -> None:
        name, ok = QInputDialog.getText(self, "Add Commandlet", "Commandlet name:")
        if ok and name:
            if self.scope.cmdlet_cb.findText(name) == -1:
                self.scope.cmdlet_cb.addItem(name)
            self.scope.cmdlet_cb.setCurrentText(name)
            proj = self.uproject
            if proj:
                cmds = [
                    self.scope.cmdlet_cb.itemText(i)
                    for i in range(self.scope.cmdlet_cb.count())
                ]
                save_commandlets(proj, cmds)
            self._dry_run()

    def _edit_cmdlet(self) -> None:
        current = self.scope.cmdlet_cb.currentText()
        if current in DEFAULT_COMMANDLETS:
            return
        name, ok = QInputDialog.getText(
            self, "Edit Commandlet", "Commandlet name:", text=current
        )
        if ok and name and name != current:
            idx = self.scope.cmdlet_cb.currentIndex()
            self.scope.cmdlet_cb.setItemText(idx, name)
            proj = self.uproject
            if proj:
                cmds = [
                    self.scope.cmdlet_cb.itemText(i)
                    for i in range(self.scope.cmdlet_cb.count())
                ]
                save_commandlets(proj, cmds)
            self._dry_run()

    def _remove_cmdlet(self) -> None:
        current = self.scope.cmdlet_cb.currentText()
        if current in DEFAULT_COMMANDLETS:
            return
        idx = self.scope.cmdlet_cb.currentIndex()
        self.scope.cmdlet_cb.removeItem(idx)
        proj = self.uproject
        if proj:
            cmds = [
                self.scope.cmdlet_cb.itemText(i)
                for i in range(self.scope.cmdlet_cb.count())
            ]
            save_commandlets(proj, cmds)
        self._dry_run()

    def _recipe(self) -> CommandletRecipe:
        flags = CommandletFlags(
            unattended=self.flags.flag_unatt.isChecked(),
            nop4=self.flags.flag_nop4.isChecked(),
            nullrhi=self.flags.flag_nullrhi.isChecked(),
            stdout=self.flags.flag_stdout.isChecked(),
            utf8=self.flags.flag_utf8.isChecked(),
        )
        return CommandletRecipe(
            commandlet=self.scope.cmdlet_cb.currentText(),
            packages=[p for p in self.scope.packages_le.text().split(";") if p],
            maps=[m for m in self.scope.maps_le.text().split(";") if m],
            collection=self.scope.collection_le.text().strip(),
            extra_args=self.flags.extra_le.text().strip(),
            flags=flags,
        )

    def _build(self) -> list[str]:
        if not (self.exe_path and self.uproject):
            return []
        argv = build_argv(self.exe_path, self.uproject, self._recipe())
        self.controls.preview_le.setText(preview_command(argv))
        return argv

    def _dry_run(self) -> None:
        self._build()

    def _run(self) -> None:
        text = self.controls.preview_le.text().strip()
        argv = shlex.split(text) if text else self._build()
        if not argv:
            return
        self._toggle(True)

        def out(line: str) -> None:
            self.log(line, "info")

        def err(line: str) -> None:
            self.log(line, "error")

        def done(code: int) -> None:
            self.log(f"Commandlet exited {code}", "info")
            self._toggle(False)

        self.runner.start(argv, out, err, done)

    def _toggle(self, running: bool) -> None:
        for w in self.inputs:
            w.setEnabled(not running)
        self.controls.stop_btn.setEnabled(running)

    def _save_recipe(self) -> None:
        if not self.uproject:
            return
        name, ok = QInputDialog.getText(
            self, "Recipe Name", "Filename (without .json):"
        )
        if ok and name:
            save_recipe(self.uproject, name, self._recipe())

    def _apply_recipe(self, r: CommandletRecipe) -> None:
        if self.scope.cmdlet_cb.findText(r.commandlet) == -1:
            self.scope.cmdlet_cb.addItem(r.commandlet)
        self.scope.cmdlet_cb.setCurrentText(r.commandlet)
        for le, text in [
            (self.scope.packages_le, ";".join(r.packages)),
            (self.scope.maps_le, ";".join(r.maps)),
            (self.scope.collection_le, r.collection),
            (self.flags.extra_le, r.extra_args),
        ]:
            le.setText(text)
        for cb, state in [
            (self.flags.flag_unatt, r.flags.unattended),
            (self.flags.flag_nop4, r.flags.nop4),
            (self.flags.flag_nullrhi, r.flags.nullrhi),
            (self.flags.flag_stdout, r.flags.stdout),
            (self.flags.flag_utf8, r.flags.utf8),
        ]:
            cb.setChecked(state)

    def _load_recipe(self) -> None:
        if not self.uproject:
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Recipe",
            str(recipes_dir(self.uproject)),
            "*.json",
        )
        if path:
            self._apply_recipe(load_recipe(Path(path)))
            self._dry_run()

    def update_profile(self, profile: Profile | None) -> None:
        self.profile = profile
        if profile:
            exe = profile.engine_root / "Engine/Binaries/Win64/UnrealEditor-Cmd.exe"
            self.exe_path = exe
            self.paths.exe_lbl.setText(str(exe))
            for p in profile.project_dir.glob("*.uproject"):
                self.uproject = p
                break
            self._load_cmdlets()
            self._dry_run()
        else:
            self.paths.exe_lbl.setText("(no profile)")
            self.exe_path = None
            self.uproject = None

    def _rebuild_editor(self) -> None:
        if not self.profile:
            self.log("[ubt] No profile selected", "error")
            return
        ubt = Ubt(self.profile.engine_root, self.profile.project_dir)
        if sys.platform == "win32":
            platform = "Win64"
        elif sys.platform == "darwin":
            platform = "Mac"
        else:
            platform = "Linux"
        target, cfg = ubt.guess_target("DevelopmentEditor")
        argv = ubt.build_argv(target, platform, cfg, clean=True)
        self.log(f"[ubt] {' '.join(argv)}", "info")

        def done(code: int) -> None:
            self.log(f"[ubt] exit code {code}", "success" if code == 0 else "error")

        self.runner.start(
            argv,
            on_stdout=lambda s: self.log(f"[ubt] {s}", "info"),
            on_stderr=lambda s: self.log(f"[ubt] {s}", "error"),
            on_exit=done,
        )
