# crm/contacts/models/contact.py
# Contact domain model with enhanced tenancy support

from django.db import models
from django.core.validators import EmailValidator
from crm.tenancy import TenantOwnedModel
from core.models import User


class Contact(TenantOwnedModel):
    """
    Contact model represents an individual person.
    Contacts can be associated with accounts (companies).
    """
    
    # Basic Information
    first_name = models.CharField(max_length=100, db_index=True)
    last_name = models.CharField(max_length=100, db_index=True)
    full_name = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text="Auto-generated full name"
    )
    title = models.CharField(max_length=100, blank=True, help_text="Job title")
    department = models.CharField(max_length=100, blank=True)
    
    # Contact Information
    primary_email = models.EmailField(blank=True, validators=[EmailValidator()])
    phone = models.CharField(max_length=50, blank=True)
    mobile = models.CharField(max_length=50, blank=True)
    
    # Relationships
    account = models.ForeignKey(
        'accounts.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contacts_v2',
        help_text="Company/Account this contact belongs to"
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_contacts_v2',
        help_text="Sales rep who owns this contact"
    )
    
    # Mailing Address
    mailing_address_line1 = models.CharField(max_length=255, blank=True)
    mailing_address_line2 = models.CharField(max_length=255, blank=True)
    mailing_city = models.CharField(max_length=100, blank=True)
    mailing_state = models.CharField(max_length=100, blank=True)
    mailing_postal_code = models.CharField(max_length=20, blank=True)
    mailing_country = models.CharField(max_length=100, blank=True)
    
    # Status
    status = models.CharField(
        max_length=50,
        choices=[
            ('active', 'Active'),
            ('inactive', 'Inactive'),
        ],
        default='active',
        db_index=True
    )
    is_active = models.BooleanField(default=True, db_index=True)
    
    # Custom Data
    custom_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Custom field values stored as JSON"
    )
    
    # Notes
    description = models.TextField(blank=True, help_text="Notes about this contact")
    
    class Meta:
        db_table = 'crm_contacts_v2'
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['organization', 'last_name', 'first_name']),
            models.Index(fields=['organization', 'account']),
            models.Index(fields=['organization', 'owner']),
            models.Index(fields=['organization', 'primary_email']),
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['organization', 'created_at']),
        ]
    
    def __str__(self):
        return self.full_name or f"{self.first_name} {self.last_name}"
    
    def save(self, *args, **kwargs):
        # Auto-generate full_name
        self.full_name = f"{self.first_name} {self.last_name}".strip()
        super().save(*args, **kwargs)
    
    def get_full_address(self):
        """Get formatted mailing address"""
        parts = [
            self.mailing_address_line1,
            self.mailing_address_line2,
            self.mailing_city,
            self.mailing_state,
            self.mailing_postal_code,
            self.mailing_country
        ]
        return ', '.join([p for p in parts if p])
