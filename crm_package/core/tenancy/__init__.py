"""
Tenancy module for row-level multi-tenancy support.

This module provides the foundation for multi-tenant isolation using
row-level security (organization foreign key on models).

Components:
    - context: ContextVar-based organization storage
    - middleware: Request-level tenant resolution (not enabled yet)
    - mixins: TenantOwnedModel abstract base for tenant-owned entities
    - selectors: Helper functions for organization access
"""

from .context import (
    get_current_organization_id,
    set_current_organization_id,
    clear_current_organization,
)
from .middleware import TenancyMiddleware
from .mixins import TenantOwnedModel
from .selectors import (
    get_organization_by_id,
    get_user_organizations,
    get_user_primary_organization,
    user_has_organization_access,
)

__all__ = [
    'get_current_organization_id',
    'set_current_organization_id',
    'clear_current_organization',
    'TenancyMiddleware',
    'TenantOwnedModel',
    'get_organization_by_id',
    'get_user_organizations',
    'get_user_primary_organization',
    'user_has_organization_access',
]
