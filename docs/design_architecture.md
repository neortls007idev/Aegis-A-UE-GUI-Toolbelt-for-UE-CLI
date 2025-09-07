# Design and Architecture

This document describes the high-level design of the Gauntlet and BuildGraph
runners introduced in Phase 5. Both runners share a common goal: provide
a one-click interface that assembles exact Unreal Automation Tool (UAT)
commands while streaming logs and collecting artifacts.

## Gauntlet Runner
- Builds `RunUAT.bat Gauntlet` commands with tests, platforms, devices,
  optional editor executable and profiling `ExecCmds`.
- Automatically discovers `RunUAT.bat`, `UnrealEditor-Cmd.exe`, and the
  project `.uproject` from the active profile's engine and project
  directories.
- Streams merged stdout/stderr to the log panel and stores exit codes
  for reproducibility.

## BuildGraph Runner
- Assembles `RunUAT.bat BuildGraph` invocations using XML presets.
- Preset variables are exposed in the UI; users can dry-run or execute
  with one click.
- Like the Gauntlet panel, all UAT and project paths auto-populate from
  the active profile.

Both panels follow the north star principles: copyable CLI previews,
non-blocking execution via `TaskRunner`, and structured paths for
artifacts. Future phases can expand on these foundations with richer
preflight checks and artifact harvesting.
