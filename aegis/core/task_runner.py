import subprocess
import threading
from typing import Callable, List, Optional

from PySide6.QtCore import QObject, Signal


class TaskRunner(QObject):
    """Minimal non-blocking subprocess runner.

    Emits ``started`` when a task begins and ``finished`` with the exit code
    when the task completes. Only a single task can run at a time.
    """

    started = Signal()
    finished = Signal(int)

    def __init__(self) -> None:
        super().__init__()
        self._proc: Optional[subprocess.Popen] = None

    def start(
        self,
        argv: List[str],
        on_stdout: Callable[[str], None],
        on_stderr: Callable[[str], None],
        on_exit: Callable[[int], None],
    ):
        if self._proc:
            raise RuntimeError("A task is already running")

        self._proc = subprocess.Popen(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            shell=False,
        )
        self.started.emit()

        def pump(stream, cb):
            assert stream is not None
            for line in iter(stream.readline, ""):
                cb(line.rstrip("\n"))
            stream.close()

        t_out = threading.Thread(
            target=pump, args=(self._proc.stdout, on_stdout), daemon=True
        )
        t_err = threading.Thread(
            target=pump, args=(self._proc.stderr, on_stderr), daemon=True
        )
        t_out.start()
        t_err.start()

        def wait_and_finish():
            code = self._proc.wait()
            self._proc = None
            on_exit(code)
            self.finished.emit(code)

        threading.Thread(target=wait_and_finish, daemon=True).start()

    def cancel(self):
        if self._proc:
            self._proc.terminate()
            self._proc = None
