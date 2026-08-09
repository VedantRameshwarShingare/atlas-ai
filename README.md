# Atlas AI

Atlas AI is a Python-based financial intelligence assistant built around FastAPI, asynchronous services, retrieval workflows, and capability-driven automation.

## Architecture Overview

The project separates interface, orchestration, capabilities, services, persistence, and background-work concerns. API and Telegram interfaces call application orchestration; capabilities coordinate domain work; services integrate external providers; repositories persist application data. Background jobs and monitoring remain isolated modules.

## Folder Structure

```text
app/                 Application packages
  ai/                Orchestration and capability abstractions
  api/               FastAPI interface layer
  database/          Database setup and migrations
  models/            Persistence models
  repositories/      Data-access layer
  services/          Provider integrations
  scheduler/         Background scheduling
  monitoring/        Metrics, tracing, and health primitives
tests/               Unit and integration test suites
requirements/        Runtime and development dependency sets
```

## Quick Start

```bash
uv python install 3.12
uv sync --extra dev
make run
```

Copy `.env.example` to `.env` and set the required provider and database values before running integrations.

## Development Setup

Use Python 3.12 or newer. Install development dependencies with `make install`, then use `make test`, `make lint`, and `make format` before opening a change. The project configuration for Ruff, Black, isort, mypy, and pytest lives in `pyproject.toml`.

See the [installation guide](docs/installation.md) for uv setup and environment management.

See [RAG architecture and setup](docs/rag.md) for document ingestion and retrieval configuration.

See [chat API setup](docs/chat.md) for authenticated conversations and provider configuration.
