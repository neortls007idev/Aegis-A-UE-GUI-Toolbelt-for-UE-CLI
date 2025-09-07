"""Model representing a task queued in the batch builder panel."""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtWidgets import QCheckBox, QListWidgetItem, QProgressBar, QWidget


@dataclass(slots=True)
class QueuedTask:
    """State for a single queued build task."""

    tag: str
    config: str
    platform: str
    item: QListWidgetItem
    widget: QWidget
    bar: QProgressBar
    edit: QCheckBox
    clean: bool = False
    cmd_override: str | None = None
