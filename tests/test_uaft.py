from pathlib import Path

import pytest

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
    pytest.importorskip("watchfiles")
    ini = tmp_path / "Config" / "DefaultEngine.ini"
    make_ini(ini, "AAA")
    uaft = Uaft(Path("uaft"), project_dir=tmp_path)
    assert uaft.security_token() == "AAA"
    uaft._token_updated.clear()
    make_ini(ini, "BBB")
    assert uaft._token_updated.wait(timeout=2)
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


def test_security_token_duplicate_options(tmp_path: Path) -> None:
    ini = tmp_path / "Config" / "DefaultEngine.ini"
    ini.parent.mkdir(parents=True, exist_ok=True)
    ini.write_text(
        """
[/Script/AndroidFileServerEditor.AndroidFileServerRuntimeSettings]
SecurityToken=DDD
[/Script/WindowsTargetPlatform.WindowsTargetSettings]
+d3d12targetedshaderformats=PCD3D_SM6
+d3d12targetedshaderformats=PCD3D_SM5
""",
        encoding="utf-8",
    )
    uaft = Uaft(Path("uaft"), project_dir=tmp_path)
    assert uaft.security_token() == "DDD"
    uaft.stop()


def test_security_token_flag_without_value(tmp_path: Path) -> None:
    ini = tmp_path / "Config" / "DefaultEngine.ini"
    ini.parent.mkdir(parents=True, exist_ok=True)
    ini.write_text(
        """
[/Script/AndroidFileServerEditor.AndroidFileServerRuntimeSettings]
SecurityToken=EEE
[/Script/WindowsTargetPlatform.WindowsTargetSettings]
+d3d12targetedshaderformats=PCD3D_SM6
+UseShaderCompilerWorker
""",
        encoding="utf-8",
    )
    uaft = Uaft(Path("uaft"), project_dir=tmp_path)
    assert uaft.security_token() == "EEE"
    uaft.stop()


def test_security_token_special_operators(tmp_path: Path) -> None:
    ini = tmp_path / "Config" / "DefaultEngine.ini"
    ini.parent.mkdir(parents=True, exist_ok=True)
    ini.write_text(
        """
[/Script/AndroidFileServerEditor.AndroidFileServerRuntimeSettings]
SecurityToken=AAA
+SecurityToken=BBB
.SecurityToken=CCC
-SecurityToken=CCC
!SecurityToken
.SecurityToken=DDD
""",
        encoding="utf-8",
    )
    uaft = Uaft(Path("uaft"), project_dir=tmp_path)
    assert uaft.security_token() == "DDD"
    uaft.stop()


def test_security_token_plus_only(tmp_path: Path) -> None:
    ini = tmp_path / "Config" / "DefaultEngine.ini"
    ini.parent.mkdir(parents=True, exist_ok=True)
    ini.write_text(
        """
[/Script/AndroidFileServerEditor.AndroidFileServerRuntimeSettings]
+SecurityToken=AAA
+SecurityToken=BBB
""",
        encoding="utf-8",
    )
    uaft = Uaft(Path("uaft"), project_dir=tmp_path)
    assert uaft.security_token() == "AAA"
    uaft.stop()
