from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from aegis.core.profile import Profile


def test_profile_roundtrip(tmp_path):
    path = tmp_path / "profile.json"
    prof = Profile(
        engine_root=Path("/Engine"),
        project_dir=Path("/Project"),
        nickname="nick",
        build_configs=["Development", "Shipping"],
        build_platforms=["Win64", "Linux"],
    )
    prof.save(path)
    loaded = Profile.load(path)
    assert loaded.build_configs == ["Development", "Shipping"]
    assert loaded.build_platforms == ["Win64", "Linux"]
    assert loaded.nickname == "nick"
