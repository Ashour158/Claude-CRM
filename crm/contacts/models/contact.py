# crm/contacts/models/contact.py
"""
Contact model for CRM - represents individuals
"""
from django.db import models
from crm.core.tenancy.mixins import TenantOwnedModel
from crm.core.tenancy.managers import TenantManager


class Contact(TenantOwnedModel):
    """
    Contact represents an individual person in the CRM.
    Can be associated with an Account.
    """
    
    SALUTATION_CHOICES = [
        ('mr', 'Mr.'),
        ('ms', 'Ms.'),
        ('mrs', 'Mrs.'),
        ('dr', 'Dr.'),
        ('prof', 'Prof.'),
    ]
    
    # Basic Information
    salutation = models.CharField(
        max_length=10,
        choices=SALUTATION_CHOICES,
        blank=True
    )
    first_name = models.CharField(max_length=100, db_index=True)
    last_name = models.CharField(max_length=100, db_index=True)
    title = models.CharField(max_length=100, blank=True, help_text="Job title")
    
    # Contact Information
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=50, blank=True)
    mobile = models.CharField(max_length=50, blank=True)
    
    # Account Relationship
    account = models.ForeignKey(
        'accounts.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contacts',
        help_text="Associated account/company"
    )
    
    # Address
    mailing_address_line1 = models.CharField(max_length=255, blank=True)
    mailing_address_line2 = models.CharField(max_length=255, blank=True)
    mailing_city = models.CharField(max_length=100, blank=True)
    mailing_state = models.CharField(max_length=100, blank=True)
    mailing_postal_code = models.CharField(max_length=20, blank=True)
    mailing_country = models.CharField(max_length=100, blank=True)
    
    # Owner
    owner = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_contacts',
        help_text="Contact owner/sales rep"
    )
    
    # Social & Additional
    linkedin_url = models.URLField(blank=True)
    twitter_handle = models.CharField(max_length=100, blank=True)
    
    # Custom Fields (JSON)
    custom_fields = models.JSONField(
        default=dict,
        blank=True,
        help_text="Custom field values stored as JSON"
    )
    
    # Status
    is_active = models.BooleanField(default=True, db_index=True)
    description = models.TextField(blank=True)
    
    # Manager
    objects = TenantManager()
    
    class Meta:
        db_table = 'crm_contact'
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['organization', 'last_name', 'first_name']),
            models.Index(fields=['organization', 'email']),
            models.Index(fields=['account', 'organization']),
        ]
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'
    
    def __str__(self):
        return self.get_full_name()
    
    def get_full_name(self):
        """Get contact's full name"""
        parts = [self.salutation, self.first_name, self.last_name]
        return ' '.join(filter(None, parts))
    
    def get_full_address(self):
        """Get formatted mailing address"""
        parts = [
            self.mailing_address_line1,
            self.mailing_address_line2,
            self.mailing_city,
            self.mailing_state,
            self.mailing_postal_code,
            self.mailing_country,
        ]
        return ', '.join(filter(None, parts))
