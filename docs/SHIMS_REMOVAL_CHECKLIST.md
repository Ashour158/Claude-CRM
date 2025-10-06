# Legacy Shims Removal Checklist

## Overview

This document defines the conditions and process for removing legacy compatibility shims that provide backward compatibility during the architecture migration.

## What are Shims?

Shims are temporary compatibility modules that:
1. Import from legacy file locations
2. Re-export to new package structure
3. Emit deprecation warnings when imported
4. Allow gradual migration without breaking existing code

Example: `crm_accounts_models.py` → shim → `crm.accounts.models`

## Shim Lifecycle

```
Phase 1: Shim Created
  ↓
Phase 2: Legacy code still used, shim active
  ↓
Phase 3: New location used, shim still present
  ↓
Phase 4: All imports updated, tests pass
  ↓
Phase 5: Shim removed, legacy file deleted
```

## Removal Conditions

A shim can be safely removed when **ALL** of the following conditions are met:

### 1. Code Migration Complete ✅

- [ ] All models moved to new location
- [ ] All serializers moved to new location
- [ ] All views/viewsets moved to new location
- [ ] All services implemented
- [ ] All selectors implemented
- [ ] All tests updated

### 2. Import Updates Complete ✅

- [ ] Application code updated (no imports from `crm_*_models.py`)
- [ ] Test code updated
- [ ] Migration files updated (if any)
- [ ] Management commands updated
- [ ] Celery tasks updated (if any)
- [ ] Scripts updated

### 3. Tests Pass ✅

- [ ] Unit tests pass with new imports
- [ ] Integration tests pass
- [ ] E2E tests pass (if applicable)
- [ ] No deprecation warnings in test output
- [ ] Test coverage maintained or improved

### 4. Documentation Updated ✅

- [ ] Import examples in docs use new paths
- [ ] API documentation updated
- [ ] README updated
- [ ] Inline code comments updated

### 5. External Dependencies Checked ✅

- [ ] Frontend code reviewed (no hardcoded paths)
- [ ] External API clients notified (if any)
- [ ] Third-party integrations reviewed
- [ ] CI/CD pipelines updated

### 6. Deprecation Period Elapsed ⏱️

- [ ] Shim has been present for at least 2 release cycles
- [ ] Deprecation warning logged/monitored for usage
- [ ] No recent imports of legacy locations detected

### 7. Team Sign-off ✅

- [ ] All team members aware of removal
- [ ] Code review approved
- [ ] QA tested migration
- [ ] Product owner notified (if user-facing changes)

## Removal Process

### Step 1: Verify Conditions

Run checklist for specific shim:

```bash
# Example: Checking accounts shim
python manage.py check_shim_usage accounts
```

Expected output:
```
Checking shim usage for: accounts
✓ No imports from crm_accounts_models.py
✓ No imports from crm_accounts_serializers.py
✓ No imports from crm_accounts_views.py
✓ All tests passing
✓ No deprecation warnings

Shim safe to remove!
```

### Step 2: Create Removal Branch

```bash
git checkout -b remove-accounts-shim
```

### Step 3: Remove Shim Files

```bash
# Remove shim from new structure
rm crm/accounts/models/legacy_shim.py

# Remove legacy flat files
rm crm_accounts_models.py
rm crm_accounts_serializers.py
rm crm_accounts_views.py
```

### Step 4: Add Import Guard Test

Add test to prevent future use of legacy imports:

```python
# tests/test_no_legacy_imports.py

def test_no_legacy_accounts_imports():
    """Ensure no code imports from legacy accounts files."""
    import os
    import re
    
    legacy_imports = [
        'from crm_accounts_models import',
        'import crm_accounts_models',
        'from crm_accounts_serializers import',
        'from crm_accounts_views import',
    ]
    
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        if any(skip in root for skip in ['.git', 'node_modules', '__pycache__']):
            continue
            
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    content = f.read()
                    for legacy_import in legacy_imports:
                        assert legacy_import not in content, \
                            f"Legacy import found in {filepath}: {legacy_import}"
```

### Step 5: Run Full Test Suite

```bash
# Run all tests
pytest

# Run import guard tests
pytest tests/test_no_legacy_imports.py

# Check for deprecation warnings
pytest -W error::DeprecationWarning
```

### Step 6: Update Changelog

```markdown
## [Version X.Y.Z] - YYYY-MM-DD

### Removed
- Legacy shims for accounts module
  - `crm_accounts_models.py`
  - `crm_accounts_serializers.py`
  - `crm_accounts_views.py`
- All code must now import from `crm.accounts.*`

### Migration Guide
Update imports:
- Old: `from crm_accounts_models import Account`
- New: `from crm_package.accounts.models import Account`
```

### Step 7: Create PR

```bash
git add .
git commit -m "Remove accounts shim - all imports migrated"
git push origin remove-accounts-shim

# Create PR with checklist completed
```

### Step 8: Deploy & Monitor

After PR merged:

1. Deploy to staging
2. Run smoke tests
3. Monitor for import errors
4. Deploy to production
5. Monitor for 48 hours

## Shim Removal Order

Remove shims in order of domain migration completion:

