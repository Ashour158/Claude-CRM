# Permissions Enforcement

## Overview

The Phase 3 Permission Enforcement Layer provides role-based access control (RBAC) for API endpoints with comprehensive logging and denial tracking.

## Architecture

### Components

1. **ObjectTypePermission**: Base permission class for object-type based access control
2. **ActionPermission**: Extended permission class for custom action permissions
3. **Permission Logging**: Security audit trail for all denial events

### Permission Flow

```
Request → Permission Check → Role Evaluation → Action Authorization → Deny/Allow
```

## Permission Classes

### ObjectTypePermission

Maps HTTP methods to actions and checks against user roles:

- `GET` → `view`
- `POST` → `add`
- `PUT/PATCH` → `change`
- `DELETE` → `delete`

**Usage:**

```python
from core.permissions import ObjectTypePermission
from rest_framework import viewsets

class MyViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, ObjectTypePermission]
    object_type = 'mymodel'  # Optional: specify object type
```

### ActionPermission

Extends ObjectTypePermission to support custom actions:

```python
from core.permissions import ActionPermission

class DealViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, ActionPermission]
    object_type = 'deal'
    
    @action(detail=False, methods=['get'])
    def board(self, request):
        # Automatically checks 'view' permission
        pass
    
    @action(detail=False, methods=['post'])
    def move(self, request):
        # Automatically checks 'change' permission
        pass
```

## Role-Based Permissions

### Default Roles

| Role | View | Add | Change | Delete |
|------|------|-----|--------|--------|
| **admin** | ✓ | ✓ | ✓ | ✓ |
| **manager** | ✓ | ✓ | ✓ | ✗ |
| **sales_rep** | ✓ | ✓ | ✓ | ✗ |
| **user** | ✓ | ✗ | ✗ | ✗ |

### Ownership Rules

- **Owners** have full access to their own records
- **Non-owners** require manager or admin role for modifications
- **Superusers** bypass all permission checks

## Permission Denial Logging

All permission denials are logged with the following information:

```json
{
  "event": "permission_denied",
  "user_id": "uuid",
  "user_email": "user@example.com",
  "object_type": "deal",
  "action": "delete",
  "ip_address": "192.168.1.1",
  "path": "/api/deals/123/",
  "method": "DELETE",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Error Response Format

When permission is denied, the API returns:

```json
{
  "detail": "You do not have permission to perform this action."
}
```

Status Code: `403 Forbidden`

## Custom Permission Logic

Override `check_permission` or `check_object_permission` for custom logic:

```python
class CustomPermission(ObjectTypePermission):
    def check_permission(self, user, object_type, action, request):
        # Custom logic here
        if custom_condition:
            return True
        return super().check_permission(user, object_type, action, request)
```

## Security Best Practices

1. **Always use IsAuthenticated** as the first permission class
2. **Specify object_type** explicitly for clarity
3. **Review denial logs** regularly for security auditing
4. **Test negative scenarios** in your test suite
5. **Don't bypass permissions** directly in views

## Testing Permissions

Example test case:

```python
from django.test import TestCase
from rest_framework.test import APIClient

class PermissionTests(TestCase):
    def test_non_admin_cannot_delete(self):
        # Setup user with 'user' role
        client = APIClient()
        client.force_authenticate(user=self.user)
        
        # Try to delete
        response = client.delete(f'/api/deals/{deal.id}/')
        
        # Should be denied
        self.assertEqual(response.status_code, 403)
```

## Endpoint Permission Matrix

### Deals Module

| Endpoint | Method | Required Role | Notes |
|----------|--------|---------------|-------|
| `/api/deals/` | GET | user+ | List deals |
| `/api/deals/` | POST | sales_rep+ | Create deal |
| `/api/deals/{id}/` | GET | user+ | View deal |
| `/api/deals/{id}/` | PUT | sales_rep+ | Update deal (owner or manager+) |
| `/api/deals/{id}/` | DELETE | admin | Delete deal |
| `/api/deals/board/` | GET | user+ | View kanban board |
| `/api/deals/move/` | POST | sales_rep+ | Move deal between stages |

### Core Module

| Endpoint | Method | Required Role | Notes |
|----------|--------|---------------|-------|
| `/api/core/saved-views/` | GET | user+ | List views |
| `/api/core/saved-views/` | POST | user+ | Create private view |
| `/api/core/saved-views/{id}/` | PUT | owner or admin | Update view |
| `/api/core/saved-views/{id}/` | DELETE | owner or admin | Delete view |

## Monitoring

Use the permission denial logs to:

- **Identify unauthorized access attempts**
- **Detect misconfigured roles**
- **Audit security compliance**
- **Improve user training**

## Future Enhancements

- Field-level permissions
- Time-based access restrictions
- IP whitelist/blacklist integration
- MFA requirement enforcement
- Permission caching for performance
