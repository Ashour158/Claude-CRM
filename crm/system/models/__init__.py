# crm/system/models/__init__.py
from .custom_field_definition import CustomFieldDefinition
from .role import Role
from .role_permission import RolePermission

__all__ = ['CustomFieldDefinition', 'Role', 'RolePermission']
