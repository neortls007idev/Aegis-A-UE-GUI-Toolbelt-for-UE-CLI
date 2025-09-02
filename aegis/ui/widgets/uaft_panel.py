from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from aegis.core.profile import Profile
from aegis.core.task_runner import TaskRunner


class UaftPanel(QWidget):
    """Display UAFT and Unreal Insights locations."""

    def __init__(
        self,
        runner: TaskRunner,
        log_cb: Callable[[str, str], None],
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.runner = runner
        self.log = log_cb
        self.profile: Profile | None = None
        self.uaft_path: Path | None = None
        self.insights_path: Path | None = None

        self.uaft_label = QLabel("UAFT: (not found)")
        self.uaft_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.insights_label = QLabel("Unreal Insights: (not found)")
        self.insights_label.setTextInteractionFlags(Qt.TextSelectableByMouse)

        self.build_uaft_btn = QPushButton("Build UAFT")
        self.build_uaft_btn.clicked.connect(self._build_uaft)
        self.build_insights_btn = QPushButton("Build Unreal Insights")
        self.build_insights_btn.clicked.connect(self._build_insights)

        layout = QVBoxLayout(self)
        layout.addWidget(self.uaft_label)
        layout.addWidget(self.build_uaft_btn)
        layout.addSpacing(8)
        layout.addWidget(self.insights_label)
        layout.addWidget(self.build_insights_btn)
        layout.addStretch()
        self.build_uaft_btn.hide()
        self.build_insights_btn.hide()

    # ----- Profile -----
    def update_profile(self, profile: Optional[Profile]) -> None:
        self.profile = profile
        self._scan()

    def _scan(self) -> None:
        self.uaft_path = None
        self.insights_path = None
        if not self.profile:
            self.uaft_label.setText("UAFT: (no profile)")
            self.insights_label.setText("Unreal Insights: (no profile)")
            self.build_uaft_btn.hide()
            self.build_insights_btn.hide()
            return

        engine_root = self.profile.engine_root
        self.uaft_path = next(engine_root.rglob("UAFT.exe"), None)
        if not self.uaft_path:
            self.uaft_path = next(engine_root.rglob("UAFT"), None)
        self.insights_path = next(engine_root.rglob("UnrealInsights.exe"), None)
        if not self.insights_path:
            self.insights_path = next(engine_root.rglob("UnrealInsights"), None)

        self.uaft_label.setText(
            f"UAFT: {self.uaft_path}" if self.uaft_path else "UAFT: (not found)"
        )
        self.insights_label.setText(
            "Unreal Insights: " f"{self.insights_path}"
            if self.insights_path
            else "Unreal Insights: (not found)"
        )
        self.build_uaft_btn.setVisible(self.uaft_path is None)
        self.build_insights_btn.setVisible(self.insights_path is None)

    # ----- Build -----
    def _build_uaft(self) -> None:
        if not self.profile:
            self.log("[uaft] No profile selected", "error")
            return
        script = (
            self.profile.engine_root / "Engine" / "Build" / "BatchFiles" / "RunUAT.sh"
        )
        argv = [str(script), "BuildUAFT"]
        self._run(argv, "uaft")

    def _build_insights(self) -> None:
        if not self.profile:
            self.log("[insights] No profile selected", "error")
            return
        script = (
            self.profile.engine_root / "Engine" / "Build" / "BatchFiles" / "RunUAT.sh"
        )
        argv = [str(script), "BuildUnrealInsights"]
        self._run(argv, "insights")

    def _run(self, argv: list[str], tag: str) -> None:
        self.log(f"[{tag}] {' '.join(argv)}", "info")
        try:
            self.runner.start(
                argv,
                on_stdout=lambda s: self.log(f"[{tag}] {s}", "info"),
                on_stderr=lambda s: self.log(f"[{tag}] {s}", "error"),
                on_exit=lambda code: self.log(
                    f"[{tag}] exit code {code}", "success" if code == 0 else "error"
                ),
            )
        except Exception as e:  # pragma: no cover - subprocess failures
            self.log(f"[{tag}] {e}", "error")
