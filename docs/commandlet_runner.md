# Commandlet Runner

A dockable panel that turns Unreal commandlets into one-click actions with a copyable CLI preview and streamed logs.

## Goals & Scope
- Launch `UnrealEditor-Cmd.exe` against a chosen `.uproject`.
- Provide JSON recipes for repeatable runs.
- Filter scope by packages, paths, collections, or maps.
- Remain engine-agnostic by only invoking official tools.
- Make commands and output copyable and auditable.

## UI Layout
1. **Paths & Target**
   - Browse and validate paths to `UnrealEditor-Cmd.exe` and the target project in a single row.
2. **Commandlet & Scope**
   - Dropdown of common commandlets with an **Add** button for project-specific entries.
   - Inputs for packages/paths, collections, and maps with wildcard support.
3. **Behavior Flags**
   - Common toggles laid out horizontally: `-unattended`, `-nop4`, `-NullRHI`, `-stdout`, `-UTF8Output`.
   - Free-form extra arguments appended verbatim.
4. **Run Controls**
   - **Dry Run** – compose and show the final CLI without executing.
   - **Run** – execute using `QProcess` and stream merged stdout/stderr.
   - **Stop** – attempt graceful termination, then force-kill if needed.
5. **Observability**
   - Read-only command preview with copy button.
   - Output streams to the main log panel with search and filtering.
6. **Recipes**
   - Save/load JSON recipes at `<uproject>/.aegies/recipes/commandlets/*.json`.
   - Custom commandlets persist at `<uproject>/.aegies/commandlets.json`.
   - Auto-save last used settings per profile.

## Command Construction
The runner composes conservative argv lists:

```
UnrealEditor-Cmd.exe "<Project.uproject>" -run=<Commandlet> -unattended -nop4 -UTF8Output
```

Scope options:
- `-Package="/Game/MyPath"` for each package or path token.
- `-Map=<MapAsset>` for each map.
- `-Collection=<Name>` for collection filters.
- Extra arguments supplied verbatim.

## Architecture & Data Flow
1. **Validation** – ensure paths exist and at least one scope option is set when required.
2. **Command Builder** – build an argv list and populate the preview command.
3. **Execution** – run with `QProcess`, `MergedChannels`, and stream log output.
4. **Logging & Export** – record stdout/stderr and final argv in the task transcript.
5. **Profiles & Recipes** – defaults from the active profile with shareable recipe files.

## Guardrails
- Never use `shell=True`.
- Show reminders for operations that modify content.
- Disable inputs while a run is active.
- Dry-run preview must match the executable argv exactly.

## Failure Modes & Fixes
| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| `UnrealEditor-Cmd.exe` not found | Wrong engine path | Point to `Engine/Binaries/Win64/UnrealEditor-Cmd.exe` |
| Exit code non-zero with missing modules | Project or plug-in not compiled | Rebuild the editor target and verify plug-ins |
| "No assets matched scope" | Bad `-Package`/`-Map` patterns | Use absolute `/Game/...` paths or broaden scope |
| Editor tries to open UI | Missing `-unattended` or `-NullRHI` | Keep both toggles enabled for headless runs |
| Hangs on Perforce dialog | P4 integration active | Use `-nop4` or disconnect Perforce |
| Unicode garbling | Code page mismatch | Add `-UTF8Output` and decode as UTF-8 |

