"""
Core module for CRM system.

This module contains core functionality including:
    - Tenancy support (row-level multi-tenancy)
    - Common exceptions
    - System constants
    - Shared utilities
"""

from . import tenancy

__all__ = ['tenancy']
