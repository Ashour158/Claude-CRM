# CRM Tenancy Strategy - Row-Level Multi-Tenancy

## Overview

This document describes the multi-tenancy strategy for the CRM system using **row-level tenancy** (organization foreign key on models) as the foundation for data isolation.

## Strategy Decision: Row-Level Tenancy

### Chosen Approach
**Row-level (shared database, shared schema)** with organization/company foreign key on all tenant-owned tables.

### Why Row-Level?

#### Advantages
1. **Simplicity**: Single database, single schema, standard Django ORM
2. **Incremental Adoption**: Can be added gradually to existing models
3. **Cost-Effective**: No per-tenant database/schema overhead
4. **Easier Migrations**: Single schema to migrate
5. **Simpler Backups**: One database to backup/restore
6. **Cross-Tenant Queries**: Super-admin dashboards can query across orgs
7. **Resource Sharing**: Efficient use of database connections and memory

#### Disadvantages & Mitigations
1. **Security Risk**: Improper filtering could leak data
   - **Mitigation**: Middleware + context + base model enforcement
   - **Mitigation**: Comprehensive tests for tenant isolation
   - **Mitigation**: Code review checklist for tenant filtering

2. **Performance**: Large table scans if not properly indexed
   - **Mitigation**: Index on organization_id in all tenant-owned tables
   - **Mitigation**: Partition by organization_id for huge tables (future)
   - **Mitigation**: Selector layer encapsulates optimized queries

3. **Noisy Neighbor**: One tenant's heavy usage affects others
   - **Mitigation**: Rate limiting per organization
   - **Mitigation**: Query timeouts
   - **Mitigation**: Resource monitoring by tenant

### Alternatives Considered

#### Schema-Per-Tenant (PostgreSQL Schemas)
**Pros**: Better isolation, easier per-tenant backups
**Cons**: 
- Complex migrations (N schemas × 1 migration)
- Connection pooling complications
- Harder cross-tenant queries
- Database overhead for many tenants

**Decision**: Defer until/unless we exceed ~500 organizations or need strict regulatory compliance.

#### Database-Per-Tenant
**Pros**: Maximum isolation and performance
**Cons**:
- Extreme operational complexity
- Expensive infrastructure
- Very hard to run analytics across tenants

**Decision**: Not suitable for our scale and use case.

## Implementation Architecture

### 1. Tenant Context Management

#### Context Storage
Use Python's `contextvars` to store current organization ID per request.

```python
# crm/core/tenancy/context.py

from contextvars import ContextVar
import uuid

_current_organization_id: ContextVar[Optional[uuid.UUID]] = ContextVar(
    'current_organization_id', default=None
)

def get_current_organization_id() -> Optional[uuid.UUID]:
    return _current_organization_id.get()

def set_current_organization_id(organization_id: Optional[uuid.UUID]):
    _current_organization_id.set(organization_id)
```

**Why ContextVar?**
- Thread-safe and async-safe
- Automatically scoped to request lifecycle
- No global state pollution
- Works with ASGI and WSGI

### 2. Tenant Resolution Middleware

Middleware extracts organization from request and sets context.

```python
# crm/core/tenancy/middleware.py

class TenancyMiddleware:
    def __call__(self, request):
        clear_current_organization()
        
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # Option 1: X-Org-ID header (for API clients)
        org_id = request.headers.get('X-Org-ID')
        
        # Option 2: Session (for web UI)
        if not org_id and 'active_company_id' in request.session:
            org_id = request.session['active_company_id']
        
        # Option 3: User's primary organization
        if not org_id:
            org_id = get_user_primary_organization(request.user)
        
        if org_id:
            # Validate access
            if not user_has_organization_access(request.user, org_id):
                return JsonResponse({'error': 'Access denied'}, status=403)
            
            set_current_organization_id(org_id)
            request.organization_id = org_id
        
        response = self.get_response(request)
        clear_current_organization()
        return response
```

**Resolution Priority**:
1. `X-Org-ID` header (explicit client selection)
2. Session `active_company_id` (user switched orgs)
3. User's primary organization (default)

### 3. Tenant-Owned Model Base

Abstract model that adds organization FK and automatic filtering.

```python
# crm/core/tenancy/mixins.py

class TenantOwnedModel(models.Model):
    organization = models.ForeignKey(
        'core.Company',
        on_delete=models.CASCADE,
        related_name='%(app_label)s_%(class)s_set',
        db_index=True
    )
    
    class Meta:
        abstract = True
        indexes = [models.Index(fields=['organization'])]
    
    def save(self, *args, **kwargs):
        # Auto-set organization from context if not set
        if not self.organization_id:
            org_id = get_current_organization_id()
            if org_id:
                self.organization_id = org_id
        super().save(*args, **kwargs)
```

