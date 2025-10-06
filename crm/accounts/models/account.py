# crm/accounts/models/account.py
"""
Account model for CRM - represents companies/organizations
"""
from django.db import models
from crm.core.tenancy.mixins import TenantOwnedModel
from crm.core.tenancy.managers import TenantManager


class Account(TenantOwnedModel):
    """
    Account represents a company or organization in the CRM.
    Can be a customer, prospect, partner, or competitor.
    """
    
    TYPE_CHOICES = [
        ('customer', 'Customer'),
        ('prospect', 'Prospect'),
        ('partner', 'Partner'),
        ('competitor', 'Competitor'),
    ]
    
    INDUSTRY_CHOICES = [
        ('technology', 'Technology'),
        ('finance', 'Finance'),
        ('healthcare', 'Healthcare'),
        ('manufacturing', 'Manufacturing'),
        ('retail', 'Retail'),
        ('education', 'Education'),
        ('other', 'Other'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255, db_index=True, help_text="Company name")
    legal_name = models.CharField(max_length=255, blank=True, help_text="Legal company name")
    account_number = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        help_text="Unique account identifier"
    )
    account_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default='prospect',
        db_index=True
    )
    
    # Contact Information
    email = models.EmailField(blank=True, db_index=True)
    phone = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    
    # Business Information
    industry = models.CharField(
        max_length=50,
        choices=INDUSTRY_CHOICES,
        blank=True,
        db_index=True
    )
    annual_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Annual revenue"
    )
    employee_count = models.IntegerField(null=True, blank=True)
    
    # Address
    billing_address_line1 = models.CharField(max_length=255, blank=True)
    billing_address_line2 = models.CharField(max_length=255, blank=True)
    billing_city = models.CharField(max_length=100, blank=True)
    billing_state = models.CharField(max_length=100, blank=True)
    billing_postal_code = models.CharField(max_length=20, blank=True)
    billing_country = models.CharField(max_length=100, blank=True)
    
    # Territory & Owner
    territory = models.ForeignKey(
        'territories.Territory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='accounts'
    )
    owner = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_accounts',
        help_text="Account owner/sales rep"
    )
    
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
        db_table = 'crm_account'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'name']),
            models.Index(fields=['organization', 'account_type']),
            models.Index(fields=['organization', 'industry']),
        ]
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'
    
    def __str__(self):
        return self.name
    
    def get_full_address(self):
        """Get formatted billing address"""
        parts = [
            self.billing_address_line1,
            self.billing_address_line2,
            self.billing_city,
            self.billing_state,
            self.billing_postal_code,
            self.billing_country,
        ]
        return ', '.join(filter(None, parts))
