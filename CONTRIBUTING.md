# Contributing

## Development setup
1. Install Python 3.11+.
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt -r requirements-dev.txt
   pre-commit install
   ```

## Branching strategy
- `main` is protected and must not be deleted.
- Use `dev` for integration.
- Prefix feature branches with `feat/` and maintenance branches with `maintenance/`.

## Commit style
- Messages follow `feat|fix|chore(scope): summary`.
- Include tests and screenshots or GIFs for UI changes.

## Coding standards
- See `CODING_STANDARDS.md` for detailed guidelines.
- Run `ruff check .`, `black --check .`, `mypy`, and `PYTHONPATH=$PWD pytest` before pushing.
- Refer to [docs/architecture.md](docs/architecture.md) for layout and extension points when adding new tools.

## UI standards
- Widget classes use PascalCase and end with `Widget`. Instances set a snake_case
  `objectName` with suffixes such as `_btn`, `_dock`, or `_log`.
- Buttons use verb-first labels (for example, `Build Paks`, `Run Tests`). Every
  action shows a copyable command preview that matches the exact `argv` passed to
  `subprocess.Popen`.
- Panels are implemented as `QDockWidget` instances with
  `setAllowedAreas(Qt.AllDockWidgetAreas)` and features set to
  `DockWidgetMovable | DockWidgetFloatable`.
- Themes live under `aegis/ui/themes/*.qss`; target widgets by `objectName` and
  persist the selected theme with `QSettings`.
- See `CODING_STANDARDS.md` for required type hints and subprocess policies.

## Pull requests
- Target `dev` unless fixing a critical issue on `main`.
- Describe manual test steps and results.
- Ensure CI checks pass.
