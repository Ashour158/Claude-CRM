# crm/leads/services/conversion_service.py
"""
Lead conversion service - converts leads to accounts, contacts, and deals
"""
from django.db import transaction
from django.utils import timezone
from crm.accounts.services.account_service import AccountService
from crm.contacts.services.contact_service import ContactService
from crm.activities.services.timeline_service import TimelineService


class ConversionService:
    """Service for converting leads"""
    
    @staticmethod
    @transaction.atomic
    def convert_lead(lead, create_deal=True, deal_data=None, user=None):
        """
        Convert a lead to Account, Contact, and optionally Deal
        
        Args:
            lead: Lead instance to convert
            create_deal: Whether to create a deal
            deal_data: Optional dict with deal-specific data
            user: User performing the conversion
            
        Returns:
            Tuple (account, contact, deal or None)
        """
        # Check if already converted
        if lead.is_converted():
            raise ValueError("Lead has already been converted")
        
        # Create or get account
        account_data = {
            'name': lead.company_name or f"{lead.first_name} {lead.last_name}",
            'email': lead.email,
            'phone': lead.phone,
            'website': lead.website if hasattr(lead, 'website') else '',
            'industry': lead.industry,
            'annual_revenue': lead.annual_revenue,
            'employee_count': lead.employee_count,
            'billing_address_line1': lead.address_line1,
            'billing_address_line2': lead.address_line2,
            'billing_city': lead.city,
            'billing_state': lead.state,
            'billing_postal_code': lead.postal_code,
            'billing_country': lead.country,
            'territory': lead.territory,
            'owner': lead.owner,
            'account_type': 'customer',
        }
        
        from crm.accounts.models import Account
        # Try to find existing account
        account = Account.objects.for_organization(lead.organization).filter(
            name=account_data['name'],
            email=lead.email
        ).first()
        
        if not account:
            account = AccountService.create_account(
                lead.organization,
                account_data,
                user
            )
        
        # Create contact
        contact = ContactService.create_from_lead(lead.organization, lead, user)
        contact.account = account
        contact.save()
        
        # Create deal if requested
        deal = None
        if create_deal:
            from deals.models import Deal
            deal_data = deal_data or {}
            deal = Deal.objects.create(
                company=lead.organization,
                name=deal_data.get('name', f"Deal - {account.name}"),
                account=account,
                contact=contact,
                amount=deal_data.get('amount', lead.budget or 0),
                owner=lead.owner,
                description=lead.description,
            )
        
        # Update lead status
        lead.lead_status = 'converted'
        lead.converted_at = timezone.now()
        lead.converted_account = account
        lead.converted_contact = contact
        lead.converted_deal = deal
        if user:
            lead.updated_by = user
        lead.save()
        
        # Record timeline event
        TimelineService.record_event(
            organization=lead.organization,
            target=lead,
            event_type='conversion',
            title=f"Lead converted to Account: {account.name}",
            description=f"Lead {lead.get_full_name()} converted to account, contact" + 
                       (", and deal" if deal else ""),
            actor=user,
            metadata={
                'account_id': str(account.id),
                'contact_id': str(contact.id),
                'deal_id': str(deal.id) if deal else None,
            }
        )
        
        return account, contact, deal
    
    @staticmethod
    def can_convert_lead(lead):
        """
        Check if a lead can be converted
        
        Args:
            lead: Lead instance
            
        Returns:
            Tuple (can_convert, reason)
        """
        if lead.is_converted():
            return False, "Lead has already been converted"
        
        if not lead.email:
            return False, "Email is required for conversion"
        
        if not lead.first_name or not lead.last_name:
            return False, "First and last name are required"
        
        return True, ""
