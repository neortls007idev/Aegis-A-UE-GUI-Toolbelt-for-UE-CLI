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
    ) -> None:
        """Launch a subprocess and stream its output.

        Parameters
        ----------
        argv
            Command arguments passed to :class:`subprocess.Popen`.
        on_stdout
            Callback invoked for each line of ``stdout``.
        on_stderr
            Callback invoked for each line of ``stderr``.
        on_exit
            Callback invoked with the process' exit code when it finishes.

        Threading
        ---------
        Output streams are pumped on daemon threads so the GUI thread remains
        responsive. A watcher thread waits for process completion, resets the
        runner's state, invokes ``on_exit``, and emits :pyattr:`finished`.

        Signals
        -------
        started
            Emitted immediately after the subprocess is spawned.
        finished
            Emitted with the exit code after the watcher thread completes.

        Raises
        ------
        RuntimeError
            If another task is already running.
        """
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

    def cancel(self) -> None:
        """Terminate the running subprocess, if any.

        ``terminate()`` sends ``SIGTERM`` and returns immediately; the watcher
        thread created by :meth:`start` still emits :pyattr:`finished` when the
        process exits. Calling :meth:`cancel` when no task is active is a
        no-op.
        """
        if self._proc:
            self._proc.terminate()
            self._proc = None
