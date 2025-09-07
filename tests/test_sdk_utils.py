from pathlib import Path

from aegis.core.sdk_utils import detect_sdk_version


def test_detect_android_sdk(tmp_path: Path) -> None:
    sdk = tmp_path / "sdk"
    (sdk / "platforms" / "android-31").mkdir(parents=True)
    info = detect_sdk_version("Android SDK", sdk)
    assert info.version == "31"
    assert not info.warn


def test_detect_android_ndk(tmp_path: Path) -> None:
    ndk = tmp_path / "ndk"
    ndk.mkdir()
    (ndk / "source.properties").write_text("Pkg.Revision=23.1", encoding="utf-8")
    info = detect_sdk_version("Android NDK", ndk)
    assert info.version == "23.1"
    assert not info.warn


def test_detect_jdk(tmp_path: Path) -> None:
    jdk = tmp_path / "jdk"
    jdk.mkdir()
    (jdk / "release").write_text('JAVA_VERSION="17"', encoding="utf-8")
    info = detect_sdk_version("JDK", jdk)
    assert info.version == "17"
    assert not info.warn


def test_detect_vulkan(tmp_path: Path) -> None:
    vulkan = tmp_path / "1.3.250"
    vulkan.mkdir()
    info = detect_sdk_version("Vulkan SDK", vulkan)
    assert info.version == "1.3.250"
    assert not info.warn


def test_detect_unknown(tmp_path: Path) -> None:
    info = detect_sdk_version("Unknown", tmp_path / "missing")
    assert info.warn
    assert info.version == "Version Unknown"
