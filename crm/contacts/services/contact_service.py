# crm/contacts/services/contact_service.py
# Contact services for business logic

from typing import Optional
from django.db import transaction
from crm.contacts.models import Contact
from core.models import User, Company


@transaction.atomic
def create_contact(
    *,
    organization: Company,
    first_name: str,
    last_name: str,
    owner: Optional[User] = None,
    primary_email: str = '',
    phone: str = '',
    account_id: Optional[int] = None,
    **kwargs
) -> Contact:
    """Create a new contact."""
    contact = Contact(
        organization=organization,
        first_name=first_name,
        last_name=last_name,
        owner=owner,
        primary_email=primary_email,
        phone=phone,
        account_id=account_id,
        **kwargs
    )
    contact.save()
    return contact


@transaction.atomic
def update_contact(*, contact_id: int, **update_fields) -> Contact:
    """Update an existing contact."""
    contact = Contact.objects.select_for_update().get(id=contact_id)
    
    for field, value in update_fields.items():
        if hasattr(contact, field):
            setattr(contact, field, value)
    
    contact.save()
    return contact


@transaction.atomic
def soft_delete_contact(contact_id: int) -> Contact:
    """Soft delete a contact."""
    contact = Contact.objects.select_for_update().get(id=contact_id)
    contact.is_active = False
    contact.status = 'inactive'
    contact.save()
    return contact
