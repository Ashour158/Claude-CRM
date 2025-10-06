# crm/contacts/selectors/contact_selector.py
# Contact selectors for data retrieval

from django.db.models import Q
from typing import Optional, List
from crm.contacts.models import Contact


def get_contact(contact_id: int, for_update: bool = False) -> Optional[Contact]:
    """Get a single contact by ID."""
    qs = Contact.objects.all()
    if for_update:
        qs = qs.select_for_update()
    
    try:
        return qs.get(id=contact_id)
    except Contact.DoesNotExist:
        return None


def list_contacts(
    *,
    search: Optional[str] = None,
    account_id: Optional[int] = None,
    owner_id: Optional[int] = None,
    is_active: bool = True,
    order_by: str = 'last_name'
):
    """List contacts with optional filtering."""
    qs = Contact.objects.all()
    
    if is_active is not None:
        qs = qs.filter(is_active=is_active)
    
    if search:
        qs = qs.filter(
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(primary_email__icontains=search) |
            Q(phone__icontains=search)
        )
    
    if account_id:
        qs = qs.filter(account_id=account_id)
    
    if owner_id:
        qs = qs.filter(owner_id=owner_id)
    
    return qs.order_by(order_by)


def search_contacts(query: str, limit: int = 10) -> List[Contact]:
    """Search contacts by name, email, or phone."""
    return list(
        Contact.objects.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(primary_email__icontains=query) |
            Q(phone__icontains=query)
        ).order_by('last_name', 'first_name')[:limit]
    )
