# Installation Guide

## Prerequisites

Atlas AI uses Python 3.12 and the [uv](https://docs.astral.sh/uv/) package manager. The repository's `.python-version` file pins the intended interpreter series.

Install uv on Windows with PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Restart the terminal after installation and confirm the tool is available:

```powershell
uv --version
```

## Create the Environment

From the repository root:

```powershell
uv python install 3.12
uv sync --extra dev
```

`uv sync` creates the project-local `.venv`, installs the runtime dependencies, and includes test and quality tooling through the `dev` extra.

## Start the Project

```powershell
uv run uvicorn app.main:app --reload
```

Or use Make:

```powershell
make install
make run
```

## Common Development Commands

```powershell
make test
make lint
make format
make clean
```

## Dependency Changes

Update dependencies in `pyproject.toml`, then run `uv lock` followed by `uv sync --extra dev`. Commit the generated `uv.lock` file so development and deployment use the same resolved dependency versions.
