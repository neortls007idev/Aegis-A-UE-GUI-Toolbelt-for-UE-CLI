from __future__ import annotations

import io
import json
import os
from pathlib import Path
from urllib.error import URLError
from unittest.mock import patch

import pytest

pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication

from aegis.core.profile import Profile
from aegis.core.task_runner import TaskRunner
from aegis.ui.widgets.env_doc import EnvDocPanel


@pytest.fixture(scope="module")
def app() -> QApplication:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def _panel_with_logs() -> tuple[EnvDocPanel, list[tuple[str, str]]]:
    logs: list[tuple[str, str]] = []
    panel = EnvDocPanel(TaskRunner(), lambda m, level: logs.append((m, level)))
    return panel, logs


def test_collect_scripts_requires_profile(app: QApplication) -> None:
    panel, _ = _panel_with_logs()
    with pytest.raises(RuntimeError, match="profile not loaded"):
        panel._collect_scripts()


def test_collect_scripts_with_profile(app: QApplication, tmp_path: Path) -> None:
    engine = tmp_path / "eng"
    (engine / "Extras" / "Android").mkdir(parents=True)
    local = engine / "Extras" / "Android" / "SetupAndroid.sh"
    local.write_text("", "utf-8")
    panel, _ = _panel_with_logs()
    panel.update_profile(Profile(engine, tmp_path))
    with patch.object(panel, "_fetch_remote_scripts", return_value={"Remote": local}):
        scripts = panel._collect_scripts()
    assert scripts["Android Dependencies"] == local
    assert "Remote" in scripts


def test_fetch_remote_scripts_network_error(app: QApplication) -> None:
    panel, logs = _panel_with_logs()
    with (
        patch("urllib.request.urlopen", side_effect=URLError("boom")),
        patch("urllib.request.urlretrieve", side_effect=URLError("boom")),
    ):
        scripts = panel._fetch_remote_scripts()
    assert scripts == {}
    assert any("boom" in msg for msg, _level in logs)


def test_fetch_remote_scripts_cleanup(app: QApplication, monkeypatch) -> None:
    panel, _ = _panel_with_logs()
    data = [{"name": "fix", "url": "https://example.com/fix.sh"}]

    class DummyResp(io.StringIO):
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            self.close()
            return False

    monkeypatch.setattr(
        "urllib.request.urlopen", lambda *_: DummyResp(json.dumps(data))
    )

    def fake_urlretrieve(url: str, dest: str, *_args, **_kwargs) -> None:
        Path(dest).write_text("", "utf-8")

    monkeypatch.setattr("urllib.request.urlretrieve", fake_urlretrieve)

    scripts = panel._fetch_remote_scripts()
    assert "fix" in scripts
    tmp_dir = panel._tmp_dir
    assert tmp_dir is not None and Path(tmp_dir.name).exists()
    tmp_dir.cleanup()
    assert not Path(tmp_dir.name).exists()
