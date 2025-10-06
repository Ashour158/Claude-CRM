# crm/contacts/services/contact_service.py
"""
Contact service layer for business logic
"""
from django.db import transaction
from crm.contacts.models import Contact


class ContactService:
    """Service for contact operations"""
    
    @staticmethod
    @transaction.atomic
    def create_contact(organization, data, user=None):
        """
        Create a new contact
        
        Args:
            organization: Company instance
            data: Dict with contact data
            user: User creating the contact
            
        Returns:
            Contact instance
        """
        contact = Contact(
            organization=organization,
            **data
        )
        if user:
            contact.created_by = user
            contact.updated_by = user
        contact.save()
        return contact
    
    @staticmethod
    @transaction.atomic
    def create_from_lead(organization, lead, user=None):
        """
        Create a contact from a lead
        
        Args:
            organization: Company instance
            lead: Lead instance
            user: User creating the contact
            
        Returns:
            Contact instance
        """
        contact_data = {
            'first_name': lead.first_name,
            'last_name': lead.last_name,
            'title': lead.title,
            'email': lead.email,
            'phone': lead.phone,
            'mobile': lead.mobile,
            'mailing_address_line1': lead.address_line1,
            'mailing_address_line2': lead.address_line2,
            'mailing_city': lead.city,
            'mailing_state': lead.state,
            'mailing_postal_code': lead.postal_code,
            'mailing_country': lead.country,
            'owner': lead.owner,
            'description': lead.description,
            'custom_fields': lead.custom_fields or {},
        }
        
        return ContactService.create_contact(organization, contact_data, user)
    
    @staticmethod
    @transaction.atomic
    def update_contact(contact, data, user=None):
        """
        Update an existing contact
        
        Args:
            contact: Contact instance
            data: Dict with updated data
            user: User updating the contact
            
        Returns:
            Updated Contact instance
        """
        for key, value in data.items():
            if hasattr(contact, key):
                setattr(contact, key, value)
        
        if user:
            contact.updated_by = user
        contact.save()
        return contact
