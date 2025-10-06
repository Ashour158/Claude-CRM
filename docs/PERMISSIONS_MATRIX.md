# Permissions Matrix

## Overview
The permissions system provides role-based access control (RBAC) with object-level permissions and scope restrictions.

## Architecture

### Role Model
Defines roles within an organization. Each role can have multiple permissions.

```python
class Role(TenantOwnedModel):
    name            # Role name (e.g., "Sales Manager")
    role_type       # admin, manager, sales_rep, viewer, custom
    description     # Role description
    is_active       # Whether role is active
    is_system_role  # System roles cannot be deleted
```

### RolePermission Model
Maps specific permissions to roles for object types.

```python
class RolePermission(TenantOwnedModel):
    role            # FK to Role
    object_type     # account, contact, lead, deal, etc.
    permission_code # view, create, edit, delete, convert, etc.
    scope           # own, team, territory, all
    is_granted      # Allow or deny
```

## Permission Matrix

### Object Types
- `account` - Account/Company records
- `contact` - Contact/Person records
- `lead` - Lead/Prospect records
- `deal` - Deal/Opportunity records
- `opportunity` - Opportunity records
- `custom_field_definition` - Custom field management
- `activity` - Activity/Timeline records
- `report` - Reports
- `dashboard` - Dashboards

### Permission Actions

| Permission | Code | Description |
|------------|------|-------------|
| View | `view` | View records |
| Create | `create` | Create new records |
| Edit | `edit` | Edit existing records |
| Delete | `delete` | Delete records |
| Convert | `convert` | Convert leads (lead-specific) |
| Export | `export` | Export data |
| Import | `import` | Import data |
| Manage Custom Fields | `manage_custom_fields` | Create/edit custom fields |
| Assign | `assign` | Assign records to other users |
| Share | `share` | Share records with others |

### Permission Scopes

| Scope | Code | Description |
|-------|------|-------------|
| Own Records Only | `own` | User can only access their own records |
| Team Records | `team` | User can access their team's records |
| Territory Records | `territory` | User can access records in their territory |
| All Records | `all` | User can access all organization records |

## Default Roles

### Administrator
Full access to everything.

```python
{
    "role": "Administrator",
    "role_type": "admin",
    "permissions": {
        "*": {  # All object types
            "view": "all",
            "create": "all",
            "edit": "all",
            "delete": "all",
            "export": "all",
            "import": "all",
            "manage_custom_fields": "all",
            "assign": "all",
            "share": "all"
        }
    }
}
```

### Sales Manager
Manage team's sales activities.

```python
{
    "role": "Sales Manager",
    "role_type": "manager",
    "permissions": {
        "account": {
            "view": "team",
            "create": "all",
            "edit": "team",
            "delete": "own",
            "export": "team"
        },
        "contact": {
            "view": "team",
            "create": "all",
            "edit": "team",
            "delete": "own"
        },
        "lead": {
            "view": "team",
            "create": "all",
            "edit": "team",
            "delete": "own",
            "convert": "team"
        },
        "deal": {
            "view": "team",
            "create": "all",
            "edit": "team",
            "delete": "own"
        },
        "activity": {
            "view": "team",
            "create": "all",
            "edit": "team",
            "delete": "own"
        }
    }
}
```

### Sales Representative
Manage own sales activities.

```python
{
    "role": "Sales Representative",
    "role_type": "sales_rep",
    "permissions": {
        "account": {
            "view": "own",
            "create": "all",
            "edit": "own",
            "delete": "own"
        },
        "contact": {
            "view": "own",
            "create": "all",
            "edit": "own",
            "delete": "own"
        },
        "lead": {
            "view": "own",
            "create": "all",
            "edit": "own",
            "delete": "own",
            "convert": "own"
        },
        "deal": {
            "view": "own",
            "create": "all",
            "edit": "own",
            "delete": "own"
        },
        "activity": {
            "view": "own",
            "create": "all",
            "edit": "own",
            "delete": "own"
        }
    }
}
```

### Viewer
Read-only access.

```python
{
    "role": "Viewer",
    "role_type": "viewer",
    "permissions": {
        "account": {"view": "all"},
        "contact": {"view": "all"},
        "lead": {"view": "all"},
        "deal": {"view": "all"},
        "activity": {"view": "all"}
    }
}
```

## Permission Checking

### PermissionMatrix Utility

#### has_permission(user, object_type, permission_code, obj=None, organization=None)
Check if a user has a specific permission.

```python
from crm.permissions.models import PermissionMatrix

# Check if user can edit accounts
can_edit = PermissionMatrix.has_permission(
    user=current_user,
    object_type='account',
    permission_code='edit',
    obj=account_instance,  # Optional specific object
    organization=current_org
)
```

#### get_user_permissions(user, object_type, organization=None)
Get all permissions a user has for an object type.

```python
permissions = PermissionMatrix.get_user_permissions(
    user=current_user,
    object_type='lead',
    organization=current_org
)
# Returns: ['view', 'create', 'edit', 'delete', 'convert']
```

