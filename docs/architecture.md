# Architecture

This project wraps Unreal Engine command‑line tools in a PySide6 desktop GUI. The layout keeps core services, thin CLI modules, and UI widgets separate so new tools can plug in cleanly.

## Core
- `aegis/app.py` – application entry point.
- `aegis/core` – infrastructure such as:
  - `task_runner.py` streaming subprocess output without blocking the UI.
  - `settings.py` and `profile.py` for persisted preferences and profiles.
  - helpers like `app_preferences.py`, `key_bindings.py`, and `log_colors.py`.

The core provides shared services and utilities used by all modules and widgets.

## Modules
`aegis/modules` contains thin wrappers around individual CLI tools (e.g. `uaft.py`, `uat.py`, `ubt.py`). Each module focuses on:
- Building exact argv lists without using `shell=True`.
- Parsing line‑based output where helpful.
- Leaving execution to `TaskRunner` so stdout/stderr stream into the Live Log and exit codes surface to the user.

### Extension points
To add a new CLI integration:
1. Create a module in `aegis/modules` that exposes functions or classes to build argv lists and parse output.
2. Use `TaskRunner` to execute commands from the UI.
3. Avoid blocking calls and redact secrets in logs.

## UI layout
`aegis/ui` hosts all Qt code:
- `main_window.py` sets up the `QMainWindow` with movable/floatable/tabbable `QDockWidget` panes.
- `widgets/` contains dock widgets like `log_panel.py`, `batch_builder_panel.py`, and `uaft_panel.py`.
- `themes/` holds QSS files (`dark.qss`, `light.qss`, `high_contrast.qss`) applied via QSettings. A “Reset Layout” and “Load Theme…” action live in the main menu.

UI components present verbs as buttons, show the exact command preview, and stream logs while keeping the GUI thread responsive.

### Adding UI for new tools
Create a widget under `aegis/ui/widgets` that uses your module's argv builders. Register it with `main_window.py` or the appropriate menu/page so it can be docked and the command preview matches the executed argv.

## Integrating new CLI tools
When introducing another command‑line tool:
1. Detect the tool's executable path (respecting platform differences and EULA safety).
2. Implement argv builders and output parsers in a new `aegis/modules/<tool>.py` file.
3. Build a UI panel in `aegis/ui/widgets` that leverages `TaskRunner` for non‑blocking execution and streams logs to the Live Log.
4. Persist any settings via `settings.py` or `profile.py` and follow existing theming and layout conventions.

This separation ensures one‑click actions with accurate previews, guardrails, and self‑service logs while making it straightforward to grow the toolbelt.
