# Permissions Matrix

## Overview
Role-based permission system controlling access to CRM entities and actions.

## Permission Actions

### Basic CRUD
- `view` - Read access to records
- `create` - Create new records
- `edit` - Modify existing records
- `delete` - Delete/soft-delete records

### Special Actions
- `convert` - Convert leads to contacts/accounts
- `merge` - Merge duplicate records
- `export` - Export data to files
- `import` - Import data from files
- `bulk_update` - Perform bulk operations
- `bulk_delete` - Delete multiple records
- `manage_custom_fields` - Define custom fields
- `manage_permissions` - Manage roles and permissions
- `manage_users` - Manage user accounts

## Default Roles

### Administrator
**Code**: `admin`
**Description**: Full system access

| Object Type | Allowed Actions |
|------------|----------------|
| Account | view, create, edit, delete, merge, export, bulk_update |
| Contact | view, create, edit, delete, merge, export, bulk_update |
| Lead | view, create, edit, delete, convert, export, bulk_update |
| Deal | view, create, edit, delete, export, bulk_update |
| Product | view, create, edit, delete, export |
| Activity | view, create, edit, delete |
| Custom Field | manage_custom_fields |
| System | manage_permissions, manage_users |

### Sales Representative
**Code**: `sales_rep`
**Description**: Can manage own leads, contacts, accounts, and deals

| Object Type | Allowed Actions |
|------------|----------------|
| Account | view, create, edit, export |
| Contact | view, create, edit, export |
| Lead | view, create, edit, convert |
| Deal | view, create, edit |
| Product | view |
| Activity | view, create, edit |

### Read Only
**Code**: `read_only`
**Description**: View-only access to CRM data

| Object Type | Allowed Actions |
|------------|----------------|
| Account | view |
| Contact | view |
| Lead | view |
| Deal | view |
| Product | view |
| Activity | view |

## Permission Evaluation

### Hierarchy
1. **Superuser**: Bypass all checks (Django superuser flag)
2. **Role Permissions**: Defined in RolePermission table
3. **Ownership**: Record owners get additional edit/view rights
4. **Default**: No permission = no access

### Ownership Rules
- If user owns a record (owner_id matches), they automatically get:
  - `view` permission
  - `edit` permission (if role allows any edit)

### Code Example

```python
from crm.permissions.evaluator import has_permission, get_allowed_actions

# Check specific permission
can_convert = has_permission(
    user=current_user,
    object_type='lead',
    action='convert',
    organization=current_org,
    obj=lead_instance
)

# Get all allowed actions
actions = get_allowed_actions(
    user=current_user,
    object_type='account',
    organization=current_org
)
# Returns: {'view', 'create', 'edit', 'export'}
```

## API Integration

### Permission Decorator Example

```python
from crm.permissions.evaluator import has_permission
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

@api_view(['POST'])
def convert_lead(request, lead_id):
    lead = Lead.objects.get(id=lead_id)
    
    if not has_permission(
        user=request.user,
        object_type='lead',
        action='convert',
        organization=lead.organization,
        obj=lead
    ):
        return Response(
            {'error': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Proceed with conversion
    ...
```

## Database Schema

### Role Table
```sql
CREATE TABLE crm_roles (
    id INTEGER PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    name VARCHAR(100),
    code VARCHAR(50),
    description TEXT,
    is_system BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(organization_id, code)
);
```

### RolePermission Table
```sql
CREATE TABLE crm_role_permissions (
    id INTEGER PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    object_type VARCHAR(50),
    action VARCHAR(50),
    field_restrictions JSONB DEFAULT '{}',
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(organization_id, role_id, object_type, action)
);
```

## Seeding Roles

Default roles can be seeded using the management command:

```bash
python manage.py seed_roles
```

Or programmatically:

```python
from crm.fixtures.seed_roles import seed_roles_for_organization

seed_roles_for_organization(organization)
```

## Future Enhancements

### Field-Level Permissions
Store field restrictions in `field_restrictions` JSON:

```json
{
    "allowed_fields": ["name", "email", "phone"],
    "hidden_fields": ["annual_revenue", "credit_limit"],
    "read_only_fields": ["created_at", "account_number"]
}
```

### Conditional Permissions
Rules based on record state:

```json
{
    "conditions": {
        "status": {"not_in": ["closed", "archived"]},
        "owner_id": {"equals": "current_user"}
    }
}
```

### Team-Based Permissions
- Permissions based on team membership
- Hierarchical team structures
- Manager can access subordinates' records

### Record-Level Sharing
- Share individual records with users/teams
- Grant temporary elevated permissions
- Audit sharing activity

## Best Practices

1. **Principle of Least Privilege**: Start with minimal permissions, add as needed
2. **Regular Audits**: Review role assignments quarterly
3. **Document Custom Roles**: Maintain description and reasoning
4. **Test Permissions**: Verify permissions work as expected
5. **Monitor Usage**: Track permission denials for refinement

## Security Considerations

- Roles are organization-scoped (no cross-org access)
- System roles (`is_system=True`) cannot be deleted
- Permission changes take effect immediately
- Failed permission checks should be logged
- Superusers bypass all checks (use carefully)

## Testing Permissions

```python
def test_sales_rep_cannot_delete_account():
    sales_rep = create_user_with_role('sales_rep')
    account = create_account()
    
    can_delete = has_permission(
        user=sales_rep,
        object_type='account',
        action='delete',
        organization=account.organization,
        obj=account
    )
    
    assert can_delete is False
```
