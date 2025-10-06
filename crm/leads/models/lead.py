# crm/leads/models/lead.py
# Lead model with row-level multi-tenancy

from django.db import models
from django.core.validators import EmailValidator
from django.utils import timezone
from core.tenant_models import TenantOwnedModel
from core.models import User
from territories.models import Territory


class Lead(TenantOwnedModel):
    """
    Lead model represents a potential customer.
    Leads can be converted to Account + Contact + Deal.
    Migrated to use TenantOwnedModel for enhanced multi-tenancy.
    """
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('unqualified', 'Unqualified'),
        ('converted', 'Converted'),
    ]
    
    RATING_CHOICES = [
        ('hot', 'Hot'),
        ('warm', 'Warm'),
        ('cold', 'Cold'),
    ]
    
    SOURCE_CHOICES = [
        ('website', 'Website'),
        ('referral', 'Referral'),
        ('cold_call', 'Cold Call'),
        ('trade_show', 'Trade Show'),
        ('email_campaign', 'Email Campaign'),
        ('social_media', 'Social Media'),
        ('partner', 'Partner'),
        ('other', 'Other'),
    ]
    
    # Basic Information
    first_name = models.CharField(max_length=100, blank=True, db_index=True)
    last_name = models.CharField(max_length=100, blank=True, db_index=True)
    full_name = models.CharField(max_length=255, blank=True, db_index=True)
    company_name = models.CharField(max_length=255, blank=True, db_index=True)
    title = models.CharField(max_length=100, blank=True)
    
    # Contact Information
    email = models.EmailField(blank=True, validators=[EmailValidator()])
    phone = models.CharField(max_length=50, blank=True)
    mobile = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    
    # Lead Details
    source = models.CharField(
        max_length=100,
        choices=SOURCE_CHOICES,
        blank=True,
        db_index=True
    )
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='new',
        db_index=True
    )
    rating = models.CharField(
        max_length=20,
        choices=RATING_CHOICES,
        blank=True,
        db_index=True,
        help_text="How hot is this lead?"
    )
    
    # Lead Scoring
    lead_score = models.IntegerField(
        default=0,
        help_text="Automated lead score (0-100)"
    )
    
    # Address
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    # Business Information
    industry = models.CharField(max_length=100, blank=True, db_index=True)
    annual_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    employee_count = models.IntegerField(null=True, blank=True)
    
    # Relationships
    territory = models.ForeignKey(
        Territory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leads'
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_leads',
        help_text="Sales rep who owns this lead"
    )
    
    # Conversion Tracking
    converted_at = models.DateTimeField(null=True, blank=True)
    converted_account = models.ForeignKey(
        'crm_accounts.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='converted_from_leads'
    )
    converted_contact = models.ForeignKey(
        'crm_contacts.Contact',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='converted_from_leads'
    )
    
    # Campaign Tracking
    campaign_name = models.CharField(max_length=255, blank=True)
    utm_source = models.CharField(max_length=100, blank=True)
    utm_medium = models.CharField(max_length=100, blank=True)
    utm_campaign = models.CharField(max_length=100, blank=True)
    
    # Qualification
    budget = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated budget"
    )
    timeline = models.CharField(
        max_length=100,
        blank=True,
        help_text="Purchase timeline"
    )
    
    # Description/Notes
    description = models.TextField(blank=True)
    
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
    
    class Meta:
        db_table = 'crm_lead'
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['organization', 'rating']),
            models.Index(fields=['organization', 'source']),
            models.Index(fields=['organization', 'owner']),
            models.Index(fields=['organization', 'territory']),
            models.Index(fields=['organization', 'email']),
            models.Index(fields=['organization', 'is_active']),
            models.Index(fields=['organization', '-created_at']),
        ]
    
    def __str__(self):
        if self.full_name:
            return self.full_name
        elif self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.company_name or f"Lead #{self.id}"
    
    def save(self, *args, **kwargs):
        # Auto-generate full_name
        if not self.full_name and (self.first_name or self.last_name):
            self.full_name = f"{self.first_name} {self.last_name}".strip()
        
        super().save(*args, **kwargs)
    
    def get_full_address(self):
        """Get formatted address"""
        parts = [
            self.address_line1,
            self.address_line2,
            self.city,
            self.state,
            self.postal_code,
            self.country
        ]
        return ', '.join([p for p in parts if p])
    
    @property
    def is_hot(self):
        """Check if lead is hot"""
        return self.rating == 'hot'
    
    @property
    def is_qualified(self):
        """Check if lead is qualified"""
        return self.status == 'qualified'
    
    @property
    def days_since_creation(self):
        """Calculate days since lead was created"""
        if not self.created_at:
            return 0
        delta = timezone.now() - self.created_at
        return delta.days
