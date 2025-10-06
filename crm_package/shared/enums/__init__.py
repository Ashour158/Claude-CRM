"""
Shared enumeration types.
"""

from enum import Enum


class AccountType(str, Enum):
    """Account type enumeration."""
    CUSTOMER = "customer"
    PROSPECT = "prospect"
    PARTNER = "partner"
    COMPETITOR = "competitor"


class LeadStatus(str, Enum):
    """Lead status enumeration."""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    CONVERTED = "converted"
    LOST = "lost"


class DealStage(str, Enum):
    """Deal stage enumeration."""
    PROSPECTING = "prospecting"
    QUALIFICATION = "qualification"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class Priority(str, Enum):
    """Priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"
