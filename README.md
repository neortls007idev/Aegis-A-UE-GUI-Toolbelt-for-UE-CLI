# Aegis-A-UE-GUI-Toolbelt-for-UE-CLI

A cross-platform PySide6 GUI toolbelt that turns Unreal Engine command-line tools into one-click workflows. It supports theming,
 dockable panes, live logs, command previews, and is built for future expansion.

Powered with - PySide6

## Quick start

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m aegis.app
```

## Usage

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

Run linters and tests before committing:

```bash
ruff .
black --check .
pytest
```

See `CONTRIBUTORS.md` for contributor guidelines.

