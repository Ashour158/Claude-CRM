"""
Tenancy Context Management

This module provides ContextVar-based storage for the current organization/tenant
context to be used throughout the application for row-level multi-tenancy.

Note: This is scaffolding for future multi-tenancy enforcement. The middleware
is not yet enabled in settings to avoid breaking existing functionality.
"""

from contextvars import ContextVar
from typing import Optional
import uuid

# Context variable to store the current organization ID
_current_organization_id: ContextVar[Optional[uuid.UUID]] = ContextVar(
    'current_organization_id', default=None
)


def get_current_organization_id() -> Optional[uuid.UUID]:
    """
    Get the current organization ID from context.
    
    Returns:
        Optional[uuid.UUID]: The current organization ID if set, None otherwise.
    """
    return _current_organization_id.get()


def set_current_organization_id(organization_id: Optional[uuid.UUID]) -> None:
    """
    Set the current organization ID in context.
    
    Args:
        organization_id: The organization ID to set, or None to clear.
    """
    _current_organization_id.set(organization_id)


def clear_current_organization() -> None:
    """Clear the current organization from context."""
    _current_organization_id.set(None)
