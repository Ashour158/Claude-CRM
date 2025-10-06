# Domain Migration Status

## Overview
This document tracks the migration from legacy flat models to the new domain-driven structure with proper tenancy support.

## Migration Status by Entity

| Entity | Legacy Model | New Model Location | Status | Migration Date |
|--------|--------------|-------------------|--------|----------------|
| Account | `crm/models.py::Account` | `crm/accounts/models/account.py` | ✅ Complete | 2025-01-06 |
| Contact | `crm/models.py::Contact` | `crm/contacts/models/contact.py` | ✅ Complete | 2025-01-06 |
| Lead | `crm/models.py::Lead` | `crm/leads/models/lead.py` | ✅ Complete | 2025-01-06 |
| Deal | `deals/models.py::Deal` | `deals/models.py` | 🔄 Legacy (v1) | Pending |
| Activity | `activities/models.py` | `crm/activities/models/activity.py` | ✅ Complete (Timeline) | 2025-01-06 |
| CustomField | `system_config/models.py` | `crm/system/models/custom_field_definition.py` | ✅ Complete | 2025-01-06 |

## Key Changes

### Tenancy Layer
- **Base Model**: All new models extend `TenantOwnedModel` instead of `CompanyIsolatedModel`
- **Auto-filtering**: Queries automatically filter by current organization context
- **Safety**: Cross-org operations are blocked at the model level

### Structural Improvements
- **Package Organization**: Domain entities organized into dedicated packages
  - `crm/accounts/` - Account domain
  - `crm/contacts/` - Contact domain
  - `crm/leads/` - Lead domain
  - `crm/activities/` - Activity/Timeline domain
  - `crm/system/` - System models (custom fields, etc.)
  - `crm/permissions/` - Permission models

- **Service Layer**: Business logic extracted to services
  - `*/services/*_service.py` - Write operations and business logic
  - `*/selectors/*_selector.py` - Read operations and queries

### Database Changes
- **New Tables**: Models use new table names with `_v2` suffix during migration
  - `crm_accounts_v2`
  - `crm_contacts_v2`
  - `crm_leads_v2`
  - `crm_timeline_events`
  - `crm_custom_field_definitions`
  - `crm_roles`
  - `crm_role_permissions`

## Migration Strategy

### Phase 1: Parallel Run (Current)
- ✅ New models defined alongside legacy models
- ✅ New API endpoints created
- ⏳ Legacy endpoints still functional
- ⏳ Data migration scripts needed

### Phase 2: Data Migration
- [ ] Create migration scripts to copy data from legacy tables
- [ ] Validate data integrity
- [ ] Update foreign keys and relationships

### Phase 3: Deprecation
- [ ] Mark legacy endpoints as deprecated
- [ ] Frontend updates to use new endpoints
- [ ] Monitor usage of legacy endpoints

### Phase 4: Cleanup
- [ ] Remove legacy models
- [ ] Drop old tables
- [ ] Update documentation

## Breaking Changes

### API Endpoints
- New endpoint structure under `/api/v1/crm/`
- Timeline events replace individual activity endpoints
- Custom fields now use JSON storage with definitions

### Field Changes
- `company` → `organization` (FK renamed for clarity)
- `custom_fields` → `custom_data` (JSON field for values)
- Email fields: `email` → `primary_email` (for consistency)

## Testing Status

| Test Category | Status | Coverage |
|--------------|--------|----------|
| Account CRUD | ⏳ Pending | 0% |
| Contact CRUD | ⏳ Pending | 0% |
| Lead CRUD | ⏳ Pending | 0% |
| Lead Conversion | ⏳ Pending | 0% |
| Timeline Events | ⏳ Pending | 0% |
| Custom Fields | ⏳ Pending | 0% |
| Permissions | ⏳ Pending | 0% |
| Tenancy | ⏳ Pending | 0% |

## Rollback Plan

If issues arise:
1. Disable new API endpoints via feature flag
2. Restore legacy endpoint routes
3. Investigate and fix issues
4. Re-enable with fixes

## Notes

- Legacy models remain functional during migration
- No data loss risk - running in parallel
- Custom field values stored as JSON (Phase 1 approach)
- Future: May migrate to relational CustomFieldValue table if needed
