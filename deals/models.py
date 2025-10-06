# deals/models.py
# Deals Models

from django.db import models
from django.utils import timezone
from core.models import CompanyIsolatedModel, User
from crm.models import Account, Contact, Lead, Tag
from territories.models import Territory
from products.models import Product
import uuid

# ========================================
# PIPELINE MODELS
# ========================================

class Pipeline(CompanyIsolatedModel):
    """
    Pipeline model for organizing deal stages.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'pipeline'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class PipelineStage(CompanyIsolatedModel):
    """
    Pipeline stage model for deal progression.
    """
    pipeline = models.ForeignKey(
        Pipeline,
        on_delete=models.CASCADE,
        related_name='stages',
        null=True,
        blank=True
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    sequence = models.IntegerField(default=0, help_text="Order in pipeline", db_index=True)
    probability = models.IntegerField(default=0, help_text="Win probability percentage")
    is_closed = models.BooleanField(default=False, help_text="Stage represents closed deals")
    is_won = models.BooleanField(default=False, help_text="Stage represents won deals")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'pipeline_stage'
        ordering = ['sequence']
        indexes = [
            models.Index(fields=['sequence']),
        ]
    
    def __str__(self):
        return f"{self.name} (Seq: {self.sequence})"


# ========================================
# DEAL MODEL
# ========================================

class Deal(CompanyIsolatedModel):
    """
    Deal/Opportunity model for sales pipeline management.
    """
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('won', 'Won'),
        ('lost', 'Lost'),
        ('cancelled', 'Cancelled'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    SOURCE_CHOICES = [
        ('website', 'Website'),
        ('referral', 'Referral'),
        ('campaign', 'Campaign'),
        ('cold_call', 'Cold Call'),
        ('partner', 'Partner'),
        ('other', 'Other'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    
    # Financial Information
    amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    expected_revenue = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    probability = models.IntegerField(default=0, help_text="Probability percentage")
    
    # Relationships
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='deals',
        help_text="Associated account"
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deals',
        help_text="Primary contact"
    )
    lead = models.ForeignKey(
        Lead,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deals',
        help_text="Originating lead"
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_deals',
        help_text="Sales rep who owns this deal"
    )
    territory = models.ForeignKey(
        Territory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deals'
    )
    
    # Pipeline Information
    stage = models.ForeignKey(
        PipelineStage,
        on_delete=models.PROTECT,
        related_name='deals',
        help_text="Current pipeline stage"
    )
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='open',
        db_index=True
    )
    
    # Additional Fields
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        blank=True
    )
    competitor = models.CharField(max_length=255, blank=True)
    next_step = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Dates
    expected_close_date = models.DateField(null=True, blank=True)
    actual_close_date = models.DateField(null=True, blank=True)
    
    # Kanban Ordering
    ordering = models.IntegerField(default=0, help_text="Order within stage", db_index=True)
    
    # Soft Delete
    is_active = models.BooleanField(default=True, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    # Tags and Metadata
    tags = models.ManyToManyField(Tag, blank=True, related_name='deals')
    metadata = models.JSONField(default=dict, blank=True)
    
    # Custom Fields
    custom_fields = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'deals'
        verbose_name = 'Deal'
        verbose_name_plural = 'Deals'
        ordering = ['ordering', '-created_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['ordering']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    def soft_delete(self):
        """Soft delete the deal."""
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_active', 'deleted_at'])
    
    @property
    def weighted_amount(self):
        """Calculate weighted amount based on probability."""
        if self.amount and self.probability:
            return (self.amount * self.probability) / 100
        return 0


# ========================================
# DEAL RELATED MODELS
# ========================================

class DealProduct(CompanyIsolatedModel):
    """Products associated with deals."""
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='products')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=15, decimal_places=2)
    
    class Meta:
        db_table = 'deal_product'
    
    def __str__(self):
        return f"{self.deal.name} - {self.product.name}"
    
    def save(self, *args, **kwargs):
        # Calculate total price
        self.total_price = (self.quantity * self.unit_price) * (1 - self.discount_percent / 100)
        super().save(*args, **kwargs)


class DealActivity(CompanyIsolatedModel):
    """Activities specific to deals."""
    ACTIVITY_TYPES = [
        ('call', 'Phone Call'),
        ('email', 'Email'),
        ('meeting', 'Meeting'),
        ('demo', 'Demo'),
        ('proposal', 'Proposal'),
        ('follow_up', 'Follow Up'),
        ('note', 'Note'),
    ]
    
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    subject = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    activity_date = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    participants = models.ManyToManyField(User, related_name='deal_activities', blank=True)
    
    class Meta:
        db_table = 'deal_activity'
        ordering = ['-activity_date']
        verbose_name_plural = 'Deal Activities'
    
    def __str__(self):
        return f"{self.deal.name} - {self.subject}"


class DealForecast(CompanyIsolatedModel):
    """Deal forecasting data."""
    FORECAST_PERIODS = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='forecasts')
    forecast_period = models.CharField(max_length=20, choices=FORECAST_PERIODS)
    forecast_date = models.DateField()
    forecast_amount = models.DecimalField(max_digits=15, decimal_places=2)
    confidence_level = models.IntegerField(help_text="Confidence percentage")
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'deal_forecast'
        ordering = ['-forecast_date']
    
    def __str__(self):
        return f"{self.deal.name} - {self.forecast_period}"