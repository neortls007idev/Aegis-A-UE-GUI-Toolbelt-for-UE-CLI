from pathlib import Path
import time

import pytest

from aegis.modules.uaft_token import UaftTokenWatcher


def make_ini(path: Path, token: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""
[/Script/AndroidFileServerEditor.AndroidFileServerRuntimeSettings]
SecurityToken={token}
""",
        encoding="utf-8",
    )


def test_token_refresh(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    ini = tmp_path / "Config" / "DefaultEngine.ini"
    make_ini(ini, "AAA")
    monkeypatch.setattr("aegis.modules.uaft_token.Observer", None)
    watcher = UaftTokenWatcher(tmp_path)
    assert watcher.security_token() == "AAA"
    watcher.token_updated.clear()
    time.sleep(1.1)
    make_ini(ini, "BBB")
    assert watcher.token_updated.wait(timeout=5)
    assert watcher.security_token() == "BBB"
    watcher.stop()
