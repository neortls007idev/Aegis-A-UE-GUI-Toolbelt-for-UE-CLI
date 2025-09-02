from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass


@dataclass
class Uaft:
    """Thin UAFT command helper.

    Builds argv lists for UAFT operations and provides parsers for
    the tool's line-based output. The UI is responsible for running the
    commands via :class:`~aegis.core.task_runner.TaskRunner` and handling
    streaming output.
    """

    exe: Path

    # ----- Arg builders -----
    def devices_argv(self) -> list[str]:
        return [str(self.exe), "devices"]

    @staticmethod
    def parse_devices(lines: list[str]) -> list[str]:
        devices: list[str] = []
        for ln in lines:
            ln = ln.strip().lstrip("@")
            if ln and " " not in ln and ln.lower() != "devices":
                devices.append(ln)
        return devices

    def packages_argv(self, serial: str | None = None) -> list[str]:
        args = [str(self.exe)]
        if serial:
            args += ["-s", serial]
        args += ["packages"]
        return args

    @staticmethod
    def parse_packages(lines: list[str]) -> list[str]:
        return [ln.strip() for ln in lines if "." in ln.strip()]

    def push_commandfile_argv(
        self,
        serial: str | None,
        ip: str | None,
        port: str | None,
        package: str,
        token: str | None,
        local_cmd: str,
    ) -> list[str]:
        args = [str(self.exe)]
        if serial:
            args += ["-s", serial]
        elif ip:
            args += ["-ip", ip]
        if port:
            args += ["-t", port]
        args += ["-p", package]
        if token:
            args += ["-k", token]
        args += ["push", local_cmd, "^commandfile"]
        return args

    def list_traces_argv(
        self,
        serial: str | None,
        ip: str | None,
        port: str | None,
        package: str,
        token: str | None,
    ) -> list[str]:
        args = [str(self.exe)]
        if serial:
            args += ["-s", serial]
        elif ip:
            args += ["-ip", ip]
        if port:
            args += ["-t", port]
        args += ["-p", package]
        if token:
            args += ["-k", token]
        args += ["ls", "-R", "^saved/Traces"]
        return args

    @staticmethod
    def parse_traces(lines: list[str]) -> list[str]:
        files: list[str] = []
        for ln in lines:
            ln = ln.strip()
            if ln.endswith(".trace") or ln.endswith(".utrace"):
                files.append(ln)
        return files

    def pull_trace_argv(
        self,
        serial: str | None,
        ip: str | None,
        port: str | None,
        package: str,
        token: str | None,
        remote_file: str,
        local_dir: Path,
    ) -> list[str]:
        local_dir.mkdir(parents=True, exist_ok=True)
        args = [str(self.exe)]
        if serial:
            args += ["-s", serial]
        elif ip:
            args += ["-ip", ip]
        if port:
            args += ["-t", port]
        args += ["-p", package]
        if token:
            args += ["-k", token]
        args += ["pull", remote_file, str(local_dir)]
        return args
