# Known Issues

This file documents pre-existing issues in the codebase that were discovered during CI pipeline setup.

## 1. Duplicate django_extensions in INSTALLED_APPS

**Location**: `config/settings.py`

**Issue**: `django_extensions` is included in both:
- Line 34: `THIRD_PARTY_APPS` list
- Line 350: Conditionally added when `DEBUG=True`

**Impact**: Causes Django to fail with "Application labels aren't unique" error when DEBUG=True

**Workaround**: The test conftest.py (tests/conftest.py) includes a workaround that removes duplicates before calling django.setup()

**Recommended Fix**: Remove line 350 since django_extensions is already in THIRD_PARTY_APPS

```python
# Remove this line (line 350):
INSTALLED_APPS += ['django_extensions']
```

## 2. Import Error in deals/admin.py

**Location**: `deals/admin.py`

**Issue**: Attempting to import `PipelineStage` from `deals.models` but it doesn't exist

```python
# deals/admin.py line 3:
from deals.models import PipelineStage, Deal, DealProduct, DealActivity, DealForecast
```

**Impact**: Prevents Django admin autodiscovery from completing, blocks django.setup()

**Recommended Fix**: Either:
1. Remove `PipelineStage` from the import if it's not needed
2. Add the missing model to deals/models.py
3. Comment out the problematic admin registration until the model is created

## 3. Admin Field Configuration Warnings

**Issue**: Multiple admin classes have invalid field configurations (list_display, search_fields, list_filter)

**Impact**: Django system checks report 111+ warnings

**Detection**: Use the new management command:
```bash
python manage.py check_admin --verbose --fix-suggestions
```

**Recommended Fix**: Systematic review and correction using the check_admin command output

## Testing Strategy

Given these pre-existing issues, the smoke tests are designed to:
1. Work around known issues where possible
2. Skip gracefully when issues prevent testing
3. Provide informational output about issues found
4. Not fail the build for pre-existing problems

The CI pipeline uses `continue-on-error: true` to allow gradual fixing of these issues without blocking development.

## Action Items

Priority order for fixing:

1. **Critical**: Fix duplicate django_extensions (breaks tests)
2. **Critical**: Fix deals/admin.py import error (breaks admin)
3. **High**: Fix admin field warnings using check_admin command
4. **Medium**: Review and update other import issues flagged by Ruff

---

**Note**: These issues were present before CI pipeline implementation and should be addressed in separate PRs to avoid scope creep.
