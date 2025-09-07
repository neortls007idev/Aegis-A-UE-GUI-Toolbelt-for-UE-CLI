"""SDK inspection helpers used by the Environment Doctor."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass
class SDKVersion:
    """Result of SDK version detection."""

    version: str
    warn: bool = False


def detect_sdk_version(component: str, path: Path) -> SDKVersion:
    """Return version and warning flag for an SDK component.

    Args:
        component: SDK name such as ``"Android SDK"``.
        path: Directory to inspect.

    Returns:
        :class:`SDKVersion` describing the detected version and whether the
        user should be warned.
    """
    try:
        if component == "Android SDK":
            platforms = path / "platforms"
            if platforms.exists():
                versions: list[int] = []
                for p in platforms.iterdir():
                    if p.is_dir() and p.name.startswith("android-"):
                        try:
                            versions.append(int(p.name.split("-", 1)[1]))
                        except ValueError:
                            continue
                if versions:
                    return SDKVersion(str(max(versions)))
            prop = path / "source.properties"
            if prop.exists():
                for line in prop.read_text(encoding="utf-8").splitlines():
                    if line.startswith("Pkg.Revision="):
                        return SDKVersion(line.split("=", 1)[1].strip())
        elif component == "Android NDK":
            if path.name != "ndk":
                return SDKVersion(path.name)
            prop = path / "source.properties"
            if prop.exists():
                for line in prop.read_text(encoding="utf-8").splitlines():
                    if line.startswith("Pkg.Revision="):
                        return SDKVersion(line.split("=", 1)[1].strip())
        elif component == "JDK":
            rel = path / "release"
            if rel.exists():
                for line in rel.read_text(encoding="utf-8").splitlines():
                    if line.startswith("JAVA_VERSION="):
                        return SDKVersion(line.split("=", 1)[1].strip().strip('"'))
        elif component == "Vulkan SDK":
            return SDKVersion(path.name)
    except Exception:  # pragma: no cover - best effort
        pass
    return SDKVersion("Version Unknown", True)
