# crm/leads/services/lead_conversion_service.py
# Lead conversion service for converting leads to accounts and contacts

from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from crm.leads.models import Lead
from crm.accounts.models import Account
from crm.contacts.models import Contact
from crm.activities.models import TimelineEvent


class LeadConversionResult:
    """Result object returned from lead conversion"""
    
    def __init__(self, lead_id, contact_id, account_id=None, status='success', message=''):
        self.lead_id = lead_id
        self.contact_id = contact_id
        self.account_id = account_id
        self.status = status
        self.message = message
    
    def to_dict(self):
        return {
            'lead_id': str(self.lead_id),
            'contact_id': str(self.contact_id),
            'account_id': str(self.account_id) if self.account_id else None,
            'status': self.status,
            'message': self.message
        }
    
    def __repr__(self):
        return f"<LeadConversionResult: {self.status} - Lead {self.lead_id} -> Contact {self.contact_id}>"


class AlreadyConvertedError(Exception):
    """Raised when trying to convert an already converted lead"""
    pass


class LeadConversionService:
    """
    Service for converting leads to accounts and contacts.
    
    Features:
    - Creates Contact (required)
    - Creates Account if requested and not already linked
    - Moves/copies relevant fields
    - Records Activity event (type = lead_converted)
    - Uses select_for_update to prevent race conditions
    """
    
    @staticmethod
    @transaction.atomic
    def convert_lead(lead_id, *, create_account=True, user=None, organization=None):
        """
        Convert a lead to a contact (and optionally an account).
        
        Args:
            lead_id: ID of the lead to convert
            create_account: If True, create an account (if lead doesn't have one)
            user: User performing the conversion (for audit trail)
            organization: Organization context (uses lead's org if not provided)
            
        Returns:
            LeadConversionResult object
            
        Raises:
            Lead.DoesNotExist: If lead doesn't exist
            AlreadyConvertedError: If lead is already converted
            ValidationError: If conversion fails validation
        """
        # Get lead with lock to prevent concurrent conversions
        lead = Lead.objects.select_for_update().get(id=lead_id)
        
        # Check if already converted
        if lead.status == 'converted':
            raise AlreadyConvertedError(
                f"Lead {lead_id} was already converted on {lead.converted_at}"
            )
        
        organization = organization or lead.organization
        
        # Create or determine account
        account = None
        if create_account:
            account = LeadConversionService._create_account_from_lead(lead, user)
        
        # Create contact
        contact = LeadConversionService._create_contact_from_lead(
            lead, 
            account=account, 
            user=user
        )
        
        # Update lead status
        lead.status = 'converted'
        lead.converted_at = timezone.now()
        lead.converted_account = account
        lead.converted_contact = contact
        lead.save(update_fields=['status', 'converted_at', 'converted_account', 'converted_contact', 'updated_at'])
        
        # Record timeline event
        TimelineEvent.record(
            event_type='lead_converted',
            target_object=lead,
            actor=user,
            data={
                'contact_id': str(contact.id),
                'account_id': str(account.id) if account else None,
                'converted_at': lead.converted_at.isoformat()
            },
            summary=f"Lead converted to Contact: {contact.full_name}" + 
                   (f" at Account: {account.name}" if account else ""),
            organization=organization
        )
        
        return LeadConversionResult(
            lead_id=lead.id,
            contact_id=contact.id,
            account_id=account.id if account else None,
            status='success',
            message=f"Lead successfully converted to contact{' and account' if account else ''}"
        )
    
    @staticmethod
    def _create_account_from_lead(lead, user=None):
        """
        Create an Account from a Lead.
        
        Args:
            lead: Lead instance
            user: User creating the account (for audit)
            
        Returns:
            Account instance
        """
        # Check if account already exists with same name
        if lead.company_name:
            existing_account = Account.objects.filter(
                organization=lead.organization,
                name=lead.company_name
            ).first()
            
            if existing_account:
                return existing_account
        
        # Create new account
        account_name = lead.company_name or f"{lead.first_name} {lead.last_name}".strip()
        
        account = Account(
            organization=lead.organization,
            name=account_name,
            email=lead.email,
            phone=lead.phone,
            website=lead.website,
            industry=lead.industry,
            annual_revenue=lead.annual_revenue,
            employee_count=lead.employee_count,
            billing_address_line1=lead.address_line1,
            billing_address_line2=lead.address_line2,
            billing_city=lead.city,
            billing_state=lead.state,
            billing_postal_code=lead.postal_code,
            billing_country=lead.country,
            territory=lead.territory,
            owner=lead.owner or user,
            description=lead.description,
            created_by=user,
            updated_by=user,
        )
        
        # Copy custom fields
        if lead.custom_data:
            account.custom_data = lead.custom_data.copy()
        
        account.save()
        return account
    
    @staticmethod
    def _create_contact_from_lead(lead, account=None, user=None):
        """
        Create a Contact from a Lead.
        
        Args:
            lead: Lead instance
            account: Optional account to associate with
            user: User creating the contact (for audit)
            
        Returns:
            Contact instance
        """
        # Check for existing contact with same email
        if lead.email:
            existing_contact = Contact.objects.filter(
                organization=lead.organization,
                email=lead.email
            ).first()
            
            if existing_contact:
                # Update account if provided
                if account and not existing_contact.account:
                    existing_contact.account = account
                    existing_contact.save(update_fields=['account', 'updated_at'])
                return existing_contact
        
        contact = Contact(
            organization=lead.organization,
            first_name=lead.first_name,
            last_name=lead.last_name,
            full_name=lead.full_name,
            title=lead.title,
            email=lead.email,
            phone=lead.phone,
            mobile=lead.mobile,
            account=account,
            owner=lead.owner or user,
            mailing_address_line1=lead.address_line1,
            mailing_address_line2=lead.address_line2,
            mailing_city=lead.city,
            mailing_state=lead.state,
            mailing_postal_code=lead.postal_code,
            mailing_country=lead.country,
            description=lead.description,
            created_by=user,
            updated_by=user,
        )
        
        # Copy custom fields
        if lead.custom_data:
            contact.custom_data = lead.custom_data.copy()
        
        contact.save()
        return contact
    
    @staticmethod
    def can_convert_lead(lead_id):
        """
        Check if a lead can be converted.
        
        Args:
            lead_id: ID of the lead
            
        Returns:
            tuple: (can_convert: bool, reason: str)
        """
        try:
            lead = Lead.objects.get(id=lead_id)
            
            if lead.status == 'converted':
                return False, "Lead is already converted"
            
            if not lead.first_name and not lead.last_name and not lead.company_name:
                return False, "Lead must have either a name or company name"
            
            if lead.status == 'unqualified':
                return False, "Cannot convert unqualified lead"
            
            return True, "Lead can be converted"
            
        except Lead.DoesNotExist:
            return False, "Lead does not exist"
