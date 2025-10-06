# Domain Migration Status

## Overview
This document tracks the migration status from the monolithic CRM app structure to the new domain-driven package structure.

## Package Structure

### New Structure (crm/ package)
```
crm/
├── core/
│   └── tenancy/
│       ├── mixins.py       # TenantOwnedModel base class
│       └── managers.py     # TenantQuerySet & TenantManager
├── accounts/
│   ├── models/
│   │   └── account.py      # Account model
│   ├── services/
│   │   └── account_service.py
│   └── selectors/
│       └── account_selector.py
├── contacts/
│   ├── models/
│   │   └── contact.py      # Contact model
│   └── services/
│       └── contact_service.py
├── leads/
│   ├── models/
│   │   └── lead.py         # Lead model
│   ├── services/
│   │   ├── lead_service.py
│   │   └── conversion_service.py
│   └── selectors/
│       └── lead_selector.py
├── activities/
│   ├── models/
│   │   └── activity.py     # TimelineEvent model
│   ├── services/
│   │   └── timeline_service.py
│   └── selectors/
│       └── timeline_selector.py
├── system/
│   ├── models/
│   │   ├── custom_field_definition.py
│   │   ├── role.py
│   │   └── role_permission.py
│   └── services/
│       └── custom_field_service.py
├── permissions/
│   └── evaluator.py        # Permission evaluation logic
└── api/
    ├── views.py            # API endpoints
    └── urls.py             # URL routing
```

## Migration Status

### Completed ✅
- **Core Tenancy Infrastructure**
  - TenantOwnedModel mixin with organization FK, audit fields
  - TenantQuerySet and TenantManager for scoping
  - Automatic created_by/updated_by tracking

- **Domain Models**
  - Account model with tenancy support
  - Contact model with tenancy support
  - Lead model with conversion tracking
  - TimelineEvent model for activity tracking
  - CustomFieldDefinition for extensibility
  - Role and RolePermission models

- **Services & Selectors**
  - AccountService: create/update/soft_delete
  - AccountSelector: get/list/search/statistics
  - ContactService: create/update/create_from_lead
  - LeadService: create/update/calculate_score
  - ConversionService: convert_lead with idempotency
  - TimelineService: record_event and convenience methods
  - TimelineSelector: fetch_timeline with filtering
  - CustomFieldService: validate_and_assign, resolve_display
  - PermissionEvaluator: get_allowed_actions, has_permission

- **API Endpoints**
  - GET /api/v1/activities/timeline/
  - POST /api/v1/leads/convert/

### Pending 🔄
- **Migrations**
  - Generate initial migrations for new apps
  - Apply indexes and constraints
  
- **Testing**
  - Comprehensive test suite
  
- **Admin Integration**
  - Register new models in admin
  
- **Backward Compatibility**
  - Ensure old code paths still work
  - Gradual migration of existing code

## Key Decisions

### 1. Multi-Tenancy Strategy
- **Approach**: Organization FK on all tenant-owned models
- **Isolation**: Enforced at QuerySet level via TenantManager
- **Audit**: Automatic created_by/updated_by tracking via mixin

### 2. Custom Fields
- **Storage**: JSON field on each entity (accounts.custom_fields, leads.custom_fields)
- **Definitions**: Stored in CustomFieldDefinition table
- **Validation**: Handled by CustomFieldService

### 3. Lead Conversion
- **Process**: Lead → Account + Contact + (optional) Deal
- **Idempotency**: Checks if lead already converted before proceeding
- **Timeline**: Records conversion event automatically

### 4. Permissions
- **Model**: Role-based with resource/action granularity
- **Inheritance**: Roles can inherit from parent roles
- **Conditions**: Support for conditions like "own_records_only"

## Next Steps

1. **Generate Migrations**
   ```bash
   python manage.py makemigrations crm.accounts crm.contacts crm.leads crm.activities crm.system
   ```

2. **Run Tests**
   ```bash
   pytest tests/crm/
   ```

3. **Update Admin**
   - Register new models
   - Configure list displays and filters

4. **Frontend Integration**
   - Update API clients to use new endpoints
   - Migrate forms to use new services

## Compatibility Notes

- Old `crm.models` file still exists for backward compatibility
- New models use `crm.accounts.models.Account` import path
- Old imports should be gradually migrated
- Both old and new structures can coexist during migration

## Related Documentation

- [Custom Fields Design](./CUSTOM_FIELDS_DESIGN.md)
- [Permissions Matrix](./PERMISSIONS_MATRIX.md)
- [Lead Conversion Flow](./LEAD_CONVERSION_FLOW.md)
- [Activities Timeline](./ACTIVITIES_TIMELINE.md)
