.PHONY: help install install-dev format lint type security test test-quick test-cov migrations migrate check-all ci clean

# Default target
help:
	@echo "Available targets:"
	@echo "  install       - Install production dependencies"
	@echo "  install-dev   - Install development dependencies"
	@echo "  format        - Format code with black and isort"
	@echo "  lint          - Run ruff linter"
	@echo "  type          - Run mypy type checker"
	@echo "  security      - Run security checks (bandit + pip-audit)"
	@echo "  test          - Run all tests with coverage"
	@echo "  test-quick    - Run tests without coverage"
	@echo "  test-cov      - Run tests with coverage report"
	@echo "  migrations    - Check for uncommitted migrations"
	@echo "  migrate       - Run database migrations"
	@echo "  check-all     - Run all checks (lint, type, security, test)"
	@echo "  ci            - Run CI pipeline locally"
	@echo "  clean         - Remove generated files"

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

format:
	@echo "Formatting code with black..."
	black --line-length 100 .
	@echo "Sorting imports with isort..."
	isort --profile black --line-length 100 .
	@echo "Formatting with ruff..."
	ruff format .

lint:
	@echo "Running ruff linter..."
	ruff check . --fix

type:
	@echo "Running mypy type checker..."
	mypy . --config-file mypy.ini || true

security:
	@echo "Running bandit security checks..."
	bandit -r . -x tests,venv,env,.venv -ll -f screen || true
	@echo "Running pip-audit for dependency vulnerabilities..."
	pip-audit --require-hashes --disable-pip || true

test:
	@echo "Running tests with coverage..."
	pytest --cov=. --cov-report=html --cov-report=term-missing --cov-report=xml

test-quick:
	@echo "Running tests without coverage..."
	pytest -x --tb=short

test-cov:
	@echo "Generating coverage report..."
	pytest --cov=. --cov-report=html
	@echo "Coverage report available at htmlcov/index.html"

migrations:
	@echo "Checking for uncommitted migrations..."
	python manage.py makemigrations --dry-run --check

migrate:
	@echo "Running database migrations..."
	python manage.py migrate

check-all: lint type security test migrations
	@echo "All checks completed!"

ci: install-dev lint type security test migrations
	@echo "CI pipeline completed!"

clean:
	@echo "Cleaning generated files..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.coverage" -delete
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage coverage.xml test-results.xml
	@echo "Clean complete!"