**Usage**:
```python
class Account(TenantOwnedModel):
    name = models.CharField(max_length=255)
    # organization field automatically added
```

### 4. Selector Pattern with Tenant Filtering

Selectors encapsulate queries with automatic tenant filtering.

```python
# crm/accounts/selectors/__init__.py

def list_accounts(*, filters=None):
    from crm_package.accounts.models import Account
    from crm_package.core.tenancy import get_current_organization_id
    
    queryset = Account.objects.all()
    
    # Apply tenant filtering
    org_id = get_current_organization_id()
    if org_id:
        queryset = queryset.filter(organization_id=org_id)
    
    # Apply other filters
    if filters:
        queryset = queryset.filter(**filters)
    
    return queryset
```

**Benefits**:
- Tenant filtering in one place
- Easy to add query optimization
- Testable without database
- Prevents accidental data leakage

## Data Model Changes

### Organization/Company Model

```python
class Company(BaseModel):
    """Multi-tenant organization/company."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    
    # Settings
    currency = models.CharField(max_length=3, default='USD')
    timezone = models.CharField(max_length=50, default='UTC')
    
    # Status
    is_active = models.BooleanField(default=True)
    subscription_plan = models.CharField(max_length=50)
    subscription_expires_at = models.DateTimeField(null=True)
```

### User-Company Access

```python
class UserCompanyAccess(BaseModel):
    """Many-to-many relationship between users and companies."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    
    # Access control
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False)
    role = models.CharField(max_length=50)  # admin, user, viewer
    
    class Meta:
        unique_together = [['user', 'company']]
```

### Tenant-Owned Models

All business entity models add organization FK:

```python
# Before
class Account(BaseModel):
    name = models.CharField(max_length=255)

# After
class Account(TenantOwnedModel):  # Inherits organization FK
    name = models.CharField(max_length=255)
```

## Security Considerations

### Defense in Depth

Multiple layers of tenant isolation:

1. **Middleware Layer**: Sets tenant context, validates access
2. **Model Layer**: TenantOwnedModel enforces organization FK
3. **Selector Layer**: Automatic filtering in queries
4. **Service Layer**: Validates operations within tenant
5. **API Layer**: Permission classes check tenant access

### Security Checklist

- [ ] All tenant-owned models inherit from TenantOwnedModel
- [ ] All selectors apply tenant filtering
- [ ] Middleware validates user has access to organization
- [ ] Services validate tenant context before operations
- [ ] API endpoints use HasCompanyAccess permission class
- [ ] Tests verify tenant isolation
- [ ] Code review checks tenant filtering

### Audit Logging

Log tenant-switching events:

```python
# When user switches organization
logger.info(
    "User switched organization",
    extra={
        'user_id': user.id,
        'from_org': old_org_id,
        'to_org': new_org_id,
        'ip_address': request.META['REMOTE_ADDR']
    }
)
```

## Performance Optimization

### Indexing Strategy

```sql
-- Every tenant-owned table needs this
CREATE INDEX idx_accounts_organization ON accounts(organization_id);
CREATE INDEX idx_contacts_organization ON contacts(organization_id);
CREATE INDEX idx_deals_organization ON deals(organization_id);
-- ... etc for all tenant-owned tables
```

**Composite Indexes** for common queries:
```sql
-- Frequently filter by org + status
CREATE INDEX idx_accounts_org_status ON accounts(organization_id, status);

-- Date range queries
CREATE INDEX idx_deals_org_created ON deals(organization_id, created_at DESC);
```

### Query Optimization

Always filter by organization first:
```python
# Good - uses organization index
Account.objects.filter(
    organization_id=org_id,
    status='active'
).select_related('owner')

# Bad - full table scan then filter
Account.objects.filter(
    status='active'
).filter(organization_id=org_id)
```

### Partitioning (Future)

For very large tables (millions of rows), consider table partitioning:

```sql
-- PostgreSQL 10+ partitioning by organization
CREATE TABLE accounts (
    id UUID PRIMARY KEY,
    organization_id UUID NOT NULL,
    ...
) PARTITION BY HASH (organization_id);

CREATE TABLE accounts_p0 PARTITION OF accounts
    FOR VALUES WITH (MODULUS 4, REMAINDER 0);
-- ... create 3 more partitions
```

