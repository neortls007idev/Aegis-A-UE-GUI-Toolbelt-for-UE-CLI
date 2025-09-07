# Architecture

This project wraps Unreal Engine command‑line tools in a PySide6 desktop GUI.
The repository is organized so core services, thin CLI modules, and UI widgets
stay decoupled and easy to extend.

## Repository layout

- `aegis/app.py` – application entry point
- `aegis/core/` – shared services such as settings management and the
  subprocess task runner
- `aegis/modules/` – wrappers for individual Unreal command‑line tools
- `aegis/ui/` – Qt widgets, pages, and themes
- `docs/` – developer documentation
- `tests/` – unit and functional tests

## Core

The core package provides reusable building blocks:

- `task_runner.py` – streams subprocess output on background threads so the UI
  remains responsive. See the `start` and `cancel` docstrings for API details.
- `settings.py` and `profile.py` – persist application preferences and project
  profiles.
- Helpers like `app_preferences.py`, `key_bindings.py`, and `log_colors.py`.

These modules avoid GUI dependencies and can be imported by both CLI wrappers
and widgets.

## Modules

`aegis/modules` contains thin adapters around command‑line tools such as
`uaft.py`, `uat.py`, and `ubt.py`.

Responsibilities:

- Build exact argv lists without using `shell=True`.
- Parse line‑based output where helpful.
- Delegate execution to `TaskRunner` so stdout/stderr stream into the Live Log
  and exit codes surface to the user.

### Extension points

To add a new CLI integration:

1. Create a module under `aegis/modules` that exposes functions or classes to
   build argv lists and parse output.
2. Use `TaskRunner` to execute commands from the UI.
3. Avoid blocking calls and redact secrets in logs.

## UI layout

All Qt code lives under `aegis/ui`:

- `main_window.py` configures the `QMainWindow` and dock widgets.
- `pages/` groups high‑level views.
- `widgets/` holds dockable panels such as `log_panel.py`,
  `batch_builder_panel.py`, and `uaft_panel.py`.
- `themes/` contains QSS files (`dark.qss`, `light.qss`, `high_contrast.qss`).

UI elements follow these conventions:

- Widgets have verb‑first buttons and expose an exact command preview.
- Each dock uses `setAllowedAreas(Qt.AllDockWidgetAreas)` and enables the
  `DockWidgetMovable | DockWidgetFloatable` features.
- Themes are loaded via `QSettings` with a "Reset Layout" and "Load Theme…"
  action available in the main menu.

### Adding UI for new tools

Create a widget under `aegis/ui/widgets` that uses your module's argv builders.
Register it with `main_window.py` or the relevant page so the panel can be
docked and the command preview matches the executed argv.

## Integrating new CLI tools

When introducing another command‑line tool:

1. Detect the tool's executable path (respecting platform differences and EULA
   safety).
2. Implement argv builders and output parsers in a new
   `aegis/modules/<tool>.py` file.
3. Build a UI panel in `aegis/ui/widgets` that leverages `TaskRunner` for
   non‑blocking execution and streams logs to the Live Log.
4. Persist any settings via `settings.py` or `profile.py` and follow existing
   theming and layout conventions.

This separation ensures one‑click actions with accurate previews, guardrails,
and self‑service logs while keeping the codebase straightforward to grow.
