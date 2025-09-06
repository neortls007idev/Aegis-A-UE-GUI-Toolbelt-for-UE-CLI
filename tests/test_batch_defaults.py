import pytest

pytest.importorskip("PySide6")

from aegis.ui.widgets.batch_builder_panel import DEFAULT_CONFIGS, DEFAULT_PLATFORMS


def test_default_configs_include_server_and_editor():
    assert "DevelopmentServer" in DEFAULT_CONFIGS
    assert "DevelopmentEditor" in DEFAULT_CONFIGS


def test_default_platforms_include_mac():
    assert "Mac" in DEFAULT_PLATFORMS
