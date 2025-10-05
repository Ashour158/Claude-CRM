# Test Suite

This directory contains the test suite for the CRM system.

## Structure

```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── test_health.py           # System health smoke tests (17 tests)
├── test_migrations.py       # Migration integrity tests (8 tests)
├── test_admin_load.py       # Admin interface tests (11 tests)
├── test_models.py           # Model unit tests (existing)
├── test_api.py              # API integration tests (existing)
└── README.md                # This file
```

## Running Tests

### All Tests
```bash
make test
# Or:
pytest
```

### Smoke Tests Only
```bash
pytest -m smoke
```

### Specific Test File
```bash
pytest tests/test_health.py
```

### With Coverage
```bash
make test-cov
# Or:
pytest --cov=. --cov-report=html
```

### Quick Tests (no coverage)
```bash
make test-quick
# Or:
pytest -x --tb=short
```

## Test Categories

Tests are organized using pytest markers:

- **smoke**: Quick tests ensuring basic functionality (< 5s total)
- **unit**: Test individual functions/methods in isolation
- **integration**: Test multiple components together
- **api**: Test REST API endpoints
- **slow**: Tests that take longer to run
- **django_db**: Tests that require database access

### Running by Category

```bash
# Only smoke tests
pytest -m smoke

# Skip slow tests
pytest -m "not slow"

# Only API tests
pytest -m api

# Unit and smoke tests
pytest -m "unit or smoke"
```

## New Test Files

### test_health.py

System health checks ensuring Django can start and basic functionality works:

- Django settings configured
- System checks pass
- Core app imports work
- Database connection available
- All installed apps loadable
- Middleware configured
- Authentication configured
- Cache working
- Logging configured
- URLs configured

**Purpose**: Catch configuration errors and import issues early

### test_migrations.py

Migration integrity checks:

- No missing migrations (models in sync)
- Migrations can be applied
- No migration conflicts
- Migration naming conventions
- All apps have migrations

**Purpose**: Ensure database schema stays in sync with models

### test_admin_load.py

Django admin interface checks:

- Admin site exists
- Admin autodiscovery completes
- Models registered with admin
- Admin field configurations valid
- Admin URLs configured
- Admin templates available

**Purpose**: Catch admin configuration errors (list_display, search_fields, etc.)

## Test Fixtures

Available fixtures (from conftest.py):

```python
# Basic fixtures
user                      # Create a test user
company                   # Create a test company
user_with_company         # User with company access

# API fixtures
api_client               # Unauthenticated API client
authenticated_api_client # Authenticated API client

# CRM fixtures
account                  # Test account
contact                  # Test contact
lead                     # Test lead
deal                     # Test deal
activity                 # Test activity
task                     # Test task
product                  # Test product

# Batch fixtures
multiple_accounts        # 5 test accounts
multiple_contacts        # 5 test contacts
multiple_leads           # 5 test leads
sample_crm_data         # Complete test dataset

# Utility fixtures
temp_media_dir          # Temporary media directory
mock_cache              # Mocked cache
mock_email_backend      # Mocked email
```

## Writing Tests

### Basic Test Structure

```python
import pytest

@pytest.mark.smoke
@pytest.mark.django_db
def test_something(user, company):
    """Test description."""
    # Arrange
    expected = "value"
    
    # Act
    result = do_something(user, company)
    
    # Assert
    assert result == expected
```

### API Test Example

```python
@pytest.mark.api
def test_api_endpoint(authenticated_api_client):
    """Test API endpoint."""
    response = authenticated_api_client.get('/api/accounts/')
    assert response.status_code == 200
    assert len(response.data) >= 0
```

### Using Factories

```python
from tests.conftest import UserFactory, AccountFactory

@pytest.mark.unit
@pytest.mark.django_db
def test_with_factory(company):
    """Test using factories."""
    # Create 5 users
    users = UserFactory.create_batch(5, company=company)
    
    # Create account
    account = AccountFactory(company=company, owner=users[0])
    
    assert account.owner in users
```

## Best Practices

1. **One test, one assertion focus**: Multiple assertions OK if testing same thing
2. **Use descriptive names**: `test_user_cannot_access_other_company_data`
3. **Use markers**: Help organize and filter tests
4. **Clean up**: Use fixtures and transactions (automatic)
5. **Avoid test interdependence**: Each test should be independent
6. **Test edge cases**: Not just happy path
7. **Use factories**: Don't create test data manually
8. **Document complex tests**: Use docstrings

## Coverage

### Current Coverage
Run `make test-cov` to see current coverage statistics.

Coverage report will be in `htmlcov/index.html`.

### Coverage Goals
- **Baseline**: 0% (starting point)
- **Short-term**: 60%
- **Long-term**: 80%

### Improving Coverage
1. Run coverage report: `make test-cov`
2. Open `htmlcov/index.html` in browser
3. Identify uncovered code
4. Write tests for critical paths first
5. Gradually increase coverage

## Known Issues

See `KNOWN_ISSUES.md` in the root directory for:
- Pre-existing bugs that affect tests
- Workarounds implemented in conftest.py
- Recommended fixes

## Continuous Integration

Tests run automatically on:
- Every push to main/develop
- Every pull request

CI runs:
1. Linting (ruff)
2. Type checking (mypy)
3. Security scanning (bandit, pip-audit)
4. Tests with coverage

See `.github/workflows/ci.yml` for details.

## Troubleshooting

### ImportError
- Ensure all dependencies installed: `make install-dev`
- Check DJANGO_SETTINGS_MODULE is set

### Database errors
- Ensure PostgreSQL running (for integration tests)
- Check database credentials in .env

### "Application labels aren't unique"
- Known issue with django_extensions
- Workaround implemented in conftest.py
- See KNOWN_ISSUES.md

### Tests hanging
- Check for infinite loops in code
- Use pytest-timeout if needed: `pytest --timeout=30`

### Redis connection errors
- Some tests skip if Redis unavailable
- Install and start Redis for full test suite

## Resources

- **Pytest docs**: https://docs.pytest.org/
- **Django testing**: https://docs.djangoproject.com/en/4.2/topics/testing/
- **Factory Boy**: https://factoryboy.readthedocs.io/
- **Project docs**: `docs/DEVELOPMENT_PIPELINE.md`

---

**Note**: Tests are designed to work even with pre-existing bugs in the codebase. They skip gracefully when needed and provide informational output about issues found.
