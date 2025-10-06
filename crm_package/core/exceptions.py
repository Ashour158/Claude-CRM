"""
Core exceptions for the CRM system.

This module defines custom exceptions used throughout the application
for consistent error handling.
"""


class CRMBaseException(Exception):
    """Base exception for all CRM-related errors."""
    pass


class TenancyException(CRMBaseException):
    """Raised when there's an issue with tenant/organization context."""
    pass


class OrganizationAccessDenied(TenancyException):
    """Raised when user doesn't have access to an organization."""
    pass


class NoActiveOrganization(TenancyException):
    """Raised when an operation requires an active organization but none is set."""
    pass


class ValidationError(CRMBaseException):
    """Raised when data validation fails."""
    pass


class ResourceNotFound(CRMBaseException):
    """Raised when a requested resource is not found."""
    pass


class PermissionDenied(CRMBaseException):
    """Raised when user doesn't have permission for an action."""
    pass
