# Sharing Enforcement Implementation

## Overview

This implementation adds robust record-level sharing enforcement across core CRM entities (Leads, Deals, Accounts, Contacts, Activities) using a layered security model.

## Architecture

### Layered Security Model

The sharing enforcement follows a **layered approach** with three levels:

1. **Ownership** - User owns the record (via `owner_id` or `user_id` field)
2. **Predicate-based Rules** - SharingRule with automatic predicate matching (OR semantics)
3. **Explicit Shares** - RecordShare entries granting specific users access
4. **Default Deny** - If none of the above match, access is denied (empty queryset)

### Components

#### 1. Data Models (`sharing/models.py`)

**SharingRule**
- Company-scoped rules for automatic record access
- JSON predicate format: `{'field': 'status', 'operator': 'eq', 'value': 'qualified'}`
- Supports read_only and read_write access levels
- Can be activated/deactivated without deletion

**RecordShare**
- Explicit record-level sharing
- Direct user-to-record access grants
- Includes optional reason field for audit trail
- Unique constraint on (company, object_type, object_id, user)

#### 2. Predicate Evaluation Engine (`sharing/predicate.py`)

Supports the following operators:
- `eq` - Equal to
- `ne` - Not equal to
- `in` - In list
- `nin` - Not in list
- `contains` - String contains (case-sensitive)
- `icontains` - String contains (case-insensitive)
- `gt` - Greater than
- `gte` - Greater than or equal to
- `lt` - Less than
- `lte` - Less than or equal to

Converts JSON predicates to Django Q objects with proper validation.

#### 3. Enforcement Engine (`sharing/enforcement.py`)

**SharingEnforcer** class provides:
- `enforce_sharing()` - Filters querysets based on all three layers
- `can_user_access_record()` - Checks if user can access a specific record
- Default deny behavior when no access is granted

#### 4. DRF Integration (`sharing/mixins.py`)

**SharingEnforcedViewMixin** provides:
- Automatic queryset filtering in ViewSets
- Configuration via class attributes:
  - `sharing_object_type` - Type of object (required)
  - `sharing_ownership_field` - Field for ownership check (default: 'owner')
- Optional Prometheus metrics tracking

#### 5. Admin APIs (`sharing/views.py`, `sharing/serializers.py`)

**SharingRuleViewSet**
- CRUD operations for sharing rules
- Activate/deactivate actions
- Automatically scoped to user's active company

**RecordShareViewSet**
- CRUD operations for explicit shares
- Bulk create and bulk delete actions
- Automatically scoped to user's active company

#### 6. Management Command (`sharing/management/commands/seed_sharing_rules.py`)

Seeds example sharing rules:
```bash
python manage.py seed_sharing_rules [--company-code CODE]
```

Creates:
- Example rule: Qualified/converted leads visible to all
- Example rule: High-value deals (amount >= 10000) visible to all
- Example explicit share (if data exists)

#### 7. Optional Metrics (`sharing/metrics.py`)

Prometheus counter: `sharing_filter_applied_total{object_type}`
- Tracks how often sharing filters are applied
- Gracefully degrades if prometheus_client not installed

## Usage

### 1. Apply to ViewSets

```python
from sharing.mixins import SharingEnforcedViewMixin

class LeadViewSet(SharingEnforcedViewMixin, viewsets.ModelViewSet):
    queryset = Lead.objects.all()
    serializer_class = LeadSerializer
    
    # Sharing configuration
    sharing_object_type = 'lead'
    sharing_ownership_field = 'owner'
```

### 2. Create Sharing Rules

```python
from sharing.models import SharingRule

# Rule: All users can see qualified leads
rule = SharingRule.objects.create(
    company=company,
    name='Qualified Leads Visibility',
    object_type='lead',
    predicate={
        'field': 'status',
        'operator': 'eq',
        'value': 'qualified'
    },
    access_level='read_only',
    is_active=True
)
```

### 3. Create Explicit Shares

```python
from sharing.models import RecordShare

# Share specific lead with user
share = RecordShare.objects.create(
    company=company,
    object_type='lead',
    object_id=lead.id,
    user=target_user,
    access_level='read_only',
    reason='Collaboration on this opportunity'
)
```

### 4. Use Admin API

**List sharing rules:**
```
GET /api/sharing/rules/
```

**Create sharing rule:**
```
POST /api/sharing/rules/
{
  "name": "Hot Leads Visibility",
  "object_type": "lead",
  "predicate": {
    "field": "rating",
    "operator": "eq",
    "value": "hot"
  },
  "access_level": "read_only",
  "is_active": true
}
```

