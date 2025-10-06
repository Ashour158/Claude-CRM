# crm/accounts/services/account_service.py
# Account services for business logic and data manipulation

from typing import Dict, Optional
from django.db import transaction
from django.utils import timezone
from crm.accounts.models import Account
from core.models import User, Company


@transaction.atomic
def create_account(
    *,
    organization: Company,
    name: str,
    owner: Optional[User] = None,
    primary_email: str = '',
    phone: str = '',
    account_type: str = '',
    status: str = 'active',
    **kwargs
) -> Account:
    """
    Create a new account.
    
    Args:
        organization: The organization/company this account belongs to
        name: Account name (required)
        owner: Account owner (user)
        primary_email: Primary email address
        phone: Phone number
        account_type: Account type (customer, prospect, etc.)
        status: Account status
        **kwargs: Additional account fields
        
    Returns:
        Created Account instance
    """
    account = Account(
        organization=organization,
        name=name,
        owner=owner,
        primary_email=primary_email,
        phone=phone,
        type=account_type,
        status=status,
        **kwargs
    )
    account.save()
    return account


@transaction.atomic
def update_account(
    *,
    account_id: int,
    **update_fields
) -> Account:
    """
    Update an existing account.
    
    Args:
        account_id: The account ID to update
        **update_fields: Fields to update
        
    Returns:
        Updated Account instance
        
    Raises:
        Account.DoesNotExist: If account not found
    """
    account = Account.objects.select_for_update().get(id=account_id)
    
    for field, value in update_fields.items():
        if hasattr(account, field):
            setattr(account, field, value)
    
    account.save()
    return account


@transaction.atomic
def soft_delete_account(account_id: int) -> Account:
    """
    Soft delete an account (mark as inactive).
    
    Args:
        account_id: The account ID to soft delete
        
    Returns:
        Soft-deleted Account instance
        
    Raises:
        Account.DoesNotExist: If account not found
    """
    account = Account.objects.select_for_update().get(id=account_id)
    account.is_active = False
    account.status = 'inactive'
    account.save()
    return account


@transaction.atomic
def merge_accounts(
    *,
    primary_account_id: int,
    secondary_account_id: int,
    keep_secondary: bool = False
) -> Account:
    """
    Merge two accounts, moving contacts and deals to the primary account.
    
    Args:
        primary_account_id: ID of account to keep
        secondary_account_id: ID of account to merge from
        keep_secondary: If False, soft-deletes the secondary account
        
    Returns:
        Primary Account instance
        
    Raises:
        Account.DoesNotExist: If either account not found
    """
    from crm.contacts.models import Contact
    from deals.models import Deal
    
    primary = Account.objects.select_for_update().get(id=primary_account_id)
    secondary = Account.objects.select_for_update().get(id=secondary_account_id)
    
    # Move contacts
    Contact.objects.filter(account=secondary).update(account=primary)
    
    # Move deals
    Deal.objects.filter(account=secondary).update(account=primary)
    
    # Optionally soft-delete secondary account
    if not keep_secondary:
        secondary.is_active = False
        secondary.status = 'inactive'
        secondary.save()
    
    return primary


def update_custom_data(
    *,
    account_id: int,
    custom_data: Dict
) -> Account:
    """
    Update custom data fields for an account.
    
    Args:
        account_id: The account ID
        custom_data: Dictionary of custom field values
        
    Returns:
        Updated Account instance
    """
    account = Account.objects.get(id=account_id)
    
    if account.custom_data is None:
        account.custom_data = {}
    
    account.custom_data.update(custom_data)
    account.save(update_fields=['custom_data', 'updated_at'])
    
    return account
