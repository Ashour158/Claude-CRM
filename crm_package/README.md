# CRM Package - Domain-Centric Architecture

This package provides a clean, modular structure for the CRM system organized by domain concerns with built-in multi-tenancy support.

## 🏗️ Architecture Overview

The CRM package follows a **domain-centric** organization where each business domain (accounts, contacts, leads, etc.) is a self-contained module with clear responsibilities:

- **Models**: Data structure definitions
- **Services**: Business logic and write operations
- **Selectors**: Data retrieval and read operations
- **API**: REST endpoints and serializers
- **Tests**: Domain-specific test suites

## 📦 Package Structure

```
crm_package/
├── core/                    # Core functionality
│   ├── tenancy/            # Multi-tenancy support
│   │   ├── context.py      # ContextVar-based tenant storage
│   │   ├── middleware.py   # Request-level tenant resolution
│   │   ├── mixins.py       # TenantOwnedModel abstract base
│   │   └── selectors.py    # Tenant access helpers
│   ├── exceptions.py       # Custom exceptions
│   └── constants.py        # System-wide constants
│
├── accounts/               # Account management domain
├── contacts/               # Contact management domain
├── leads/                  # Lead tracking domain
├── deals/                  # Sales pipeline domain
├── activities/             # Task & activity domain
├── products/               # Product catalog domain
├── marketing/              # Marketing automation domain
├── vendors/                # Vendor management domain
├── sales/                  # Sales operations domain
├── workflow/               # Workflow automation domain
├── territories/            # Territory management domain
├── system/                 # System configuration
├── shared/                 # Shared utilities
│   ├── utils/             # General utilities
│   ├── enums/             # Enumeration types
│   ├── mixins/            # Reusable mixins
│   └── validators/        # Custom validators
└── api_router.py          # Centralized API routing
```

## 🚀 Key Features

### 1. Multi-Tenancy (Row-Level)

Built-in support for row-level multi-tenancy using organization foreign keys:

```python
from crm_package.core.tenancy import (
    get_current_organization_id,
    set_current_organization_id,
    TenantOwnedModel
)

# Get current organization from context
org_id = get_current_organization_id()

# Models automatically filter by organization
class Account(TenantOwnedModel):
    name = models.CharField(max_length=255)
    # organization FK added automatically
```

### 2. Service/Selector Pattern

**Services** handle business logic and write operations:

```python
from crm_package.accounts.services import create_account

# Business logic is encapsulated
account = create_account(
    name="ACME Corp",
    owner_id=user.id,
    industry="Technology"
)
```

**Selectors** handle data retrieval with optimized queries:

```python
from crm_package.accounts.selectors import list_accounts, get_account_by_id

# Queries are optimized and tenant-filtered
accounts = list_accounts(filters={'industry': 'Technology'})
account = get_account_by_id(account_id)
```

### 3. Shared Utilities

Common utilities available across all domains:

```python
from crm_package.shared.utils import clean_dict, chunk_list
from crm_package.shared.enums import AccountType, LeadStatus, Priority
from crm_package.shared.validators import validate_phone_number
from crm_package.shared.mixins import TimestampMixin, SoftDeleteMixin

# Use enums for type safety
account_type = AccountType.CUSTOMER

# Validate data
validate_phone_number("+1234567890")

# Utility functions
data = clean_dict({'a': 1, 'b': None})  # {'a': 1}
```

## 📖 Usage Guide

### Importing Modules

```python
# Import domain modules
from crm_package.accounts import services as account_services
from crm_package.accounts import selectors as account_selectors

# Import core functionality
from crm_package.core.tenancy import get_current_organization_id
from crm_package.core.exceptions import TenancyException
from crm_package.core.constants import DEFAULT_PAGE_SIZE

# Import shared utilities
from crm_package.shared.utils import clean_dict
from crm_package.shared.enums import Priority
```

### Working with Tenancy

```python
import uuid
from crm_package.core.tenancy import (
    get_current_organization_id,
    set_current_organization_id,
    clear_current_organization
)

# Set organization context
org_id = uuid.uuid4()
set_current_organization_id(org_id)

# Context is automatically used by selectors
accounts = list_accounts()  # Filtered by org_id

# Clear context when done
clear_current_organization()
```

### Creating Services

```python
# crm_package/accounts/services/__init__.py

from crm_package.core.tenancy import get_current_organization_id
from crm_package.core.exceptions import ValidationError

def create_account(*, name: str, **kwargs):
    """Create account with business validation."""
    
    # Get tenant context
    org_id = get_current_organization_id()
    if not org_id:
        raise TenancyException("No active organization")
    
    # Business validation
    if len(name) < 2:
        raise ValidationError("Name too short")
    
    # Create record
    account = Account.objects.create(
        name=name,
        organization_id=org_id,
        **kwargs
    )
    
    return account
```

