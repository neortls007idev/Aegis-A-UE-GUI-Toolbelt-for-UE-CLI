from pathlib import Path

from aegis.core.app_preferences import (
    list_profiles,
    list_themes,
    list_log_colors,
    list_keybindings,
)


def test_list_app_preferences(tmp_path: Path) -> None:
    # create sample files in each preferences directory under tmp_path
    (tmp_path / "profiles").mkdir(parents=True)
    (tmp_path / "profiles" / "default.json").write_text("{}")

    (tmp_path / "ui" / "themes").mkdir(parents=True)
    (tmp_path / "ui" / "themes" / "dark.qss").write_text("")

    (tmp_path / "ui" / "log_colors").mkdir(parents=True)
    (tmp_path / "ui" / "log_colors" / "colors.json").write_text("{}")

    (tmp_path / "keybindings").mkdir(parents=True)
    (tmp_path / "keybindings" / "bindings.json").write_text("{}")

    assert [p.name for p in list_profiles(tmp_path)] == ["default.json"]
    assert [p.name for p in list_themes(tmp_path)] == ["dark.qss"]
    assert [p.name for p in list_log_colors(tmp_path)] == ["colors.json"]
    assert [p.name for p in list_keybindings(tmp_path)] == ["bindings.json"]
