"""Panel for running Unreal commandlets with previews and recipes."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QFileDialog, QInputDialog, QLineEdit, QVBoxLayout, QWidget

from aegis.core.profile import Profile
from aegis.core.task_runner import TaskRunner
from aegis.modules.commandlets import (
    CommandletFlags,
    CommandletRecipe,
    build_argv,
    load_recipe,
    preview_command,
    recipes_dir,
    save_recipe,
)
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

        self.paths: crg.PathsGroup = crg.create_paths_group(self._browse)
        self.scope: crg.ScopeGroup = crg.create_scope_group()
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
            self.paths.exe_le,
            self.paths.proj_le,
            self.scope.cmdlet_cb,
            self.scope.packages_le,
            self.scope.maps_le,
            self.scope.collection_le,
            self.flags.flag_unatt,
            self.flags.flag_nop4,
            self.flags.flag_nullrhi,
            self.flags.flag_stdout,
            self.flags.flag_utf8,
            self.flags.extra_le,
            self.recipes.save_btn,
            self.recipes.load_btn,
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

    def _browse(self, le: QLineEdit, uproject: bool = False) -> None:
        if uproject:
            path, _ = QFileDialog.getOpenFileName(
                self, "Choose .uproject", str(Path.cwd()), "*.uproject"
            )
        else:
            path, _ = QFileDialog.getOpenFileName(
                self, "Choose UnrealEditor-Cmd.exe", str(Path.cwd())
            )
        if path:
            le.setText(path)
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
        argv = build_argv(
            Path(self.paths.exe_le.text()),
            Path(self.paths.proj_le.text()),
            self._recipe(),
        )
        self.controls.preview_le.setText(preview_command(argv))
        return argv

    def _dry_run(self) -> None:
        self._build()

    def _run(self) -> None:
        argv = self._build()
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
        if not self.paths.proj_le.text():
            return
        name, ok = QInputDialog.getText(
            self, "Recipe Name", "Filename (without .json):"
        )
        if ok and name:
            save_recipe(Path(self.paths.proj_le.text()), name, self._recipe())

    def _apply_recipe(self, r: CommandletRecipe) -> None:
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
        if not self.paths.proj_le.text():
            return
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Recipe",
            str(recipes_dir(Path(self.paths.proj_le.text()))),
            "*.json",
        )
        if path:
            self._apply_recipe(load_recipe(Path(path)))
            self._dry_run()

    def update_profile(self, profile: Profile | None) -> None:
        self.profile = profile
        if profile:
            exe = profile.engine_root / "Engine/Binaries/Win64/UnrealEditor-Cmd.exe"
            self.paths.exe_le.setText(str(exe))
            for p in profile.project_dir.glob("*.uproject"):
                self.paths.proj_le.setText(str(p))
                break
            self._dry_run()
