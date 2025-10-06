# crm/contacts/models/contact.py
# Contact model with row-level multi-tenancy

from django.db import models
from django.core.validators import EmailValidator
from core.tenant_models import TenantOwnedModel
from core.models import User


class Contact(TenantOwnedModel):
    """
    Contact model represents an individual person.
    Contacts can be associated with accounts (companies).
    Migrated to use TenantOwnedModel for enhanced multi-tenancy.
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
    email = models.EmailField(blank=True, validators=[EmailValidator()])
    phone = models.CharField(max_length=50, blank=True)
    mobile = models.CharField(max_length=50, blank=True)
    fax = models.CharField(max_length=50, blank=True)
    
    # Social Media
    linkedin_url = models.URLField(blank=True)
    twitter_handle = models.CharField(max_length=100, blank=True)
    facebook_url = models.URLField(blank=True)
    
    # Relationships
    account = models.ForeignKey(
        'crm_accounts.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contacts',
        help_text="Company/Account this contact belongs to"
    )
    reports_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='direct_reports',
        help_text="Manager/supervisor of this contact"
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_contacts',
        help_text="Sales rep who owns this contact"
    )
    
    # Mailing Address
    mailing_address_line1 = models.CharField(max_length=255, blank=True)
    mailing_address_line2 = models.CharField(max_length=255, blank=True)
    mailing_city = models.CharField(max_length=100, blank=True)
    mailing_state = models.CharField(max_length=100, blank=True)
    mailing_postal_code = models.CharField(max_length=20, blank=True)
    mailing_country = models.CharField(max_length=100, blank=True)
    
    # Other Address (if different from mailing)
    other_address_line1 = models.CharField(max_length=255, blank=True)
    other_address_line2 = models.CharField(max_length=255, blank=True)
    other_city = models.CharField(max_length=100, blank=True)
    other_state = models.CharField(max_length=100, blank=True)
    other_postal_code = models.CharField(max_length=20, blank=True)
    other_country = models.CharField(max_length=100, blank=True)
    
    # Preferences
    email_opt_out = models.BooleanField(
        default=False,
        help_text="Contact has opted out of email communications"
    )
    do_not_call = models.BooleanField(
        default=False,
        help_text="Contact prefers not to be called"
    )
    preferred_contact_method = models.CharField(
        max_length=50,
        choices=[
            ('email', 'Email'),
            ('phone', 'Phone'),
            ('mobile', 'Mobile'),
            ('meeting', 'In-person Meeting'),
        ],
        blank=True
    )
    
    # Classification
    contact_type = models.CharField(
        max_length=50,
        choices=[
            ('decision_maker', 'Decision Maker'),
            ('influencer', 'Influencer'),
            ('technical', 'Technical Contact'),
            ('administrative', 'Administrative'),
            ('billing', 'Billing Contact'),
        ],
        blank=True,
        db_index=True
    )
    
    # Custom Fields (JSON for flexibility)
    custom_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Custom field values stored as JSON"
    )
    
    # Legacy compatibility
    custom_fields = models.JSONField(null=True, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True, db_index=True)
    
    # Description/Notes
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'crm_contact'
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['organization', 'last_name', 'first_name']),
            models.Index(fields=['organization', 'email']),
            models.Index(fields=['organization', 'account']),
            models.Index(fields=['organization', 'owner']),
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['organization', '-created_at']),
        ]
    
    def __str__(self):
        return self.full_name or f"{self.first_name} {self.last_name}".strip()
    
    def save(self, *args, **kwargs):
        # Auto-generate full_name
        if not self.full_name:
            self.full_name = f"{self.first_name} {self.last_name}".strip()
        
        super().save(*args, **kwargs)
    
    def get_full_address(self, address_type='mailing'):
        """Get formatted address"""
        if address_type == 'mailing':
            parts = [
                self.mailing_address_line1,
                self.mailing_address_line2,
                self.mailing_city,
                self.mailing_state,
                self.mailing_postal_code,
                self.mailing_country
            ]
        else:
            parts = [
                self.other_address_line1,
                self.other_address_line2,
                self.other_city,
                self.other_state,
                self.other_postal_code,
                self.other_country
            ]
        
        return ', '.join([p for p in parts if p])
