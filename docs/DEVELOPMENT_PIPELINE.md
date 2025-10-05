# Development Pipeline Guide

This document describes the development workflow, tooling, and CI/CD pipeline for the CRM system.

## Table of Contents
- [Overview](#overview)
- [Development Setup](#development-setup)
- [Development Tools](#development-tools)
- [Running Checks Locally](#running-checks-locally)
- [CI/CD Pipeline](#cicd-pipeline)
- [Test Strategy](#test-strategy)
- [Best Practices](#best-practices)

## Overview

The project uses a comprehensive development pipeline with:
- **Linting**: Ruff for code style and quality
- **Type Checking**: Mypy for static type analysis
- **Security Scanning**: Bandit and pip-audit
- **Testing**: Pytest with coverage reporting
- **CI/CD**: GitHub Actions for automated checks

## Development Setup

### Prerequisites
- Python 3.11 or 3.12
- PostgreSQL 15+ (for production)
- Redis 7+ (for caching)
- Git

### Initial Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Claude-CRM
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   make install-dev
   # Or manually:
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your local configuration
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

## Development Tools

### Makefile Commands

The project includes a Makefile with convenient shortcuts:

```bash
make help           # Show all available commands
make install        # Install production dependencies
make install-dev    # Install development dependencies
make format         # Format code with black, isort, and ruff
make lint           # Run ruff linter with auto-fix
make type           # Run mypy type checker
make security       # Run security scans (bandit + pip-audit)
make test           # Run tests with coverage
make test-quick     # Run tests without coverage (faster)
make test-cov       # Generate coverage report
make migrations     # Check for uncommitted migrations
make migrate        # Run database migrations
make check-all      # Run all checks (lint, type, security, test)
make ci             # Run full CI pipeline locally
make clean          # Remove generated files
```

### Ruff (Linting and Formatting)

Ruff is a fast Python linter and formatter.

**Configuration**: `pyproject.toml`

```bash
# Check code
ruff check .

# Auto-fix issues
ruff check . --fix

# Format code
ruff format .
```

**Integrated rules**:
- pycodestyle (E, W)
- pyflakes (F)
- flake8-bugbear (B)
- flake8-comprehensions (C4)
- pyupgrade (UP)
- flake8-django (DJ)
- isort (I)
- pep8-naming (N)
- flake8-bandit (S)

### Mypy (Type Checking)

Mypy provides static type checking.

**Configuration**: `mypy.ini`

```bash
# Run type checker
mypy . --config-file mypy.ini
```

**Current settings**: Relaxed for incremental adoption. See mypy.ini for roadmap to stricter checking.

### Bandit (Security Scanning)

Bandit finds common security issues.

```bash
# Run security scan
bandit -r . -x tests,venv,env,.venv -ll
```

### pip-audit (Dependency Scanning)

Checks for known vulnerabilities in dependencies.

```bash
# Scan dependencies
pip-audit --disable-pip
```

### Pytest (Testing)

**Configuration**: `pyproject.toml` and `pytest.ini`

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_health.py

# Run tests with specific marker
pytest -m smoke
pytest -m "not slow"

# Run and stop at first failure
pytest -x
```

**Test markers**:
- `smoke`: Quick smoke tests
- `integration`: Integration tests
- `unit`: Unit tests
- `api`: API tests
- `slow`: Slow-running tests

## Running Checks Locally

### Before Committing

Always run these checks before committing:

```bash
# Quick check
make lint
make test-quick

# Full check (recommended)
make check-all
```

### Pre-commit Hooks (Optional)

Install pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

Now checks run automatically on `git commit`.

## CI/CD Pipeline

### GitHub Actions Workflow

**File**: `.github/workflows/ci.yml`

The CI pipeline runs on every push and pull request to `main` and `develop` branches.

### Pipeline Jobs

1. **Lint and Format Check**
   - Runs Ruff linter
   - Checks code formatting with black
   - Checks import sorting with isort

2. **Type Check**
   - Runs Mypy type checker
   - Reports type errors (non-blocking initially)

3. **Security Scanning**
   - Runs Bandit for code security issues
   - Runs pip-audit for dependency vulnerabilities

4. **Test Suite**
   - Matrix testing: Python 3.11 and 3.12
   - PostgreSQL and Redis services
   - Runs all tests with coverage
   - Uploads coverage reports as artifacts
   - Checks for uncommitted migrations

### Pipeline Status

All checks must pass (or be marked as allowed to fail) for a PR to be merged.

### Artifacts

- Coverage reports (HTML and XML)
- Test results (JUnit XML)

Available for 30 days after pipeline run.

## Test Strategy

### Test Structure

```
tests/
├── conftest.py          # Pytest configuration and fixtures
├── test_health.py       # System health smoke tests
├── test_migrations.py   # Migration integrity tests
├── test_admin_load.py   # Admin interface tests
├── test_models.py       # Model tests
└── test_api.py          # API tests
```

### Test Categories

1. **Smoke Tests** (`@pytest.mark.smoke`)
   - Quick tests to ensure system basics work
   - Should run in < 5 seconds total
   - Examples: imports, configuration, basic connectivity

2. **Unit Tests** (`@pytest.mark.unit`)
   - Test individual functions/methods
   - No external dependencies
   - Fast and isolated

3. **Integration Tests** (`@pytest.mark.integration`)
   - Test multiple components together
   - May use database/cache
   - Slower but more comprehensive

4. **API Tests** (`@pytest.mark.api`)
   - Test REST API endpoints
   - Authentication, permissions, responses

### Writing Tests

Use the fixtures in `conftest.py`:

```python
import pytest

@pytest.mark.smoke
@pytest.mark.django_db
def test_user_creation(user_factory):
    user = user_factory()
    assert user.email is not None
    assert user.is_active

@pytest.mark.api
def test_api_endpoint(authenticated_api_client):
    response = authenticated_api_client.get('/api/accounts/')
    assert response.status_code == 200
```

### Coverage Goals

- **Current target**: 0% (baseline)
- **Short-term goal**: 60%
- **Long-term goal**: 80%

Update `pyproject.toml` `cov-fail-under` as coverage improves.

## Best Practices

### Code Quality

1. **Follow PEP 8**: Enforced by Ruff
2. **Type hints**: Add gradually, starting with new code
3. **Docstrings**: Document public functions/classes
4. **Keep functions small**: Max complexity 10 (enforced by Ruff)

### Security

1. **Never commit secrets**: Use environment variables
2. **Review Bandit warnings**: Address high-priority issues
3. **Keep dependencies updated**: Run `pip-audit` regularly
4. **Use parameterized queries**: Django ORM handles this

### Testing

1. **Test happy path first**: Then edge cases
2. **One assertion focus per test**: Multiple assertions OK if related
3. **Use factories for test data**: See `conftest.py`
4. **Clean up after tests**: Use fixtures and transactions

### Git Workflow

1. **Create feature branch**: `git checkout -b feature/my-feature`
2. **Make small commits**: Logical, focused changes
3. **Write clear commit messages**: Imperative mood, < 50 chars subject
4. **Run checks before push**: `make check-all`
5. **Create PR**: Fill out template, link issues
6. **Address review feedback**: Make changes, push updates
7. **Squash merge**: Keep main branch clean

### Admin Field Validation

Use the custom management command to check admin configurations:

```bash
# Check all admin configurations
python manage.py check_admin

# Check specific app
python manage.py check_admin --app crm

# Check with fix suggestions
python manage.py check_admin --fix-suggestions --verbose
```

This helps identify and fix the 111 admin field warnings systematically.

## Troubleshooting

### Common Issues

**Import errors during tests**:
- Ensure all dependencies installed: `make install-dev`
- Check DJANGO_SETTINGS_MODULE is set correctly

**Database connection errors**:
- Check PostgreSQL is running
- Verify .env database configuration
- For tests, ensure test database can be created

**Redis connection errors**:
- Check Redis is running: `redis-cli ping`
- Verify REDIS_URL in .env

**Migration conflicts**:
- Run `python manage.py makemigrations --merge`
- Or: `make migrations` to check for issues

### Getting Help

1. Check this documentation
2. Run `make help` for command reference
3. Check CI logs for error details
4. Review test output: `pytest -v`
5. Ask team for help

## Continuous Improvement

### Roadmap

1. **Phase 1** (Current): Basic pipeline, smoke tests
2. **Phase 2**: Increase test coverage to 60%
3. **Phase 3**: Stricter type checking (see mypy.ini)
4. **Phase 4**: Add performance tests
5. **Phase 5**: Add mutation testing

### Metrics to Track

- Test coverage percentage
- Number of type annotations
- Bandit findings (should decrease)
- Build time (should stay < 10 minutes)

### Regular Tasks

- Weekly: Review and update dependencies
- Monthly: Review security scan results
- Quarterly: Evaluate new tools and practices

---

**Last Updated**: 2024-01-XX  
**Maintained By**: Development Team
