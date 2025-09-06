# Coding Standards

- **Python version**: 3.11 or newer.
- **Type hints**: required for all functions and methods.
- **Formatting**: `black` for code style, `ruff` for linting.
- **Type checking**: `mypy` run against core modules.
- **Naming**: snake_case for functions and variables; PascalCase for classes; file names in snake_case.
- **Subprocesses**: never use `shell=True`; pass `argv` lists and stream stdout/stderr.
- **UI threads**: long-running tasks must not block the GUI thread; use background threads for subprocess streaming.
- **Logging**: redact secrets or tokens; surface exit codes and errors.
- **Tests**: add or update unit and functional tests for every change.
- **Automation**: run `ruff check .`, `black --check .`, `mypy`, and `PYTHONPATH=$PWD pytest` before pushing. CI verifies these checks on `main`, `dev`, `feat/**`, and `maintenance/**` branches.
- **Dependencies and tooling**: keep requirements, pre-commit hooks, and GitHub Actions workflows in sync when introducing new tools.
