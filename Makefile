.PHONY: python install sync run test lint format clean

UV ?= uv
PYTHON_VERSION ?= 3.12

python:
	$(UV) python install $(PYTHON_VERSION)

install: python
	$(UV) sync --extra dev

sync:
	$(UV) sync --extra dev

run:
	$(UV) run uvicorn app.main:app --reload

test:
	$(UV) run pytest

lint:
	$(UV) run ruff check app tests
	$(UV) run black --check app tests
	$(UV) run isort --check-only app tests
	$(UV) run mypy app

format:
	$(UV) run ruff check --fix app tests
	$(UV) run black app tests
	$(UV) run isort app tests

clean:
	$(UV) cache clean
	$(UV) run python -c "from pathlib import Path; import shutil; [shutil.rmtree(path, ignore_errors=True) for pattern in ('__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', 'htmlcov') for path in Path('.').rglob(pattern) if path.is_dir()]"
