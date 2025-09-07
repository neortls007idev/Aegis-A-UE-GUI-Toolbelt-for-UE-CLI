from pathlib import Path

from aegis.modules.commandlets import (
    CommandletFlags,
    CommandletRecipe,
    build_argv,
    load_commandlets,
    load_recipe,
    save_commandlets,
    save_recipe,
)


def test_build_argv_basic(tmp_path: Path) -> None:
    exe = tmp_path / "UnrealEditor-Cmd.exe"
    exe.write_text("", encoding="utf-8")
    proj = tmp_path / "Game.uproject"
    proj.write_text("", encoding="utf-8")
    recipe = CommandletRecipe(packages=["/Game/Maps"])  # defaults ResavePackages
    argv = build_argv(exe, proj, recipe)
    assert argv[:3] == [str(exe), str(proj), "-run=ResavePackages"]
    assert '-Package="/Game/Maps"' in argv


def test_recipe_roundtrip(tmp_path: Path) -> None:
    proj = tmp_path / "Game.uproject"
    proj.write_text("", encoding="utf-8")
    recipe = CommandletRecipe(
        commandlet="FixupRedirects",
        packages=["/Game/*"],
        maps=["/Game/Map"],
        collection="MyCollection",
        extra_args="-AllowPlugins",
        flags=CommandletFlags(nullrhi=True, stdout=False),
    )
    path = save_recipe(proj, "sample", recipe)
    loaded = load_recipe(path)
    assert loaded == recipe


def test_commandlet_list_roundtrip(tmp_path: Path) -> None:
    proj = tmp_path / "Game.uproject"
    proj.write_text("", encoding="utf-8")
    cmds = load_commandlets(proj)
    assert "ResavePackages" in cmds
    cmds.append("CustomCmd")
    save_commandlets(proj, cmds)
    loaded = load_commandlets(proj)
    assert "CustomCmd" in loaded
