# crm/leads/services/lead_service.py
# Lead services for business logic

from typing import Optional
from django.db import transaction
from django.utils import timezone
from dataclasses import dataclass
from crm.leads.models import Lead
from crm.accounts.models import Account
from crm.contacts.models import Contact
from core.models import User, Company


@dataclass
class ConversionResult:
    """Result of lead conversion"""
    lead: Lead
    account: Optional[Account]
    contact: Contact
    was_account_created: bool
    was_contact_created: bool


@transaction.atomic
def create_lead(
    *,
    organization: Company,
    first_name: str = '',
    last_name: str = '',
    company_name: str = '',
    primary_email: str = '',
    phone: str = '',
    owner: Optional[User] = None,
    source: str = '',
    status: str = 'new',
    **kwargs
) -> Lead:
    """Create a new lead."""
    lead = Lead(
        organization=organization,
        first_name=first_name,
        last_name=last_name,
        company_name=company_name,
        primary_email=primary_email,
        phone=phone,
        owner=owner,
        source=source,
        status=status,
        **kwargs
    )
    lead.save()
    return lead


@transaction.atomic
def update_lead(*, lead_id: int, **update_fields) -> Lead:
    """Update an existing lead."""
    lead = Lead.objects.select_for_update().get(id=lead_id)
    
    for field, value in update_fields.items():
        if hasattr(lead, field):
            setattr(lead, field, value)
    
    lead.save()
    return lead


@transaction.atomic
def convert_lead(
    *,
    lead_id: int,
    create_account: bool = True,
    user: Optional[User] = None
) -> ConversionResult:
    """
    Convert a lead to Contact (and optionally Account).
    Implements deduplication by email and creates timeline event.
    
    Args:
        lead_id: ID of lead to convert
        create_account: Whether to create an account (default: True)
        user: User performing the conversion (for timeline event)
        
    Returns:
        ConversionResult with created/found entities
        
    Raises:
        Lead.DoesNotExist: If lead not found
        ValueError: If lead already converted
    """
    from crm.leads.selectors.lead_selector import get_lead_for_update
    
    lead = get_lead_for_update(lead_id)
    if not lead:
        raise Lead.DoesNotExist(f"Lead {lead_id} not found")
    
    if lead.status == 'converted':
        raise ValueError(f"Lead {lead_id} has already been converted")
    
    # Pre-conversion checks
    if not lead.primary_email and not (lead.first_name and lead.last_name):
        raise ValueError("Lead must have email or full name to be converted")
    
    was_account_created = False
    was_contact_created = False
    account = None
    contact = None
    
    # Try to find existing contact by email
    if lead.primary_email:
        contact = Contact.objects.filter(
            organization=lead.organization,
            primary_email=lead.primary_email
        ).first()
    
    # Create or use account
    if create_account and lead.company_name:
        # Try to find existing account by name
        account = Account.objects.filter(
            organization=lead.organization,
            name=lead.company_name
        ).first()
        
        if not account:
            # Create new account
            account = Account.objects.create(
                organization=lead.organization,
                name=lead.company_name,
                primary_email=lead.primary_email,
                phone=lead.phone,
                owner=lead.owner or user,
                industry=lead.industry,
                annual_revenue=lead.annual_revenue,
                employee_count=lead.employee_count,
                billing_address_line1=lead.address_line1,
                billing_address_line2=lead.address_line2,
                billing_city=lead.city,
                billing_state=lead.state,
                billing_postal_code=lead.postal_code,
                billing_country=lead.country,
                type='customer',
                status='active'
            )
            was_account_created = True
    
    # Create or update contact
    if not contact:
        contact = Contact.objects.create(
            organization=lead.organization,
            first_name=lead.first_name,
            last_name=lead.last_name,
            primary_email=lead.primary_email,
            phone=lead.phone,
            mobile=lead.mobile,
            title=lead.title,
            account=account,
            owner=lead.owner or user,
            department='',
            status='active'
        )
        was_contact_created = True
    elif account and not contact.account:
        # Update contact with account if it didn't have one
        contact.account = account
        contact.save(update_fields=['account', 'updated_at'])
    
    # Update lead status
    lead.status = 'converted'
    lead.converted_at = timezone.now()
    lead.converted_account = account
    lead.converted_contact = contact
    lead.save(update_fields=[
        'status', 'converted_at', 'converted_account', 'converted_contact', 'updated_at'
    ])
    
    # Create timeline event
    try:
        from crm.activities.services.timeline_service import record_event
        record_event(
            event_type='lead_converted',
            target=lead,
            actor=user,
            data={
                'lead_id': lead.id,
                'lead_name': str(lead),
                'contact_id': contact.id,
                'contact_name': str(contact),
                'account_id': account.id if account else None,
                'account_name': account.name if account else None,
                'was_account_created': was_account_created,
                'was_contact_created': was_contact_created,
            }
        )
    except Exception as e:
        # Don't fail conversion if timeline event fails
        print(f"Warning: Failed to create timeline event: {e}")
    
    return ConversionResult(
        lead=lead,
        account=account,
        contact=contact,
        was_account_created=was_account_created,
        was_contact_created=was_contact_created
    )


@transaction.atomic
def soft_delete_lead(lead_id: int) -> Lead:
    """Soft delete a lead."""
    lead = Lead.objects.select_for_update().get(id=lead_id)
    lead.is_active = False
    lead.save()
    return lead
