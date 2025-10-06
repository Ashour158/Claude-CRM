# crm/permissions/enums.py
# Permission action enumerations

from enum import Enum


class PermissionAction(str, Enum):
    """Enumeration of permission actions"""
    
    # Basic CRUD
    VIEW = 'view'
    EDIT = 'edit'
    DELETE = 'delete'
    CREATE = 'create'
    
    # Special actions
    CONVERT = 'convert'  # For lead conversion
    MERGE = 'merge'  # For merging records
    EXPORT = 'export'  # For exporting data
    IMPORT = 'import'  # For importing data
    
    # Custom fields
    MANAGE_CUSTOM_FIELDS = 'manage_custom_fields'
    
    # Bulk operations
    BULK_UPDATE = 'bulk_update'
    BULK_DELETE = 'bulk_delete'
    
    # Administrative
    MANAGE_PERMISSIONS = 'manage_permissions'
    MANAGE_USERS = 'manage_users'


class ObjectType(str, Enum):
    """Enumeration of object types"""
    
    ACCOUNT = 'account'
    CONTACT = 'contact'
    LEAD = 'lead'
    DEAL = 'deal'
    PRODUCT = 'product'
    ACTIVITY = 'activity'
    TASK = 'task'
    CUSTOM_FIELD = 'custom_field'
    SYSTEM = 'system'
