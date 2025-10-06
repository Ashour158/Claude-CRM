"""
System constants for the CRM application.

This module defines constants used throughout the system for consistency.
"""

# API Version
API_VERSION = "v1"

# Pagination
DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100

# Date/Time formats
DATE_FORMAT = "YYYY-MM-DD"
DATETIME_FORMAT = "YYYY-MM-DD HH:mm:ss"
TIME_FORMAT = "HH:mm:ss"

# Cache TTL (seconds)
CACHE_TTL_SHORT = 300  # 5 minutes
CACHE_TTL_MEDIUM = 1800  # 30 minutes
CACHE_TTL_LONG = 3600  # 1 hour

# Status constants
STATUS_ACTIVE = "active"
STATUS_INACTIVE = "inactive"
STATUS_DRAFT = "draft"
STATUS_ARCHIVED = "archived"

# Common choices
PRIORITY_CHOICES = [
    ("low", "Low"),
    ("medium", "Medium"),
    ("high", "High"),
    ("urgent", "Urgent"),
]

STATUS_CHOICES = [
    (STATUS_ACTIVE, "Active"),
    (STATUS_INACTIVE, "Inactive"),
    (STATUS_DRAFT, "Draft"),
    (STATUS_ARCHIVED, "Archived"),
]
