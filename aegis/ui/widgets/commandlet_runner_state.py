from __future__ import annotations

from .commandlet_runner_groups import FlagsGroup, ScopeGroup
from aegis.modules.commandlets import CommandletFlags, CommandletRecipe


def recipe_from_inputs(scope: ScopeGroup, flags: FlagsGroup) -> CommandletRecipe:
    flags_obj = CommandletFlags(
        unattended=flags.flag_unatt.isChecked(),
        nop4=flags.flag_nop4.isChecked(),
        nullrhi=flags.flag_nullrhi.isChecked(),
        stdout=flags.flag_stdout.isChecked(),
        utf8=flags.flag_utf8.isChecked(),
    )
    return CommandletRecipe(
        commandlet=scope.cmdlet_cb.currentText(),
        packages=[p for p in scope.packages_le.text().split(";") if p],
        maps=[m for m in scope.maps_le.text().split(";") if m],
        collection=scope.collection_le.text().strip(),
        extra_args=flags.extra_le.text().strip(),
        flags=flags_obj,
    )


def apply_recipe_to_inputs(
    recipe: CommandletRecipe, scope: ScopeGroup, flags: FlagsGroup
) -> None:
    scope.cmdlet_cb.setCurrentText(recipe.commandlet)
    for le, text in [
        (scope.packages_le, ";".join(recipe.packages)),
        (scope.maps_le, ";".join(recipe.maps)),
        (scope.collection_le, recipe.collection),
        (flags.extra_le, recipe.extra_args),
    ]:
        le.setText(text)
    for cb, state in [
        (flags.flag_unatt, recipe.flags.unattended),
        (flags.flag_nop4, recipe.flags.nop4),
        (flags.flag_nullrhi, recipe.flags.nullrhi),
        (flags.flag_stdout, recipe.flags.stdout),
        (flags.flag_utf8, recipe.flags.utf8),
    ]:
        cb.setChecked(state)
