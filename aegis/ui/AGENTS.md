# AGENTS: UI Guidelines

## Scope
Applies to everything under `aegis/ui`.

## Widget naming
- Custom widget classes use PascalCase and end with `Widget`.
- Instances use snake_case `objectName` values with short suffixes such as `_btn`, `_dock`, and `_log`.
- Button labels start with verbs.
- Set an `objectName` for every widget that needs styling or state persistence.

## QDockWidget usage
- Use `QDockWidget` for panels; enable docking, floating, and tabbing.
- Call `setAllowedAreas(Qt.AllDockWidgetAreas)` and set features to `DockWidgetMovable | DockWidgetFloatable`.
- Give each dock a unique `objectName` and default dock location.
- Provide "Reset Layout" and "Load Theme…" actions in the main window.

## Theme and QSS best practices
- Theme files live in `aegis/ui/themes/*.qss`; avoid inline styles.
- Target widgets via `objectName` selectors (e.g. `#build_btn`) to keep rules explicit.
- Maintain dark, light, and high-contrast variants; ensure accessibility.
- Persist the selected theme with `QSettings`.

## Verb-first buttons and command previews
- Labels use verb-first phrases such as `Build Paks`, `Run Tests`, or `Generate Project Files`.
- Before executing a task, show a copyable CLI preview that matches the actual `argv`, e.g.

```
uaft --cook --target=Win64
```

- The preview must exactly match the subprocess command that runs.

## Type hints and subprocess rules
- Follow [CODING_STANDARDS.md](../../CODING_STANDARDS.md) for required type hints and subprocess usage.

