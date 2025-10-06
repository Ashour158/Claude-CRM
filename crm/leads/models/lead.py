# crm/leads/models/lead.py
"""
Lead model for CRM - represents potential customers
"""
from django.db import models
from django.utils import timezone
from crm.core.tenancy.mixins import TenantOwnedModel
from crm.core.tenancy.managers import TenantManager


class Lead(TenantOwnedModel):
    """
    Lead represents a potential customer or sales opportunity.
    Can be converted to Account, Contact, and Deal.
    """
    
    LEAD_STATUS_CHOICES = [
        ('new', 'New'),
        ('contacted', 'Contacted'),
        ('qualified', 'Qualified'),
        ('unqualified', 'Unqualified'),
        ('converted', 'Converted'),
        ('lost', 'Lost'),
    ]
    
    LEAD_SOURCE_CHOICES = [
        ('website', 'Website'),
        ('referral', 'Referral'),
        ('email', 'Email Campaign'),
        ('social', 'Social Media'),
        ('event', 'Event'),
        ('cold_call', 'Cold Call'),
        ('partner', 'Partner'),
        ('other', 'Other'),
    ]
    
    RATING_CHOICES = [
        ('hot', 'Hot'),
        ('warm', 'Warm'),
        ('cold', 'Cold'),
    ]
    
    # Basic Information
    first_name = models.CharField(max_length=100, db_index=True)
    last_name = models.CharField(max_length=100, db_index=True)
    company_name = models.CharField(max_length=255, blank=True, db_index=True)
    title = models.CharField(max_length=100, blank=True, help_text="Job title")
    
    # Contact Information
    email = models.EmailField(db_index=True)
    phone = models.CharField(max_length=50, blank=True)
    mobile = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    
    # Lead Details
    lead_status = models.CharField(
        max_length=20,
        choices=LEAD_STATUS_CHOICES,
        default='new',
        db_index=True
    )
    lead_source = models.CharField(
        max_length=50,
        choices=LEAD_SOURCE_CHOICES,
        blank=True,
        db_index=True
    )
    rating = models.CharField(
        max_length=10,
        choices=RATING_CHOICES,
        blank=True,
        db_index=True
    )
    lead_score = models.IntegerField(default=0, help_text="Auto-calculated lead score")
    
    # Business Information
    industry = models.CharField(max_length=100, blank=True)
    annual_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    employee_count = models.IntegerField(null=True, blank=True)
    
    # Address
    address_line1 = models.CharField(max_length=255, blank=True)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    # Territory & Owner
    territory = models.ForeignKey(
        'territories.Territory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leads'
    )
    owner = models.ForeignKey(
        'core.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_leads',
        help_text="Lead owner/sales rep"
    )
    
    # Conversion tracking
    converted_at = models.DateTimeField(null=True, blank=True)
    converted_account = models.ForeignKey(
        'accounts.Account',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='converted_leads'
    )
    converted_contact = models.ForeignKey(
        'contacts.Contact',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='converted_leads'
    )
    converted_deal = models.ForeignKey(
        'deals.Deal',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='converted_leads'
    )
    
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
        db_table = 'crm_lead'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['organization', 'last_name', 'first_name']),
            models.Index(fields=['organization', 'lead_status']),
            models.Index(fields=['organization', 'lead_source']),
            models.Index(fields=['organization', 'rating']),
        ]
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.company_name}"
    
    def get_full_name(self):
        """Get lead's full name"""
        return f"{self.first_name} {self.last_name}"
    
    def is_converted(self):
        """Check if lead has been converted"""
        return self.lead_status == 'converted'
    
    @property
    def days_since_creation(self):
        """Calculate days since lead was created"""
        if self.created_at:
            delta = timezone.now() - self.created_at
            return delta.days
        return 0
