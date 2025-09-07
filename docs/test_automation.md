# Tests & Automation Design

This document outlines the architecture for the Gauntlet and BuildGraph
integrations that power automated test and build scenarios.

## Gauntlet Runner

- Wraps `RunUAT Gauntlet` to launch client, server, and editor tests.
- Captures CSV profiler data, Unreal Insights traces, and device logs.
- Paths such as `RunUAT.bat` and `UnrealEditor-Cmd.exe` are auto-detected from
the active profile's engine directory.
- The panel exposes a copyable CLI preview and streams merged stdout/stderr to
a live log.

## BuildGraph Runner

- Invokes `RunUAT BuildGraph` with preset XML scripts for reproducible
packaging flows.
- Supports Windows, Android AAB/OBB, and tools bundles.
- Required variables (e.g. project, platform, archive directory) are surfaced
in the UI and saved alongside the CLI preview for reruns.
- The `RunUAT.bat` path and project `.uproject` are auto-filled from the
engine profile.

## Presets

Preset XML files live under `docs/buildgraph/presets/` and are intentionally
minimal to illustrate node ordering. The repository currently ships:

- `game_windows_package.xml` – builds and archives a Windows client.
- `game_android_aab.xml` – packages an Android App Bundle.
- `game_android_obb.xml` – packages an Android APK with an OBB.
- `tools_pack.xml` – bundles common Unreal Engine tools for CI use.

Each preset is designed for deterministic runs and produces artifacts under
`.aegis/artifacts/`.