**When to consider**: > 10 million rows in a table

## Migration Path for Existing Data

### Phase 1: Add Organization Column

```python
# Migration
class Migration(migrations.Migration):
    operations = [
        migrations.AddField(
            model_name='account',
            name='organization',
            field=models.ForeignKey(
                'core.Company',
                on_delete=models.CASCADE,
                null=True  # Temporary
            ),
        ),
    ]
```

### Phase 2: Backfill Data

```python
def backfill_organization(apps, schema_editor):
    Account = apps.get_model('accounts', 'Account')
    Company = apps.get_model('core', 'Company')
    
    # Get default company (create if needed)
    default_company, _ = Company.objects.get_or_create(
        code='DEFAULT',
        defaults={'name': 'Default Organization'}
    )
    
    # Assign all accounts to default company
    Account.objects.filter(organization__isnull=True).update(
        organization=default_company
    )

class Migration(migrations.Migration):
    operations = [
        migrations.RunPython(backfill_organization),
    ]
```

### Phase 3: Make Non-Nullable

```python
class Migration(migrations.Migration):
    operations = [
        migrations.AlterField(
            model_name='account',
            name='organization',
            field=models.ForeignKey(
                'core.Company',
                on_delete=models.CASCADE,
                null=False
            ),
        ),
    ]
```

## Testing Strategy

### Tenant Isolation Tests

```python
@pytest.mark.django_db
def test_account_tenant_isolation():
    # Create two organizations
    org1 = Company.objects.create(name='Org 1', code='ORG1')
    org2 = Company.objects.create(name='Org 2', code='ORG2')
    
    # Create accounts in each
    account1 = Account.objects.create(name='Account 1', organization=org1)
    account2 = Account.objects.create(name='Account 2', organization=org2)
    
    # Set org1 context
    set_current_organization_id(org1.id)
    
    # Query should only return org1's accounts
    accounts = list_accounts()
    assert accounts.count() == 1
    assert accounts.first() == account1
    
    # Set org2 context
    set_current_organization_id(org2.id)
    
    # Query should only return org2's accounts
    accounts = list_accounts()
    assert accounts.count() == 1
    assert accounts.first() == account2
```

### Cross-Tenant Leak Tests

```python
def test_cannot_access_other_org_data():
    org1 = Company.objects.create(name='Org 1', code='ORG1')
    org2 = Company.objects.create(name='Org 2', code='ORG2')
    
    account = Account.objects.create(name='Secret', organization=org2)
    
    # Set org1 context
    set_current_organization_id(org1.id)
    
    # Try to access org2's account - should fail
    with pytest.raises(Account.DoesNotExist):
        get_account_by_id(account.id)
```

## Monitoring & Observability

### Metrics to Track

1. **Queries without tenant filter**: Alert if detected
2. **Cross-tenant access attempts**: Log and alert
3. **Query performance by tenant**: Identify slow tenants
4. **Tenant data growth**: Plan for partitioning
5. **User organization switches**: Audit trail

### Logging

```python
# Log tenant context in all operations
logger.info(
    "Account created",
    extra={
        'organization_id': org_id,
        'account_id': account.id,
        'user_id': user.id,
    }
)
```

## Evolution Path

### Current: Row-Level (Phase 1)
- Simplest to implement
- Works for < 1000 organizations
- Single database maintenance

### Future: Hybrid Approach (Phase 2)
If growth requires:
- Large enterprise customers → separate schema
- SMB customers → shared schema (row-level)
- Best of both worlds

### Future: Schema-Per-Tenant (Phase 3)
If regulatory compliance requires:
- Full data isolation per tenant
- Per-tenant backups and restores
- Accept increased operational complexity

## Conclusion

Row-level tenancy provides the right balance of:
- ✅ Development simplicity
- ✅ Operational manageability
- ✅ Cost-effectiveness
- ✅ Incremental adoption path
- ✅ Future flexibility

With proper middleware, base models, and selector patterns, we can ensure robust tenant isolation while maintaining a simple, maintainable codebase.

## References

- [Django Multi-Tenancy Best Practices](https://books.agiliq.com/projects/django-multi-tenant/en/latest/)
- [PostgreSQL Row-Level Security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [contextvars Documentation](https://docs.python.org/3/library/contextvars.html)

## Changelog

- **2024-01-XX**: Initial tenancy strategy document
- **TBD**: Updates as implementation progresses
