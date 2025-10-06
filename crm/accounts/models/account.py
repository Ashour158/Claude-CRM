# crm/accounts/models/account.py
# Account domain model with enhanced tenancy support

from django.db import models
from django.core.validators import EmailValidator
from crm.tenancy import TenantOwnedModel
from core.models import User


class Account(TenantOwnedModel):
    """
    Account model represents a company/organization customer or prospect.
    Inherits multi-tenant capabilities from TenantOwnedModel.
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
    primary_email = models.EmailField(blank=True, validators=[EmailValidator()])
    
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
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_accounts_v2'
    )
    
    # Status
    status = models.CharField(
        max_length=50,
        choices=[
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('prospect', 'Prospect'),
        ],
        default='active',
        db_index=True
    )
    is_active = models.BooleanField(default=True, db_index=True)
    
    # Custom Data (JSON field for flexibility)
    custom_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Custom field values stored as JSON"
    )
    
    # Description/Notes
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'crm_accounts_v2'
        verbose_name = 'Account'
        verbose_name_plural = 'Accounts'
        ordering = ['name']
        indexes = [
            models.Index(fields=['organization', 'name']),
            models.Index(fields=['organization', 'type']),
            models.Index(fields=['organization', 'owner']),
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['organization', 'created_at']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Auto-generate account number if not provided
        if not self.account_number:
            # Get the last account number for this organization
            last_account = Account.objects.filter(
                organization=self.organization
            ).order_by('-created_at').first()
            
            if last_account and last_account.account_number:
                try:
                    last_num = int(last_account.account_number.split('-')[-1])
                    self.account_number = f"ACC-{last_num + 1:06d}"
                except:
                    self.account_number = f"ACC-000001"
            else:
                self.account_number = f"ACC-000001"
        
        super().save(*args, **kwargs)
    
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
