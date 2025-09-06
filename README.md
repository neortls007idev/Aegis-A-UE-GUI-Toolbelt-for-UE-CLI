# Aegis-A-UE-GUI-Toolbelt-for-UE-CLI

A cross-platform PySide6 GUI toolbelt that turns Unreal Engine command-line tools into one-click workflows. It supports theming,
dockable panes, live logs, command previews, and is built for future expansion.

Powered with - PySide6

## Features

- **Batch builder** – queue Clean, Build, Rebuild, Cook, Stage, Package and DDC tasks. Each step shows per-task and overall progress,
  supports reordering, and can be cancelled at any time.
- **Config & platform profiles** – project profiles persist custom build configurations and target platforms in their JSON files.
- **UBT & UAT helpers** – generate `Build.bat/.sh` and `RunUAT.bat/.sh` commands with exact CLI previews, resolving Engine paths and
  logging missing files.
- **UAFT traces** – run trace captures using arguments from `UECommandline.txt`.

## Quick start

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m aegis.app
```

## Usage

### Batch builder

Use the **Batch Builder** panel to assemble a sequence of build steps:

1. Clean
2. Build (iterative)
3. Rebuild (clean build)
4. Cook
5. Stage
6. Package
7. Derived Data Cache (build/clean/rebuild)

Each step can optionally clean its output directory before running. Tasks start from the selected profile's
build configuration and target platform, and the exact command line for each step is shown so you can copy
and reuse it in scripts. Unstarted tasks can be reordered or removed, and running tasks can be cancelled.

### UAFT traces

The UAFT module reads trace arguments from `UECommandline.txt`. A sample file is provided with the following contents:

```
-tracehost=127.0.0.1 -trace=Bookmark,Frame,CPU,GPU,LoadTime,File -cpuprofilertrace -statnamedevents -filetrace -loadtimetrace
```

For Memory Insights include `-trace=default,memory` and ensure a Development build.

## Development

Install development dependencies:

```bash
pip install -r requirements-dev.txt
pre-commit install
```

Run linters, type checks, and tests before committing:

```bash
ruff check .
black --check .
mypy
PYTHONPATH=$PWD pytest
```

See `CODING_STANDARDS.md` for naming conventions and guardrails.

## CI/CD

GitHub Actions runs `ruff check`, `black --check`, `mypy`, and `PYTHONPATH=$PWD pytest` on pushes to `main`, `dev`, `feat/**`, and `maintenance/**` branches. Codex/AI agents and contributors must add or update unit and functional tests for new behavior and keep workflows, dependencies, and tooling in sync so the pipeline stays green.

## Architecture overview

The codebase is organized to keep UI concerns separate from core logic:

- `aegis/app.py` – application entry point.
- `aegis/core` – reusable services such as the task runner and settings.
- `aegis/modules` – thin wrappers for Unreal command-line tools.
- `aegis/ui` – all widgets, pages, and theme assets.

Commands are executed through `TaskRunner` using argv lists; stdout/stderr are streamed to the log panel and the exit code is surfaced to the user.

## Troubleshooting

- **Import errors** – run tests with `PYTHONPATH=$PWD` or install the package in editable mode.
- **Missing PySide6** – install Qt bindings via `pip install -r requirements.txt`.
- **Stuck or blocking UI** – ensure long-running subprocesses use background threads.

See `CONTRIBUTORS.md` for contributor guidelines.

