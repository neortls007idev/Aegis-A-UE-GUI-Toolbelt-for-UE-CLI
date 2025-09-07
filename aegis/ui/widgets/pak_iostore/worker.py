from __future__ import annotations

import shlex
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

from PySide6.QtCore import QObject, QProcess, QTimer

from .utils import build_iostore_cmd, build_unrealpak_cmd, compare_dirs, dest_for


@dataclass
class Task:
    """Discrete unit of work."""

    type: str  # 'proc', 'zip', or 'cmp'
    action: str  # 'list', 'extract', 'validate', 'search', 'compare'
    src: Path
    dest: Optional[Path]
    row: Optional[int]
    argv: Optional[List[str]] = None


class PakWorker(QObject):
    """Sequential task runner for Pak/IoStore operations."""

    def __init__(
        self,
        log_cb: Callable[[str], None],
        preview_cb: Callable[[str], None],
        unrealpak_path: Callable[[], str],
        iostore_path: Callable[[], str],
        pak_filter: Callable[[], str],
        unzip_extract_enabled: Callable[[], bool],
        row_status_cb: Callable[[int, str], None],
        state_cb: Callable[[], None],
    ) -> None:
        super().__init__()
        self.log_cb = log_cb
        self.preview_cb = preview_cb
        self.unrealpak_path = unrealpak_path
        self.iostore_path = iostore_path
        self.pak_filter = pak_filter
        self.unzip_extract_enabled = unzip_extract_enabled
        self.row_status_cb = row_status_cb
        self.state_cb = state_cb
        self.tasks: List[Task] = []
        self.current: Optional[Task] = None
        self.proc: Optional[QProcess] = None

    # public API ---------------------------------------------------------
    def enqueue(self, items: List[Task]) -> None:
        if not items:
            return
        self.tasks.extend(items)
        if not self.proc:
            self._run_next()
        self.state_cb()

    def is_busy(self) -> bool:
        return self.proc is not None or bool(self.tasks)

    def status(self) -> tuple[int, int]:
        running = 1 if self.proc else 0
        return running, len(self.tasks)

    # internals ----------------------------------------------------------
    def _run_next(self) -> None:
        if self.proc or not self.tasks:
            return
        task = self.tasks.pop(0)
        self.current = task
        if task.row is not None:
            self.row_status_cb(task.row, "Running")
        if task.type == "proc" and task.argv:
            self.preview_cb(shlex.join(task.argv))
            program, *args = task.argv
            self.proc = QProcess()
            self.proc.setProcessChannelMode(QProcess.MergedChannels)
            self.proc.setProgram(program)
            self.proc.setArguments(args)
            self.proc.readyReadStandardOutput.connect(self._on_proc_output)
            self.proc.readyReadStandardError.connect(self._on_proc_output)
            self.proc.finished.connect(self._on_proc_finished)
            self.proc.start()
        elif task.type == "zip":
            QTimer.singleShot(0, lambda: self._run_zip(task))
        elif task.type == "cmp":
            QTimer.singleShot(0, lambda: self._run_compare(task))
        else:
            self._finish_task(1)

    def _on_proc_output(self) -> None:
        if not self.proc:
            return
        data = self.proc.readAllStandardOutput().data().decode(errors="ignore")
        if data:
            if self.current and self.current.action == "search":
                term = self.pak_filter()
                for line in data.splitlines():
                    if term in line:
                        self.log_cb(line)
            else:
                self.log_cb(data.rstrip())

    def _on_proc_finished(self, code: int, _status: QProcess.ExitStatus) -> None:
        self._finish_task(code)

    def _run_zip(self, task: Task) -> None:
        self.preview_cb(f"zipfile {task.action} {task.src}")
        try:
            with zipfile.ZipFile(task.src) as zf:
                names = zf.namelist()
                if task.action in {"list", "validate"}:
                    for name in names:
                        self.log_cb(name)
                    code = 0
                elif task.action == "search":
                    filt = self.pak_filter()
                    for name in names:
                        if filt in name:
                            self.log_cb(name)
                    code = 0
                else:
                    dest = task.dest
                    assert dest is not None
                    dest.mkdir(parents=True, exist_ok=True)
                    for name in names:
                        self.log_cb(name)
                    zf.extractall(dest)
                    code = 0
                    if self.unzip_extract_enabled():
                        new_tasks = self._scan_path_for_tasks(dest)
                        self.tasks = new_tasks + self.tasks
        except Exception as exc:  # pragma: no cover - unexpected
            self.log_cb(str(exc))
            code = 1
        self._finish_task(code)

    def _run_compare(self, task: Task) -> None:
        assert task.dest is not None
        self.preview_cb(f"compare {task.src} {task.dest}")
        only_a, only_b, diff = compare_dirs(task.src, task.dest)
        for p in sorted(only_a):
            self.log_cb(f"only in {task.src}: {p}")
        for p in sorted(only_b):
            self.log_cb(f"only in {task.dest}: {p}")
        for p in sorted(diff):
            self.log_cb(f"different: {p}")
        self._finish_task(0)

    def _scan_path_for_tasks(self, root: Path) -> List[Task]:
        tasks: List[Task] = []
        for p in root.rglob("*"):
            if not p.is_file():
                continue
            ext = p.suffix.lower()
            if ext == ".pak":
                dest = dest_for(p, "_extracted")
                argv = build_unrealpak_cmd(
                    self.unrealpak_path(), p, "extract", dest, self.pak_filter() or None
                )
                tasks.append(Task("proc", "extract", p, dest, None, argv))
            elif ext == ".utoc":
                dest = dest_for(p, "_extracted")
                argv = build_iostore_cmd(self.iostore_path(), p, "extract", dest)
                tasks.append(Task("proc", "extract", p, dest, None, argv))
        return tasks

    def _finish_task(self, code: int) -> None:
        if self.current and self.current.row is not None:
            status = "Done" if code == 0 else f"Error {code}"
            self.row_status_cb(self.current.row, status)
        self.log_cb(f"exit code {code}")
        self.proc = None
        self.current = None
        self._run_next()
        self.state_cb()
