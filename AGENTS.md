# AGENTS

## Scope
This file governs the entire repository.

## Instructions
Codex/AI agents and human contributors must:
- Use Python 3.11 or newer.
- Follow `CODING_STANDARDS.md`.
- Format code with `black` and lint with `ruff`.
- Run `ruff check .`, `black --check .`, `mypy`, and `PYTHONPATH=$PWD pytest` before committing. If `black` flags files you didn't touch, you may leave them for a dedicated formatting PR.
- Add or update unit and functional tests for every code change; CI verifies them on push.
- Keep GitHub Actions workflows, pre-commit hooks, and dependency pins up to date when introducing new tools or requirements.
- Avoid using `shell=True` in subprocess calls.