### Creating Selectors

```python
# crm_package/accounts/selectors/__init__.py

from crm_package.core.tenancy import get_current_organization_id

def list_accounts(*, filters=None):
    """List accounts with tenant filtering."""
    
    queryset = Account.objects.all()
    
    # Apply tenant filter
    org_id = get_current_organization_id()
    if org_id:
        queryset = queryset.filter(organization_id=org_id)
    
    # Apply additional filters
    if filters:
        queryset = queryset.filter(**filters)
    
    # Optimize query
    return queryset.select_related('owner')
```

## 🎯 Design Principles

### 1. Domain-Centric Organization
Each business domain is self-contained with clear boundaries.

### 2. Separation of Concerns
- **Services**: Business logic, validation, writes
- **Selectors**: Query logic, reads, optimizations
- **API**: HTTP interface, serialization

### 3. Tenant Isolation
Multi-tenancy is built into the foundation, not bolted on later.

### 4. Explicit Dependencies
Import paths clearly show module relationships.

### 5. Testability
Service and selector layers can be tested independently.

## 📝 Migration Status

This package is currently in **Phase 1: Scaffolding**.

### Current State
- ✅ Directory structure created
- ✅ Tenancy scaffolding present (not enabled)
- ✅ Service/selector stubs in place
- ✅ Documentation complete
- ⏳ Models still in legacy flat files
- ⏳ No shims created yet

### Next Steps (Phase 2)
1. Migrate Account model to `crm_package.accounts.models`
2. Create transitional shims for legacy imports
3. Implement actual account services and selectors
4. Update existing code to use new imports

See [docs/ARCHITECTURE_RESTRUCTURE_PLAN.md](../docs/ARCHITECTURE_RESTRUCTURE_PLAN.md) for the complete migration roadmap.

## 🔒 Security Considerations

### Tenant Isolation
- All tenant-owned models must use `TenantOwnedModel`
- Selectors must apply tenant filtering
- Services must validate tenant context
- Middleware validates user access to organizations

### Data Validation
- Use validators from `shared.validators`
- Service layer enforces business rules
- Never bypass service layer for writes

## 🧪 Testing

```python
# Test tenancy context
def test_tenant_context():
    from crm_package.core.tenancy import (
        get_current_organization_id,
        set_current_organization_id
    )
    import uuid
    
    org_id = uuid.uuid4()
    set_current_organization_id(org_id)
    
    assert get_current_organization_id() == org_id

# Test services
def test_create_account():
    from crm_package.accounts.services import create_account
    
    account = create_account(name="Test Corp")
    assert account.name == "Test Corp"

# Test selectors
def test_list_accounts():
    from crm_package.accounts.selectors import list_accounts
    
    accounts = list_accounts(filters={'industry': 'Tech'})
    assert accounts.count() > 0
```

## 📚 Documentation

- [Architecture Restructure Plan](../docs/ARCHITECTURE_RESTRUCTURE_PLAN.md)
- [Tenancy Strategy](../docs/TENANCY_STRATEGY.md)
- [Shims Removal Checklist](../docs/SHIMS_REMOVAL_CHECKLIST.md)

## 🤝 Contributing

### Adding a New Domain Module

1. Create directory structure:
   ```
   crm_package/newdomain/
   ├── __init__.py
   ├── apps.py
   ├── models/
   ├── services/
   ├── selectors/
   ├── api/
   └── tests/
   ```

2. Follow the service/selector pattern
3. Use `TenantOwnedModel` for tenant-owned entities
4. Add URL patterns to `api_router.py`
5. Write comprehensive tests

### Code Review Checklist

- [ ] Imports use `crm_package.*` not legacy paths
- [ ] Services used for write operations
- [ ] Selectors used for read operations
- [ ] Tenant filtering applied where applicable
- [ ] Tests added for new functionality
- [ ] Documentation updated

## 📊 Comparison with Commercial CRMs

This architecture aligns with industry standards:

- **Salesforce**: Objects ↔ Our domain modules
- **HubSpot**: Tools ↔ Our domain modules
- **Dynamics 365**: Entities ↔ Our domain modules
- **Row-level tenancy**: Standard for SaaS applications

## 📧 Support

For questions or issues with the new architecture:
1. Check documentation in `docs/`
2. Review examples in service/selector stubs
3. Ask in team channel

## 📜 License

[Your License Here]

---

**Version**: 0.1.0 (Phase 1 - Scaffolding)  
**Last Updated**: 2024-01-XX  
**Status**: 🚧 Under Development
