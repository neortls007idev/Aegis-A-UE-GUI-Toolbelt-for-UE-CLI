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

## Pull requests
- Target `dev` unless fixing a critical issue on `main`.
- Describe manual test steps and results.
- Ensure CI checks pass.
