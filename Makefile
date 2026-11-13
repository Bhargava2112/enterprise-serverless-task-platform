.PHONY: test lint check validate

test:
	python -m pytest -q

lint:
	python -m ruff check src tests

check: lint test

validate:
	sam validate --lint
