# Repository Guidelines

## Project Structure & Module Organization

`yggdrasyl/` contains the installable Python package. Public imports are collected in `yggdrasyl/__init__.py`; dependency registration and resolution live in `_dependencies.py`, utility factories in `_utils.py`, and public exceptions in `_errors.py`. Keep `py.typed` so downstream type checkers recognize the package as typed. Tests live in `tests/`, currently centered on `tests/test_dependencies.py`. GitHub Actions under `.github/workflows/` run validation on pushes and publish releases to PyPI.

## Project Context

Always read `README.md` in full before starting work. Treat it as the canonical source
for project purpose, public API behavior, and usage examples. Keep it current when a
change affects those topics.

## Communication Style

Keep updates and final responses short and concise. Use simple English. Prefer clear
fragments when shorter; sacrifice grammar for concision.

## Build, Test, and Development Commands

Use Python 3.13 and [`uv`](https://docs.astral.sh/uv/) with the committed `uv.lock`.

- `uv sync` installs the package and development dependencies.
- `make format` formats the repository with Ruff.
- `make lint` applies Ruff's safe fixes and runs `ty check`.
- `make test` runs pytest with branch coverage.
- `uv build` creates source and wheel distributions in `dist/`.

Before opening a pull request, mirror CI with `uv run -- ruff format --check .`, `uv run -- ruff check .`, `uv run -- ty check .`, and `uv run -- pytest . --cov`.

## Coding Style & Naming Conventions

Follow standard Python naming: `snake_case` for functions and modules, `PascalCase` for classes, and leading underscores for internal APIs. Ruff targets Python 3.13, uses four-space indentation and double quotes, and sorts imports. Add type annotations to public and internal interfaces; this codebase uses modern syntax such as `type` aliases and PEP 695 type parameters. Export intended public symbols through `yggdrasyl/__init__.py` and its `__all__` list.

## Testing Guidelines

Write pytest tests as `test_<behavior>` functions in `tests/test_*.py`. Use fixtures for isolated `Dependencies` instances and `pytest.raises` for error behavior. Async tests run automatically through `pytest-asyncio`. Coverage is configured for 100% branch coverage, so exercise success paths, failures, and state restoration.

## Commit & Pull Request Guidelines

History favors short, lowercase subjects such as `fix minor issues`, `upd README.md`, and `feat[#0]: add base container`. Keep each commit focused and use an issue reference when applicable. Pull requests should explain the behavior change, link relevant issues, note API or typing impacts, and include the commands run. Include screenshots when they clarify rendered documentation changes.
