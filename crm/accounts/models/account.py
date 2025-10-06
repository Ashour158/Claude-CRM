# crm/accounts/models/account.py
# Account model with row-level multi-tenancy

from django.db import models
from core.tenant_models import TenantOwnedModel
from territories.models import Territory


class Account(TenantOwnedModel):
    """
    Account model represents a company/organization.
    This is a customer, prospect, partner, or competitor.
    Migrated to use TenantOwnedModel for enhanced multi-tenancy.
    """
    
    TYPE_CHOICES = [
        ('customer', 'Customer'),
        ('prospect', 'Prospect'),
        ('partner', 'Partner'),
        ('competitor', 'Competitor'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255, db_index=True)
    legal_name = models.CharField(max_length=255, blank=True)
    account_number = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True,
        help_text="Unique account identifier"
    )
    website = models.URLField(blank=True)
    
    # Classification
    type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        blank=True,
        db_index=True
    )
    industry = models.CharField(max_length=100, blank=True, db_index=True)
    annual_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Annual revenue in company currency"
    )
    employee_count = models.IntegerField(null=True, blank=True)
    
    # Contact Information
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    
    # Billing Address
    billing_address_line1 = models.CharField(max_length=255, blank=True)
    billing_address_line2 = models.CharField(max_length=255, blank=True)
    billing_city = models.CharField(max_length=100, blank=True)
    billing_state = models.CharField(max_length=100, blank=True)
    billing_postal_code = models.CharField(max_length=20, blank=True)
    billing_country = models.CharField(max_length=100, blank=True)
    
    # Shipping Address
    shipping_address_line1 = models.CharField(max_length=255, blank=True)
    shipping_address_line2 = models.CharField(max_length=255, blank=True)
    shipping_city = models.CharField(max_length=100, blank=True)
    shipping_state = models.CharField(max_length=100, blank=True)
    shipping_postal_code = models.CharField(max_length=20, blank=True)
    shipping_country = models.CharField(max_length=100, blank=True)
    
    # Relationships
    parent_account = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='subsidiaries',
        help_text="Parent account for hierarchy"
    )
    territory = models.ForeignKey(
        Territory,
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
        related_name='owned_accounts'
    )
    
    # Financial Settings
    payment_terms = models.IntegerField(
        default=30,
        help_text="Payment terms in days"
    )
    credit_limit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    tax_id = models.CharField(max_length=100, blank=True)
    
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
        db_table = 'crm_account'
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'
        ordering = ['name']
        indexes = [
            models.Index(fields=['organization', 'name']),
            models.Index(fields=['organization', 'type']),
            models.Index(fields=['organization', 'owner']),
            models.Index(fields=['organization', 'territory']),
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['organization', '-created_at']),
        ]
    
    def __str__(self):
        return self.name
    
    def get_full_address(self, address_type='billing'):
        """Get formatted address"""
        if address_type == 'billing':
            parts = [
                self.billing_address_line1,
                self.billing_address_line2,
                self.billing_city,
                self.billing_state,
                self.billing_postal_code,
                self.billing_country
            ]
        else:
            parts = [
                self.shipping_address_line1,
                self.shipping_address_line2,
                self.shipping_city,
                self.shipping_state,
                self.shipping_postal_code,
                self.shipping_country
            ]
        
        return ', '.join([p for p in parts if p])
    
    def save(self, *args, **kwargs):
        # Auto-generate account number if not provided
        if not self.account_number:
            # Generate account number based on organization and count
            count = Account.objects.filter(organization=self.organization).count() if self.organization else 0
            self.account_number = f"ACC-{count + 1:05d}"
        
        super().save(*args, **kwargs)
