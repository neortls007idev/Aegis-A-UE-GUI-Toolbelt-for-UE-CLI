import sys
import time
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from aegis.modules.uaft import Uaft


def make_ini(path: Path, token: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""
[/Script/AndroidFileServerEditor.AndroidFileServerRuntimeSettings]
SecurityToken={token}
""",
        encoding="utf-8",
    )


def test_security_token_updates(tmp_path: Path) -> None:
    ini = tmp_path / "Config" / "DefaultEngine.ini"
    make_ini(ini, "AAA")
    uaft = Uaft(Path("uaft"), project_dir=tmp_path)
    assert uaft.security_token() == "AAA"
    time.sleep(1.1)
    make_ini(ini, "BBB")
    time.sleep(1.5)
    assert uaft.security_token() == "BBB"
    uaft.stop()


def test_security_token_after_delimiter(tmp_path: Path) -> None:
    ini = tmp_path / "Config" / "DefaultEngine.ini"
    ini.parent.mkdir(parents=True, exist_ok=True)
    ini.write_text(
        """
[/Script/AndroidFileServerEditor.AndroidFileServerRuntimeSettings]
SecurityToken=Key=ZZZ
""",
        encoding="utf-8",
    )
    uaft = Uaft(Path("uaft"), project_dir=tmp_path)
    assert uaft.security_token() == "ZZZ"
    uaft.stop()


def test_security_token_configs_dir(tmp_path: Path) -> None:
    ini = tmp_path / "Configs" / "DefaultEngine.ini"
    make_ini(ini, "CCC")
    uaft = Uaft(Path("uaft"), project_dir=tmp_path)
    assert uaft.security_token() == "CCC"
    uaft.stop()