#### get_allowed_actions(user, object_type, obj=None, organization=None)
Get all allowed actions for a user.

```python
actions = PermissionMatrix.get_allowed_actions(
    user=current_user,
    object_type='account',
    obj=account_instance,
    organization=current_org
)
# Returns: ['view', 'edit']
```

## DRF Integration (Future)

### Permission Classes

```python
from rest_framework import permissions

class CRMObjectPermission(permissions.BasePermission):
    """Check CRM object permissions"""
    
    def has_permission(self, request, view):
        # Check if user has general permission for this action
        object_type = getattr(view, 'permission_object_type', None)
        if not object_type:
            return True
        
        action_map = {
            'GET': 'view',
            'POST': 'create',
            'PUT': 'edit',
            'PATCH': 'edit',
            'DELETE': 'delete'
        }
        
        permission_code = action_map.get(request.method, 'view')
        
        return PermissionMatrix.has_permission(
            user=request.user,
            object_type=object_type,
            permission_code=permission_code,
            organization=request.organization
        )
    
    def has_object_permission(self, request, view, obj):
        # Check permission on specific object
        object_type = obj.__class__.__name__.lower()
        
        action_map = {
            'GET': 'view',
            'PUT': 'edit',
            'PATCH': 'edit',
            'DELETE': 'delete'
        }
        
        permission_code = action_map.get(request.method, 'view')
        
        return PermissionMatrix.has_permission(
            user=request.user,
            object_type=object_type,
            permission_code=permission_code,
            obj=obj,
            organization=obj.organization
        )
```

### ViewSet Usage

```python
class AccountViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, CRMObjectPermission]
    permission_object_type = 'account'
    
    def get_queryset(self):
        # Filter based on user's permission scope
        user_scope = PermissionMatrix.get_user_scope(
            self.request.user,
            'account',
            'view'
        )
        
        if user_scope == 'own':
            return Account.objects.filter(owner=self.request.user)
        elif user_scope == 'team':
            return Account.objects.filter(owner__in=get_team_members(self.request.user))
        else:  # 'all'
            return Account.objects.all()
```

## Permission Decorators (Future)

```python
from crm.permissions.decorators import require_permission

@require_permission('lead', 'convert')
def convert_lead_view(request, lead_id):
    # This view requires 'convert' permission on 'lead' objects
    ...

@require_permission('account', 'edit', scope='own')
def edit_account_view(request, account_id):
    # Can only edit own accounts
    ...
```

## Scope Resolution

### Scope Hierarchy
```
all > territory > team > own
```

### Determining User's Scope

1. Get all roles for user in organization
2. For each role, get permissions for object_type
3. Take the broadest scope:
   - If any role grants "all" scope → use "all"
   - Else if any role grants "territory" scope → use "territory"
   - Else if any role grants "team" scope → use "team"
   - Else use "own"

## Implementation Status

### Phase 2 (Current) ✅
- [x] Role model
- [x] RolePermission model
- [x] PermissionMatrix utility (stub)
- [ ] Full permission checking logic
- [ ] User-to-Role assignment

### Phase 3 (Future) 📅
- [ ] DRF permission classes
- [ ] Permission decorators
- [ ] ViewSet integration
- [ ] Scope-based QuerySet filtering
- [ ] Permission caching

### Phase 4 (Future) 📅
- [ ] Field-level permissions
- [ ] Record-level permissions
- [ ] Permission inheritance
- [ ] Delegation/temporary permissions

## Testing Permissions

```python
from crm.permissions.models import Role, RolePermission

# Create a role
role = Role.objects.create(
    organization=org,
    name="Test Role",
    role_type="custom"
)

# Grant permissions
RolePermission.objects.create(
    organization=org,
    role=role,
    object_type='account',
    permission_code='view',
    scope='all',
    is_granted=True
)

# Test permission
assert PermissionMatrix.has_permission(
    user=user,
    object_type='account',
    permission_code='view'
)
```

## Security Considerations

1. **Principle of Least Privilege**: Users should only have minimum permissions needed
2. **Default Deny**: If no permission is explicitly granted, access is denied
3. **Audit Trail**: All permission checks should be logged
4. **Regular Review**: Permissions should be reviewed quarterly
5. **Separation of Duties**: Critical operations require multiple roles

## Common Permission Patterns

### Creating Records
- Need `create` permission on object type
- Scope doesn't apply to creation (can always create)
- Newly created records are owned by creator

### Viewing Records
- Need `view` permission with appropriate scope
- Filtered by owner, team, territory, or all

### Editing Records
- Need `edit` permission with appropriate scope
- Can only edit if in scope (own/team/territory/all)

### Deleting Records
- Need `delete` permission with appropriate scope
- Usually restricted to `own` scope for safety

### Converting Leads
- Need `convert` permission on lead object type
- Creates account and contact (need `create` on those)
- Original lead ownership preserved
