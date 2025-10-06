# CRM Architecture Restructure Plan

## Overview

This document outlines the phased migration from a flat file structure to a domain-centric, modular architecture with built-in multi-tenancy support (row-level).

## Current State Problems

### Structure Issues
- **Flat file naming**: Files like `crm_accounts_models.py`, `crm_contacts_views.py` scattered at repository root
- **Poor discoverability**: Hard to locate domain logic or understand module boundaries
- **No unified CRM package**: Domain modules exist as separate Django apps without cohesive organization
- **Potential duplication**: `django_core_models.py` vs `django_models_core.py` naming inconsistency
- **Infrastructure mixed with domain code**: Scripts, exploratory frontend code at root level

### Multi-Tenancy Gaps
- SQL scripts present for row-level security but not abstracted into application layer
- No middleware for automatic tenant context management
- No base model abstraction for tenant-owned entities
- Manual tenant filtering scattered throughout codebase

### Scalability Concerns
- No service/selector pattern enforcement
- Direct model access in views
- Hard to enforce access control and tenant boundaries
- Difficult to add new domains or refactor existing ones

## Target Architecture

### New Directory Structure

**Note**: The new package is located at `crm_package/` to avoid conflict with the existing `crm/` Django app. During Phase 2+, we'll consolidate these.

```
crm_package/
├── __init__.py                    # Package root with version info
├── api_router.py                  # Centralized /api/v1/ routing (commented placeholders)
│
├── core/                          # Core functionality
│   ├── __init__.py
│   ├── exceptions.py              # Custom exceptions
│   ├── constants.py               # System-wide constants
│   └── tenancy/                   # Multi-tenancy support
│       ├── __init__.py
│       ├── context.py             # ContextVar-based tenant storage
│       ├── middleware.py          # Tenant resolution middleware (not enabled)
│       ├── mixins.py              # TenantOwnedModel abstract base
│       └── selectors.py           # Tenant access helpers
│
├── accounts/                      # Account domain
│   ├── __init__.py
│   ├── apps.py                    # Django app config
│   ├── models/
│   │   └── __init__.py            # Account models (future)
│   ├── api/
│   │   └── __init__.py            # DRF viewsets/serializers (future)
│   ├── services/
│   │   └── __init__.py            # Business logic layer
│   ├── selectors/
│   │   └── __init__.py            # Data retrieval layer
│   └── tests/
│       └── __init__.py
│
├── contacts/                      # Contact domain (same structure)
├── leads/                         # Lead domain
├── deals/                         # Deal/pipeline domain
├── activities/                    # Activity/task domain
├── products/                      # Product catalog domain
├── marketing/                     # Marketing domain
├── vendors/                       # Vendor management domain
├── sales/                         # Sales/quotes domain
├── workflow/                      # Workflow automation domain
├── territories/                   # Territory management domain
│
├── system/                        # System configuration
│   ├── __init__.py
│   ├── api/
│   ├── services/
│   └── selectors/
│
└── shared/                        # Shared utilities
    ├── __init__.py
    ├── utils/
    ├── enums/
    ├── mixins/
    └── validators/
```

### Key Principles

1. **Domain-Centric Organization**: Each business domain is a self-contained package
2. **Service/Selector Pattern**: 
   - Services = Business logic with side effects (create, update, delete)
   - Selectors = Pure data retrieval (queries, filtering)
3. **Layered Architecture**: API → Services → Selectors → Models
4. **Multi-Tenancy Built-In**: TenantOwnedModel for automatic isolation
5. **Clean Imports**: Clear module boundaries with explicit __init__.py exports

## Migration Phases

### Phase 1: Scaffolding (CURRENT PR) ✅
**Goal**: Create structure without breaking existing functionality

- [x] Create new `crm/` package structure
- [x] Add tenancy scaffolding (context, middleware, mixins)
- [x] Create placeholder service/selector files
- [x] Add transitional shims for legacy files
- [x] Document architecture and tenancy strategy
- [x] Ensure CI remains green

**Deliverables**:
- Complete directory skeleton
- Tenancy modules (non-enforcing)
- Documentation files
- Legacy shims with deprecation warnings

**Breaking Changes**: NONE

### Phase 2: Migrate Accounts Module
**Goal**: Fully migrate one domain as proof of concept