1. **Accounts** (first domain migrated)
2. **Contacts**
3. **Leads**
4. **Deals**
5. **Activities**
6. **Products**
7. **Marketing**
8. **Vendors**
9. **Sales**
10. **Workflow**
11. **Territories**

## Rollback Plan

If issues discovered after shim removal:

### Option 1: Quick Fix (Preferred)
Update remaining code to use new imports.

### Option 2: Revert (If Critical)

```bash
git revert <commit-sha>
git push origin main

# Redeploy previous version
./deploy.sh
```

### Option 3: Hotfix Shim

If revert not possible:

```python
# Temporarily recreate minimal shim
# crm_accounts_models.py
from crm_package.accounts.models import *

# Deploy hotfix
# Fix root cause
# Remove shim again
```

## Monitoring Shim Usage

### Log Deprecation Warnings

```python
# In shim file
import warnings
import logging

logger = logging.getLogger(__name__)

def log_shim_usage():
    import traceback
    stack = traceback.extract_stack()
    caller = stack[-3]  # Get caller location
    
    logger.warning(
        f"Legacy import detected: {caller.filename}:{caller.lineno}",
        extra={
            'shim': 'crm_accounts_models',
            'caller_file': caller.filename,
            'caller_line': caller.lineno,
        }
    )

log_shim_usage()
warnings.warn("Legacy import", DeprecationWarning)
```

### Aggregate Usage Reports

```bash
# Extract from logs
grep "Legacy import detected" logs/app.log | \
  awk '{print $4}' | \
  sort | uniq -c | sort -nr

# Output shows which files still use legacy imports
#   42 accounts/services/old_service.py:15
#    3 deals/views.py:8
#    1 tests/test_legacy.py:22
```

## Per-Shim Status

### Accounts Domain

| File | Status | Notes |
|------|--------|-------|
| `crm_accounts_models.py` | 🟡 Active | Migration in progress |
| `crm_accounts_serializers.py` | 🟡 Active | Migration in progress |
| `crm_accounts_views.py` | 🟡 Active | Migration in progress |

**Removal Target**: Phase 2 completion

### Contacts Domain

| File | Status | Notes |
|------|--------|-------|
| `crm_contacts_models.py` | 🟡 Active | Not yet migrated |
| `crm_contacts_serializers.py` | 🟡 Active | Not yet migrated |
| `crm_contacts_views.py` | 🟡 Active | Not yet migrated |

**Removal Target**: Phase 3 completion

### Leads Domain

| File | Status | Notes |
|------|--------|-------|
| `crm_leads_models.py` | 🟡 Active | Not yet migrated |
| `crm_leads_serializers.py` | 🟡 Active | Not yet migrated |
| `crm_leads_views.py` | 🟡 Active | Not yet migrated |

**Removal Target**: Phase 3 completion

## Success Criteria

Shim removal is successful when:

1. ✅ All automated tests pass
2. ✅ No import errors in production logs
3. ✅ No deprecation warnings in logs
4. ✅ Code coverage maintained
5. ✅ API response times unchanged
6. ✅ Zero customer-facing issues
7. ✅ Team can maintain code without confusion

## Common Issues & Solutions

### Issue: "ModuleNotFoundError"

**Cause**: Code still imports from legacy location

**Solution**:
```bash
# Find remaining imports
grep -r "from crm_accounts_models import" .

# Update to new location
# from crm_accounts_models import Account
# → from crm_package.accounts.models import Account
```

### Issue: "Circular import"

**Cause**: New structure has circular dependency

**Solution**:
- Use `TYPE_CHECKING` for type hints
- Import inside functions for runtime
- Restructure to break cycle

### Issue: Migration file errors

**Cause**: Old migration references legacy models

**Solution**:
```python
# In migration file
# Bad:
from crm_accounts_models import Account

# Good:
Account = apps.get_model('accounts', 'Account')
```

### Issue: Tests import legacy paths

**Cause**: Test fixtures or factories use old imports

**Solution**: Update test imports and fixtures

## Timeline

| Phase | Shims Status | Timeline |
|-------|-------------|----------|
| 1 - Scaffolding | ✅ Created | Week 1 |
| 2 - Accounts Migration | 🟡 Active | Week 2-3 |
| 3 - Contacts/Leads | 🟡 Active | Week 4-5 |
| 4 - API Router | 🟡 Active | Week 6 |
| 5 - Tenancy | 🟡 Active | Week 7-8 |
| 6 - Remaining Domains | 🟡 Active | Week 9-12 |
| 7 - Cleanup | 🔴 All Removed | Week 13 |

## Final Checklist Before Complete Removal

At end of Phase 7, verify:

- [ ] All domain modules migrated
- [ ] All shims removed
- [ ] All legacy flat files deleted
- [ ] Import guard tests added and passing
- [ ] Documentation fully updated
- [ ] No deprecation warnings anywhere
- [ ] Production monitoring clean for 1 week
- [ ] Team trained on new structure
- [ ] Runbook updated

## Celebration 🎉

Once all shims removed:
1. Update architecture status to "Migration Complete"
2. Document lessons learned
3. Share success metrics with team
4. Archive this checklist for reference

---

**Last Updated**: 2024-01-XX (Phase 1 - Scaffolding)
**Next Review**: Phase 2 completion (Accounts migration)
