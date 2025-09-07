from pathlib import Path
import sys

import pytest

pytest.importorskip("PySide6")

from aegis.core.profile import Profile  # noqa: E402
from aegis.modules.trace_ops import TraceOpsController  # noqa: E402
from aegis.ui.pages.page_trace_ops import TraceOpsPage  # noqa: E402
from aegis.ui.profile_actions import ProfileActions  # noqa: E402


def _noop_log(_msg: str, _level: str) -> None:
    pass


class _StubPanel:
    def update_profile(self, _profile: Profile | None) -> None:
        pass


class _StubInfoBar:
    def update(self, _profile: Profile | None, _path: str | None) -> None:
        pass


class _StubActions(ProfileActions):
    def __init__(self, page: TraceOpsPage) -> None:
        self.profile = None
        self.info_bar = _StubInfoBar()
        self.env_doc = _StubPanel()
        self.batch_panel = _StubPanel()
        self.uaft_panel = _StubPanel()
        self.pak_panel = _StubPanel()
        self.commandlet_runner = _StubPanel()
        self.gauntlet_panel = _StubPanel()
        self.buildgraph_panel = _StubPanel()
        self.trace_ops_page = page
        self._log = lambda _m, _l: None
        self.setWindowTitle = lambda _s: None


def test_profile_change_updates_trace_ops_page(tmp_path: Path, qtbot) -> None:
    engine = tmp_path / "UE"
    plat = "Win64" if sys.platform == "win32" else "Linux"
    bin_root = engine / "Engine" / "Binaries"
    (bin_root / plat).mkdir(parents=True)
    project_dir = tmp_path / "Proj"
    project_dir.mkdir()
    profile = Profile(engine_root=engine, project_dir=project_dir)
    page = TraceOpsPage(TraceOpsController(), _noop_log)
    qtbot.addWidget(page)
    actions = _StubActions(page)
    actions.profile = profile
    actions._profile_changed()
    assert page.engine_label.text() == str(bin_root)


def test_profile_change_engine_subdir(tmp_path: Path, qtbot) -> None:
    engine = tmp_path / "UE" / "Engine"
    plat = "Win64" if sys.platform == "win32" else "Linux"
    bin_root = engine / "Binaries"
    (bin_root / plat).mkdir(parents=True)
    project_dir = tmp_path / "Proj"
    project_dir.mkdir()
    profile = Profile(engine_root=engine, project_dir=project_dir)
    page = TraceOpsPage(TraceOpsController(), _noop_log)
    qtbot.addWidget(page)
    actions = _StubActions(page)
    actions.profile = profile
    actions._profile_changed()
    assert page.engine_label.text() == str(bin_root)