Tasks:
- [ ] Move Account model from `crm_accounts_models.py` to `crm/accounts/models/`
- [ ] Apply TenantOwnedModel mixin (add organization FK)
- [ ] Move serializers to `crm/accounts/api/`
- [ ] Move views to `crm/accounts/api/`
- [ ] Implement account services (create, update, delete)
- [ ] Implement account selectors (list, get with filtering)
- [ ] Update imports throughout codebase
- [ ] Write migration tests
- [ ] Update shim to import from new location
- [ ] Remove `crm_accounts_*` files from root

**Breaking Changes**: Import paths change (handled by shims initially)

### Phase 3: Migrate Contacts & Leads
**Goal**: Expand pattern to two more domains

Tasks:
- [ ] Migrate Contact model and components
- [ ] Migrate Lead model and components
- [ ] Update all imports
- [ ] Remove corresponding shims
- [ ] Add integration tests

### Phase 4: Unified API Router
**Goal**: Establish /api/v1/ routing standard

Tasks:
- [ ] Uncomment accounts routes in api_router.py
- [ ] Uncomment contacts routes
- [ ] Uncomment leads routes
- [ ] Create DRF routers for each domain
- [ ] Update frontend to use /api/v1/ paths
- [ ] Deprecate old API paths

### Phase 5: Apply Tenancy to Migrated Domains
**Goal**: Enable tenant filtering on migrated models

Tasks:
- [ ] Add organization FK to Account, Contact, Lead
- [ ] Create data migration for existing records
- [ ] Enable TenancyMiddleware in settings
- [ ] Update selectors to use tenant filtering
- [ ] Add tenant validation in services
- [ ] Write tenancy integration tests

### Phase 6: Remaining Domains
**Goal**: Complete migration of all domain modules

Tasks:
- [ ] Migrate Deals
- [ ] Migrate Activities
- [ ] Migrate Products
- [ ] Migrate Marketing
- [ ] Migrate Vendors
- [ ] Migrate Sales
- [ ] Migrate Workflow
- [ ] Migrate Territories

### Phase 7: Cleanup & Enforcement
**Goal**: Remove legacy code and add safeguards

Tasks:
- [ ] Remove all shim files
- [ ] Remove legacy flat files from root
- [ ] Add import guard test (fail on legacy imports)
- [ ] Update all documentation
- [ ] Enable mandatory service layer for writes
- [ ] Add code review checklist

## Architectural Patterns

### Service Layer Pattern

Services encapsulate business logic and coordinate operations across models.

```python
# crm/accounts/services/__init__.py

from crm_package.core.tenancy import get_current_organization_id
from crm_package.core.exceptions import NoActiveOrganization

def create_account(*, name: str, owner_id, **kwargs):
    """
    Create a new account with business validation.
    
    Args:
        name: Account name (required)
        owner_id: User who owns this account
        **kwargs: Additional fields
        
    Returns:
        Account: Created account instance
    """
    from crm_package.accounts.models import Account
    
    # Get tenant context
    org_id = get_current_organization_id()
    if not org_id:
        raise NoActiveOrganization()
    
    # Business validation
    if not name or len(name) < 2:
        raise ValidationError("Account name must be at least 2 characters")
    
    # Create with automatic tenant association
    account = Account.objects.create(
        name=name,
        owner_id=owner_id,
        organization_id=org_id,
        **kwargs
    )
    
    # Business logic: Create default contact?
    # Send notifications?
    
    return account
```

### Selector Layer Pattern

Selectors are pure data retrieval functions with optimized queries.

```python
# crm/accounts/selectors/__init__.py

def list_accounts(*, filters=None):
    """
    List accounts with tenant isolation and optimization.
    
    Args:
        filters: Optional dict of filter criteria
        
    Returns:
        QuerySet[Account]: Filtered and optimized queryset
    """
    from crm_package.accounts.models import Account
    from crm_package.core.tenancy import get_current_organization_id
    
    queryset = Account.objects.all()
    
    # Apply tenant filtering
    org_id = get_current_organization_id()
    if org_id:
        queryset = queryset.filter(organization_id=org_id)
    
    # Apply additional filters
    if filters:
        if 'account_type' in filters:
            queryset = queryset.filter(account_type=filters['account_type'])
        if 'industry' in filters:
            queryset = queryset.filter(industry=filters['industry'])
    
    # Optimize query
    return queryset.select_related('owner', 'territory').prefetch_related('contacts')
```

### API Layer Pattern

API views use services for writes and selectors for reads.

