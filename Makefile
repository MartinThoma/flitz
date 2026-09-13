maint:
	pre-commit autoupdate
	uv lock --upgrade

test:
	uv run pytest

lint:
	uv run ruff check
	uv run ruff format --check
	uv run mypy

docs:
	uv run --group docs sphinx-build docs docs/_build/html

.PHONY: maint test lint docs
