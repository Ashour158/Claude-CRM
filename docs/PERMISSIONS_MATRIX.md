# Permissions Matrix

## Overview
The CRM system implements a role-based access control (RBAC) system with fine-grained permissions for different resources and actions.

## Permission Model

### Components

1. **Role** - A named set of permissions (e.g., Sales Manager, Sales Rep)
2. **RolePermission** - Links roles to specific resource/action combinations
3. **Resource** - Entity type (account, contact, lead, deal, etc.)
4. **Action** - Operation (create, read, update, delete, export, import)

## Default Roles

### Super Admin
**Description**: Full system access, can manage all organizations
**Scope**: System-wide

| Resource | Create | Read | Update | Delete | Export | Import |
|----------|--------|------|--------|--------|--------|--------|
| Account  | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Contact  | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Lead     | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Deal     | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Activity | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Report   | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Settings | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| User     | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

### Admin
**Description**: Organization administrator
**Scope**: Organization-wide

| Resource | Create | Read | Update | Delete | Export | Import |
|----------|--------|------|--------|--------|--------|--------|
| Account  | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Contact  | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Lead     | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Deal     | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Activity | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Report   | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| Settings | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| User     | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |

### Sales Manager
**Description**: Manages sales team and all deals
**Scope**: Organization or territory

| Resource | Create | Read | Update | Delete | Export | Import |
|----------|--------|------|--------|--------|--------|--------|
| Account  | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| Contact  | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| Lead     | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ |
| Deal     | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| Activity | ✅ | ✅ | ✅ | ❌ | ✅ | ❌ |
| Report   | ❌ | ✅ | ❌ | ❌ | ✅ | ❌ |
| Settings | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| User     | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |

### Sales Rep
**Description**: Individual sales person
**Scope**: Own records only

| Resource | Create | Read | Update | Delete | Export | Import |
|----------|--------|------|--------|--------|--------|--------|
| Account  | ✅ | ✅* | ✅* | ❌ | ✅* | ❌ |
| Contact  | ✅ | ✅* | ✅* | ❌ | ✅* | ❌ |
| Lead     | ✅ | ✅* | ✅* | ❌ | ✅* | ❌ |
| Deal     | ✅ | ✅* | ✅* | ❌ | ✅* | ❌ |
| Activity | ✅ | ✅* | ✅* | ❌ | ❌ | ❌ |
| Report   | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Settings | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| User     | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

*\* = Own records only*

### Viewer
**Description**: Read-only access
**Scope**: Organization-wide

| Resource | Create | Read | Update | Delete | Export | Import |
|----------|--------|------|--------|--------|--------|--------|
| Account  | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Contact  | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Lead     | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Deal     | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Activity | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Report   | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ |
| Settings | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| User     | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

## Permission Conditions

Permissions can include conditions for more granular control:

### Own Records Only
```python
{
    "own_records_only": true
}
```
User can only access records where they are the owner.

### Territory-Based
```python
{
    "territory_only": true
}
```
User can only access records in their assigned territory.

### Status-Based
```python
{
    "allowed_statuses": ["new", "contacted", "qualified"]
}
```
User can only access records with specific statuses.

## Usage

### Check Permissions

```python
from crm.permissions.evaluator import PermissionEvaluator

# Check if user has permission
has_perm = PermissionEvaluator.has_permission(
    user=request.user,
    organization=org,
    resource='account',
    action='create'
)

# Get all allowed actions
allowed_actions = PermissionEvaluator.get_allowed_actions(
    user=request.user,
    organization=org,
    resource='lead'
)
# Returns: ['create', 'read', 'update', 'export']

# Check record-level access
can_access = PermissionEvaluator.can_access_record(
    user=request.user,
    organization=org,
    record=account_instance,
    action='update'
)
```

### Create Custom Role

```python
from crm.system.models import Role, RolePermission

# Create role
role = Role.objects.create(
    organization=org,
    name='Custom Sales Role',
    code='custom_sales',
    description='Custom role with specific permissions'
)

# Add permissions
RolePermission.objects.create(
    organization=org,
    role=role,
    resource='account',
    action='create',
    is_granted=True
)

RolePermission.objects.create(
    organization=org,
    role=role,
    resource='account',
    action='read',
    is_granted=True
)

RolePermission.objects.create(
    organization=org,
    role=role,
    resource='account',
    action='update',
    is_granted=True,
    conditions={'own_records_only': True}
)
```

### Assign Role to User

```python
from core.models import UserCompanyAccess

UserCompanyAccess.objects.create(
    user=user,
    company=org,
    role='custom_sales',  # role code
    is_active=True
)
```

## Role Inheritance

Roles can inherit permissions from parent roles:

```python
# Create parent role
manager_role = Role.objects.create(
    organization=org,
    name='Manager',
    code='manager'
)

# Create child role that inherits from manager
senior_manager_role = Role.objects.create(
    organization=org,
    name='Senior Manager',
    code='senior_manager',
    parent_role=manager_role
)
```

The child role automatically inherits all permissions from the parent role, plus any additional permissions defined specifically for it.

## Best Practices

1. **Principle of Least Privilege**: Grant minimum permissions needed
2. **Use Role Inheritance**: Create hierarchies to reduce duplication
3. **Test Permissions**: Verify permissions work as expected
4. **Document Custom Roles**: Maintain clear documentation
5. **Regular Audits**: Review permissions periodically
6. **Separation of Duties**: Don't give one role too much power

## API Integration

All API endpoints should check permissions:

```python
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from crm.permissions.evaluator import PermissionEvaluator

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_account(request):
    # Check permission
    if not PermissionEvaluator.has_permission(
        request.user,
        request.organization,
        'account',
        'create'
    ):
        return Response(
            {'error': 'Permission denied'},
            status=403
        )
    
    # Proceed with creation...
```

## Related Documentation

- [Domain Migration Status](./DOMAIN_MIGRATION_STATUS.md)
- [Custom Fields Design](./CUSTOM_FIELDS_DESIGN.md)
- [Activities Timeline](./ACTIVITIES_TIMELINE.md)
