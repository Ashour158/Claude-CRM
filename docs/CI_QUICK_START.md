# CI Pipeline Quick Start Guide

This guide will help you get started with the new CI pipeline and development tools.

## For Developers: First Time Setup

### 1. Clone and Install

```bash
# Clone repository
git clone <repository-url>
cd Claude-CRM

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
make install-dev
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your local settings
nano .env  # or use your preferred editor
```

### 3. Setup Database

```bash
# Create logs directory
mkdir -p logs

# Run migrations
make migrate

# Create superuser
python manage.py createsuperuser
```

### 4. Verify Setup

```bash
# Run all checks
make check-all
```

If everything passes, you're ready to develop!

## Daily Workflow

### Before Starting Work

```bash
# Pull latest changes
git pull origin main

# Update dependencies (if requirements changed)
make install-dev

# Run migrations (if new migrations)
make migrate
```

### While Developing

```bash
# Auto-format your code
make format

# Check for issues
make lint

# Run tests quickly
make test-quick
```

### Before Committing

```bash
# Run all checks
make check-all

# If all pass, commit and push
git add .
git commit -m "Your descriptive message"
git push
```

## Common Tasks

### Running Tests

```bash
# All tests with coverage
make test

# Quick tests (no coverage)
make test-quick

# Only smoke tests
pytest -m smoke

# Specific test file
pytest tests/test_health.py

# Single test
pytest tests/test_health.py::test_django_settings_configured
```

### Code Quality

```bash
# Auto-format code
make format

# Check code style
make lint

# Check types
make type

# Run security scans
make security
```

### Admin Field Issues

```bash
# Check all admin configurations
python manage.py check_admin

# Check specific app
python manage.py check_admin --app crm

# Get fix suggestions
python manage.py check_admin --fix-suggestions --verbose
```

### Database

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
make migrate

# Check for missing migrations
make migrations
```

## Understanding CI Pipeline

### What Happens on Push/PR?

When you push code or create a PR, GitHub Actions automatically:

1. **Lint Check** (2-3 min)
   - Runs Ruff linter
   - Checks code formatting
   - Checks import sorting

2. **Type Check** (3-4 min)
   - Runs Mypy type checker
   - Reports type errors

3. **Security Scan** (2-3 min)
   - Runs Bandit (code security)
   - Runs pip-audit (dependency vulnerabilities)

4. **Test Suite** (5-8 min)
   - Tests on Python 3.11 and 3.12
   - Runs with PostgreSQL and Redis
   - Generates coverage reports
   - Checks for missing migrations

**Total Time**: ~15-20 minutes

### Viewing CI Results

1. Go to your PR on GitHub
2. Scroll to the bottom for "Checks"
3. Click on any failed check to see details
4. Review the logs for specific errors

### CI is Passing but Local Fails?

Common causes:
- Different Python version (use 3.11 or 3.12)
- Missing dependencies (`make install-dev`)
- Database not configured
- Redis not running

## Troubleshooting

### "No module named X"

```bash
# Reinstall dependencies
make install-dev
```

### "Application labels aren't unique"

This is a known issue with django_extensions. See `KNOWN_ISSUES.md`.

**Quick fix**: Set `DEBUG=False` in .env (but lose debug toolbar)

### Tests Failing Locally

```bash
# Clean and retry
make clean
make install-dev
make test
```

### Ruff/Mypy Not Found

```bash
# Ensure dev dependencies installed
pip install -r requirements-dev.txt
```

### Make Command Not Found

If `make` is not available:

```bash
# On Windows: Install from Chocolatey
choco install make

# Or use commands directly:
pip install -r requirements-dev.txt
ruff check . --fix
pytest
```

## Best Practices

### Commit Messages

```bash
# Good
git commit -m "Add user authentication tests"
git commit -m "Fix login API endpoint validation"
git commit -m "Update README with deployment instructions"

# Bad
git commit -m "fix"
git commit -m "updates"
git commit -m "wip"
```

### Branch Naming

```bash
# Feature branches
git checkout -b feature/user-notifications
git checkout -b feature/export-reports

# Bug fixes
git checkout -b fix/login-redirect
git checkout -b fix/email-validation

# Improvements
git checkout -b improve/query-performance
git checkout -b improve/error-messages
```

### Pull Requests

1. Create PR with descriptive title
2. Fill out PR template (if present)
3. Link related issues
4. Wait for CI checks
5. Request review from team
6. Address review feedback
7. Merge when approved and CI passes

## Advanced Usage

### Running CI Locally

```bash
# Full CI pipeline
make ci

# This runs:
# - install-dev
# - lint
# - type
# - security
# - test
# - migrations check
```

### Coverage Reports

```bash
# Generate coverage
make test-cov

# Open in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit
pre-commit install

# Now checks run automatically on commit
```

### Checking Specific Issues

```bash
# Only security issues
make security

# Only type errors
make type

# Only linting
make lint
```

## Getting Help

### Documentation

- **Development Pipeline**: `docs/DEVELOPMENT_PIPELINE.md`
- **Security Hardening**: `docs/SECURITY_HARDENING.md`
- **Known Issues**: `KNOWN_ISSUES.md`
- **Test Guide**: `tests/README.md`

### Command Reference

```bash
# See all available commands
make help
```

### Support

- Create an issue on GitHub
- Ask in team chat
- Check project documentation
- Review CI logs for specific errors

## Next Steps

1. ✅ Complete first time setup (above)
2. ✅ Run `make check-all` successfully
3. ✅ Read `docs/DEVELOPMENT_PIPELINE.md`
4. ✅ Make a small change and push
5. ✅ Watch CI pipeline run
6. ✅ Fix any issues found
7. ✅ Create your first PR

## Helpful Resources

- **Ruff**: https://docs.astral.sh/ruff/
- **Mypy**: https://mypy.readthedocs.io/
- **Pytest**: https://docs.pytest.org/
- **Django Testing**: https://docs.djangoproject.com/en/4.2/topics/testing/
- **GitHub Actions**: https://docs.github.com/en/actions

---

**Questions?** Check `docs/DEVELOPMENT_PIPELINE.md` for detailed information.

**Issues?** See `KNOWN_ISSUES.md` for known problems and workarounds.