```python
# crm/accounts/api/__init__.py

from rest_framework import viewsets, status
from rest_framework.response import Response

from crm_package.accounts.services import create_account, update_account
from crm_package.accounts.selectors import list_accounts, get_account_by_id

class AccountViewSet(viewsets.ViewSet):
    """Account API endpoints."""
    
    def list(self, request):
        """List accounts with filtering."""
        accounts = list_accounts(filters=request.query_params)
        serializer = AccountSerializer(accounts, many=True)
        return Response(serializer.data)
    
    def create(self, request):
        """Create new account via service."""
        serializer = AccountSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        account = create_account(**serializer.validated_data)
        return Response(
            AccountSerializer(account).data,
            status=status.HTTP_201_CREATED
        )
```

## Benefits of New Architecture

### Discoverability
- Clear domain boundaries
- Standard structure across all domains
- Easy to find models, services, selectors for any domain

### Maintainability
- Service layer enforces business rules
- Selector layer optimizes queries in one place
- Changes to a domain contained within its package

### Testability
- Services can be unit tested without database
- Selectors test query optimization
- API layer tests integration

### Scalability
- Easy to add new domains
- Clear patterns for new features
- Service layer prevents database access sprawl

### Multi-Tenancy
- Automatic tenant filtering via middleware
- TenantOwnedModel ensures data isolation
- Centralized tenant context management

### Team Collaboration
- Clear ownership boundaries
- Reduced merge conflicts
- Standard patterns reduce cognitive load

## Migration Guidelines

### For Developers

1. **When adding new code**: Use new structure, even if domain not fully migrated
2. **When modifying existing code**: Consider migrating that component
3. **Always use services for writes**: Never call `.create()` or `.save()` directly in views
4. **Always use selectors for reads**: Encapsulate query logic
5. **Import from new locations**: Use `crm.accounts.models` not `crm_accounts_models`

### Code Review Checklist

- [ ] Imports use new package structure
- [ ] Services used for create/update/delete operations
- [ ] Selectors used for queries
- [ ] Tenant filtering applied where applicable
- [ ] Tests added for new functionality
- [ ] Documentation updated if public API changed

## Comparison with Commercial CRMs

### Salesforce Architecture
- **Objects**: Similar to our domain modules (Account, Contact, etc.)
- **Triggers/Workflows**: Similar to our service layer
- **SOQL**: Similar to our selector layer
- **Multi-Tenancy**: Org-level isolation, we use organization FK

### HubSpot Architecture
- **Tools**: Marketing, Sales, Service tools = our domain modules
- **Workflows**: Automation similar to our workflow domain
- **Custom Properties**: Our system/custom fields

### Dynamics 365
- **Entities**: Domain modules
- **Plugins**: Service layer pattern
- **Retrieving Data**: Similar to selectors
- **Business Units**: Our organization/tenant model

## Success Metrics

### Phase 1 (Scaffolding)
- ✅ All directories created
- ✅ Tenancy modules present
- ✅ Documentation complete
- ✅ CI remains green
- ✅ No runtime errors

### Phase 2+ (Migration)
- All imports updated to new locations
- Test coverage maintained or improved
- API response times maintained or improved
- Zero data loss during tenant migration
- All shims removed by Phase 7

## Timeline Estimate

- **Phase 1 (Scaffolding)**: 1 day ✅ (Current PR)
- **Phase 2 (Accounts)**: 3-5 days
- **Phase 3 (Contacts/Leads)**: 4-6 days
- **Phase 4 (API Router)**: 2-3 days
- **Phase 5 (Tenancy)**: 5-7 days
- **Phase 6 (Remaining)**: 10-15 days
- **Phase 7 (Cleanup)**: 2-3 days

**Total**: ~4-6 weeks of focused development

## Questions & Answers

**Q: Why not migrate everything at once?**
A: Phased approach reduces risk, allows learning from early phases, and keeps system running.

**Q: What if we need to add a feature during migration?**
A: Add to new structure even if domain not fully migrated. Accelerate that domain's migration.

**Q: How do we handle database migrations?**
A: Phase 5 includes data migration for adding organization FK. Migrations run incrementally per domain.

**Q: What about the existing `crm` directory?**
A: It stays as-is for now. New structure is in `crm/` package. Once migration complete, consolidate.

## Related Documentation

- [TENANCY_STRATEGY.md](./TENANCY_STRATEGY.md) - Row-level tenancy implementation details
- [SHIMS_REMOVAL_CHECKLIST.md](./SHIMS_REMOVAL_CHECKLIST.md) - Conditions for removing legacy code

## Changelog

- **2024-01-XX**: Phase 1 scaffolding completed
- **TBD**: Future phases as completed
