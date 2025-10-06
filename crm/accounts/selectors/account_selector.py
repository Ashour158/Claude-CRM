# crm/accounts/selectors/account_selector.py
# Account selectors for data retrieval

from django.db.models import Q, Count, Sum
from typing import Optional, List
from crm.accounts.models import Account


def get_account(account_id: int, for_update: bool = False) -> Optional[Account]:
    """
    Get a single account by ID.
    
    Args:
        account_id: The account ID
        for_update: If True, locks the row for update
        
    Returns:
        Account instance or None if not found
    """
    qs = Account.objects.all()
    if for_update:
        qs = qs.select_for_update()
    
    try:
        return qs.get(id=account_id)
    except Account.DoesNotExist:
        return None


def list_accounts(
    *,
    search: Optional[str] = None,
    account_type: Optional[str] = None,
    status: Optional[str] = None,
    owner_id: Optional[int] = None,
    is_active: bool = True,
    order_by: str = 'name'
):
    """
    List accounts with optional filtering.
    
    Args:
        search: Search term for name, email, phone
        account_type: Filter by account type
        status: Filter by status
        owner_id: Filter by owner
        is_active: Filter by active status
        order_by: Order by field (default: 'name')
        
    Returns:
        QuerySet of Account instances
    """
    qs = Account.objects.all()
    
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    
    if search:
        qs = qs.filter(
            Q(name__icontains=search) |
            Q(primary_email__icontains=search) |
            Q(phone__icontains=search) |
            Q(website__icontains=search)
        )
    
    if account_type:
        qs = qs.filter(type=account_type)
    
    if status:
        qs = qs.filter(status=status)
    
    if owner_id:
        qs = qs.filter(owner_id=owner_id)
    
    return qs.order_by(order_by)


def search_accounts(query: str, limit: int = 10) -> List[Account]:
    """
    Search accounts by name, email, or phone.
    
    Args:
        query: Search query string
        limit: Maximum number of results
        
    Returns:
        List of matching Account instances
    """
    return list(
        Account.objects.filter(
            Q(name__icontains=query) |
            Q(primary_email__icontains=query) |
            Q(phone__icontains=query)
        ).order_by('name')[:limit]
    )


def get_account_stats(account_id: int) -> dict:
    """
    Get statistics for an account.
    
    Args:
        account_id: The account ID
        
    Returns:
        Dictionary with account statistics
    """
    from crm.contacts.models import Contact
    from deals.models import Deal
    
    account = get_account(account_id)
    if not account:
        return {}
    
    contacts_count = Contact.objects.filter(account=account).count()
    deals_count = Deal.objects.filter(account=account).count()
    open_deals_value = Deal.objects.filter(
        account=account,
        status='open'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    return {
        'contacts_count': contacts_count,
        'deals_count': deals_count,
        'open_deals_value': float(open_deals_value),
    }