**Activate/deactivate rule:**
```
POST /api/sharing/rules/{id}/activate/
POST /api/sharing/rules/{id}/deactivate/
```

**List record shares:**
```
GET /api/sharing/shares/
GET /api/sharing/shares/?object_type=lead&object_id={uuid}
```

**Create explicit share:**
```
POST /api/sharing/shares/
{
  "object_type": "lead",
  "object_id": "{uuid}",
  "user": "{user_id}",
  "access_level": "read_only",
  "reason": "Collaboration"
}
```

**Bulk create shares:**
```
POST /api/sharing/shares/bulk_create/
{
  "shares": [
    {
      "object_type": "lead",
      "object_id": "{uuid1}",
      "user": "{user_id}",
      "access_level": "read_only"
    },
    {
      "object_type": "deal",
      "object_id": "{uuid2}",
      "user": "{user_id}",
      "access_level": "read_write"
    }
  ]
}
```

## Implementation Status

### Completed ✅
- [x] SharingRule and RecordShare models with migrations
- [x] Predicate evaluation engine with all operators
- [x] Enforcement engine with layered security
- [x] DRF mixin for automatic ViewSet filtering
- [x] Admin APIs for CRUD operations
- [x] Management command for seeding
- [x] Optional Prometheus metrics
- [x] Comprehensive tests (predicate + enforcement)
- [x] Applied to LeadViewSet, AccountViewSet, ContactViewSet
- [x] Applied to DealViewSet, ActivityViewSet

### Entities with Sharing Enforcement
- Lead (ownership field: `owner`)
- Account (ownership field: `owner`)
- Contact (ownership field: `owner`)
- Deal (ownership field: `owner`)
- Activity (ownership field: `assigned_to`)

## Testing

### Run Tests

```bash
# Run all sharing tests
pytest tests/sharing/ -v

# Run predicate tests
pytest tests/sharing/test_predicate.py -v

# Run enforcement tests
pytest tests/sharing/test_enforcement.py -v
```

### Test Coverage

**Predicate Evaluator Tests:**
- All operators (eq, ne, in, nin, contains, icontains, gt, gte, lt, lte)
- Invalid input validation
- Multiple predicates with OR/AND semantics

**Enforcement Tests:**
- Ownership-only visibility
- Rule-based access
- Explicit record share access
- Default deny with no access
- Multiple rules with OR semantics
- Inactive rules ignored
- Individual record access checks

## Security Considerations

1. **Default Deny**: If no ownership, rule, or share matches, access is denied
2. **Company Isolation**: All rules and shares are scoped to company
3. **Active Rules Only**: Inactive rules are not evaluated
4. **OR Semantics**: Multiple rules provide broader access (not restrictive)
5. **Audit Trail**: All rules and shares track created_by and timestamps

## Future Enhancements (Out of Scope)

- Write-level enforcement for read_only access
- Territory or hierarchical role integration
- Negative/deny rules
- Policy-as-code ingestion for sharing rules
- Time-based access expiration
- Conditional sharing based on user attributes

## Migration

To apply the sharing enforcement to the database:

```bash
python manage.py migrate sharing
```

To seed example data:

```bash
python manage.py seed_sharing_rules
```

## API Endpoints

- `GET /api/sharing/rules/` - List sharing rules
- `POST /api/sharing/rules/` - Create sharing rule
- `GET /api/sharing/rules/{id}/` - Get sharing rule
- `PUT /api/sharing/rules/{id}/` - Update sharing rule
- `DELETE /api/sharing/rules/{id}/` - Delete sharing rule
- `POST /api/sharing/rules/{id}/activate/` - Activate rule
- `POST /api/sharing/rules/{id}/deactivate/` - Deactivate rule

- `GET /api/sharing/shares/` - List record shares
- `POST /api/sharing/shares/` - Create record share
- `GET /api/sharing/shares/{id}/` - Get record share
- `PUT /api/sharing/shares/{id}/` - Update record share
- `DELETE /api/sharing/shares/{id}/` - Delete record share
- `POST /api/sharing/shares/bulk_create/` - Bulk create shares
- `DELETE /api/sharing/shares/bulk_delete/` - Bulk delete shares

## Django Admin

Both SharingRule and RecordShare are registered in Django admin at `/admin/` for easy management.

## Metrics

If `prometheus_client` is installed, the system tracks:
- `sharing_filter_applied_total{object_type}` - Counter of sharing filter applications

Gracefully degrades if not installed.
