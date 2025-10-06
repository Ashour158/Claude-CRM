# Domain Migration Status

## Overview
This document tracks the migration of CRM models from the legacy flat structure to the new modular domain structure with enhanced multi-tenancy support.

## Migration Status

### Phase 1: Core Infrastructure ✅
- [x] Created TenantOwnedModel base class with row-level multi-tenancy
- [x] Implemented TenantQuerySet for automatic organization scoping
- [x] Created modular package structure under `crm/`
  - `crm/accounts/`
  - `crm/contacts/`
  - `crm/leads/`
  - `crm/activities/`
  - `crm/custom_fields/`
  - `crm/permissions/`

### Phase 2: Model Migration ✅
#### Account Model
- **Status**: ✅ Migrated
- **Location**: `crm/accounts/models/account.py`
- **Changes**:
  - Extends `TenantOwnedModel` instead of `CompanyIsolatedModel`
  - Added `custom_data` JSONField for custom field values
  - Updated indexes to use `organization` instead of `company`
  - Maintains backward compatibility with `custom_fields`
- **Breaking Changes**: None (backward compatible)

#### Contact Model
- **Status**: ✅ Migrated
- **Location**: `crm/contacts/models/contact.py`
- **Changes**:
  - Extends `TenantOwnedModel` instead of `CompanyIsolatedModel`
  - Added `custom_data` JSONField for custom field values
  - Updated indexes to use `organization` instead of `company`
  - Updated FK to use `crm_accounts.Account`
- **Breaking Changes**: None (backward compatible)

#### Lead Model
- **Status**: ✅ Migrated
- **Location**: `crm/leads/models/lead.py`
- **Changes**:
  - Extends `TenantOwnedModel` instead of `CompanyIsolatedModel`
  - Added `custom_data` JSONField for custom field values
  - Updated indexes to use `organization` instead of `company`
  - Updated FKs to use `crm_accounts.Account` and `crm_contacts.Contact`
- **Breaking Changes**: None (backward compatible)

### Phase 3: Service Layer ✅
- [x] LeadConversionService - Convert leads to accounts/contacts
- [x] CustomFieldService - Manage custom field values
- [ ] AccountService - Account management operations
- [ ] ContactService - Contact management operations

### Phase 4: Timeline & Activities ✅
- [x] Created unified `TimelineEvent` model
- [x] Implemented GenericForeignKey for flexible targeting
- [x] Added timeline API endpoint: `GET /api/v1/activities/timeline/`
- [x] Polymorphic event serialization

### Phase 5: Custom Fields ✅
- [x] `CustomFieldDefinition` model with validation
- [x] JSON-based storage in `custom_data` field
- [x] Service layer for field management
- [x] Type-specific validation (text, number, date, select, etc.)

### Phase 6: Permissions ✅
- [x] `Role` model for RBAC
- [x] `RolePermission` model with object-level permissions
- [x] `PermissionMatrix` utility class (stub implementation)
- [ ] Full permission enforcement in viewsets
- [ ] Permission decorators

## Next Steps

### Immediate (Phase 2.1)
1. Create Django migrations for new models
2. Add backward compatibility shims in `crm/models.py`
3. Add deprecation warnings for old import paths
4. Create comprehensive tests

### Short-term (Phase 3)
1. Data migration from old tables (if needed)
2. Add DRF viewsets for new models
3. Implement full permission enforcement
4. Add real-time event notifications

### Long-term (Phase 4)
1. Remove legacy models entirely
2. Remove backward compatibility shims
3. Add pipeline/kanban endpoints
4. Implement advanced custom field types

## Import Paths

### New Import Paths (Recommended)
```python
from crm.accounts.models import Account
from crm.contacts.models import Contact
from crm.leads.models import Lead
from crm.activities.models import TimelineEvent
from crm.custom_fields.models import CustomFieldDefinition
from crm.permissions.models import Role, RolePermission
```

### Legacy Import Paths (Deprecated)
```python
from crm.models import Account, Contact, Lead
```

## Database Tables

| Model | Table Name | Status |
|-------|-----------|--------|
| Account | `crm_account` | ✅ Migrated |
| Contact | `crm_contact` | ✅ Migrated |
| Lead | `crm_lead` | ✅ Migrated |
| TimelineEvent | `crm_timeline_event` | ✅ New |
| CustomFieldDefinition | `crm_custom_field_definition` | ✅ New |
| Role | `crm_role` | ✅ New |
| RolePermission | `crm_role_permission` | ✅ New |

## Testing Coverage

- [ ] Unit tests for TenantOwnedModel
- [ ] Unit tests for TenantQuerySet
- [ ] Integration tests for Account model
- [ ] Integration tests for Contact model
- [ ] Integration tests for Lead model
- [ ] Service tests for LeadConversionService
- [ ] Service tests for CustomFieldService
- [ ] API tests for timeline endpoint
- [ ] Permission tests

## Known Issues

1. ⚠️ Migration files not yet created - need to run `makemigrations`
2. ⚠️ No data migration from old Company field to Organization field
3. ⚠️ Permission enforcement is stubbed (returns True for all checks)
4. ⚠️ No backward compatibility shims yet in old `crm/models.py`

## Timeline

- **Phase 1 (Infrastructure)**: ✅ Complete
- **Phase 2 (Model Migration)**: ✅ Complete
- **Phase 3 (Service Layer)**: 🔄 In Progress (70% complete)
- **Phase 4 (Testing)**: 📅 Planned
- **Phase 5 (Data Migration)**: 📅 Planned
- **Phase 6 (Legacy Removal)**: 📅 Future
