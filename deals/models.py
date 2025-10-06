# deals/models.py
# Deals Models

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from core.models import CompanyIsolatedModel, User
from crm.models import Account, Contact, Lead

class Deal(CompanyIsolatedModel):
    """
    Deal/Opportunity model for sales pipeline management.
    """
    
    STAGE_CHOICES = [
        ('prospecting', 'Prospecting'),
        ('qualification', 'Qualification'),
        ('proposal', 'Proposal'),
        ('negotiation', 'Negotiation'),
        ('closed_won', 'Closed Won'),
        ('closed_lost', 'Closed Lost'),
    ]
    
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
        ('critical', 'Critical'),
    ]
    
    SOURCE_CHOICES = [
        ('website', 'Website'),
        ('referral', 'Referral'),
        ('cold_call', 'Cold Call'),
        ('email', 'Email'),
        ('social_media', 'Social Media'),
        ('event', 'Event'),
        ('partner', 'Partner'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    
    # Financial Information
    amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='USD')
    probability = models.IntegerField(default=0, help_text="Probability percentage")
    expected_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Expected revenue (amount * probability)"
    )
    
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
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_deals',
        help_text="Sales rep who owns this deal"
    )
    lead = models.ForeignKey(
        Lead,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deals',
        help_text="Originating lead"
    )
    territory = models.ForeignKey(
        'territories.Territory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deals'
    )
    
    # Pipeline Information
    stage = models.CharField(
        max_length=50,
        choices=STAGE_CHOICES,
        default='prospecting',
        db_index=True
    )
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='open',
        db_index=True
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    source = models.CharField(
        max_length=50,
        choices=SOURCE_CHOICES,
        blank=True
    )
    
    # Additional Information
    competitor = models.CharField(max_length=255, blank=True)
    next_step = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Dates
    expected_close_date = models.DateField(null=True, blank=True)
    actual_close_date = models.DateField(null=True, blank=True)
    
    # Metadata
    tags = models.ManyToManyField('master_data.Tag', blank=True, related_name='deals')
    metadata = models.JSONField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    # Custom Fields
    custom_fields = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'deals'
        verbose_name = 'Deal'
        verbose_name_plural = 'Deals'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    @property
    def weighted_amount(self):
        """Calculate weighted amount based on probability."""
        if self.amount and self.probability:
            return (self.amount * self.probability) / 100
        return 0
    
    def save(self, *args, **kwargs):
        # Auto-calculate expected revenue
        if self.amount and self.probability:
            self.expected_revenue = self.weighted_amount
        super().save(*args, **kwargs)


class Pipeline(CompanyIsolatedModel):
    """
    Sales pipeline configuration.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_default = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'pipelines'
        verbose_name = 'Pipeline'
        verbose_name_plural = 'Pipelines'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class PipelineStage(CompanyIsolatedModel):
    """
    Individual stage within a pipeline.
    """
    pipeline = models.ForeignKey(
        Pipeline,
        on_delete=models.CASCADE,
        related_name='stages',
        null=True,
        blank=True,
        help_text="Pipeline this stage belongs to"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    sequence = models.IntegerField(
        default=0,
        help_text="Order of stage in pipeline"
    )
    probability = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Win probability percentage"
    )
    is_closed = models.BooleanField(
        default=False,
        help_text="Whether this is a closing stage"
    )
    is_won = models.BooleanField(
        default=False,
        help_text="Whether this stage represents a won deal"
    )
    wip_limit = models.IntegerField(
        null=True,
        blank=True,
        help_text="Work in progress limit (optional)"
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'pipeline_stages'
        verbose_name = 'Pipeline Stage'
        verbose_name_plural = 'Pipeline Stages'
        ordering = ['sequence']
        unique_together = [['company', 'pipeline', 'sequence']]
    
    def __str__(self):
        return f"{self.name} ({self.sequence})"


class DealProduct(CompanyIsolatedModel):
    """
    Product line items associated with a deal.
    """
    deal = models.ForeignKey(
        Deal,
        on_delete=models.CASCADE,
        related_name='products'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='deal_items'
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1
    )
    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    tax_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    class Meta:
        db_table = 'deal_products'
        verbose_name = 'Deal Product'
        verbose_name_plural = 'Deal Products'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.deal.name} - {self.product.name}"
    
    @property
    def subtotal(self):
        """Calculate subtotal before discount and tax."""
        return self.quantity * self.unit_price
    
    @property
    def discount_amount(self):
        """Calculate discount amount."""
        return self.subtotal * (self.discount_percent / 100)
    
    @property
    def tax_amount(self):
        """Calculate tax amount."""
        return (self.subtotal - self.discount_amount) * (self.tax_percent / 100)
    
    @property
    def total_price(self):
        """Calculate total price including discount and tax."""
        return self.subtotal - self.discount_amount + self.tax_amount


class DealActivity(CompanyIsolatedModel):
    """
    Activities and interactions associated with a deal.
    """
    ACTIVITY_TYPE_CHOICES = [
        ('call', 'Call'),
        ('meeting', 'Meeting'),
        ('email', 'Email'),
        ('note', 'Note'),
        ('task', 'Task'),
        ('demo', 'Demo'),
        ('presentation', 'Presentation'),
    ]
    
    deal = models.ForeignKey(
        Deal,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    activity_type = models.CharField(
        max_length=50,
        choices=ACTIVITY_TYPE_CHOICES
    )
    subject = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    activity_date = models.DateTimeField()
    duration_minutes = models.IntegerField(
        null=True,
        blank=True,
        help_text="Duration in minutes"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='deal_activities'
    )
    participants = models.ManyToManyField(
        User,
        blank=True,
        related_name='participated_activities'
    )
    
    class Meta:
        db_table = 'deal_activities'
        verbose_name = 'Deal Activity'
        verbose_name_plural = 'Deal Activities'
        ordering = ['-activity_date']
    
    def __str__(self):
        return f"{self.activity_type}: {self.subject}"


class DealForecast(CompanyIsolatedModel):
    """
    Sales forecast data for deals.
    """
    FORECAST_PERIOD_CHOICES = [
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]
    
    CONFIDENCE_LEVEL_CHOICES = [
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    
    deal = models.ForeignKey(
        Deal,
        on_delete=models.CASCADE,
        related_name='forecasts'
    )
    forecast_period = models.CharField(
        max_length=20,
        choices=FORECAST_PERIOD_CHOICES
    )
    forecast_date = models.DateField()
    forecast_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )
    confidence_level = models.CharField(
        max_length=20,
        choices=CONFIDENCE_LEVEL_CHOICES
    )
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'deal_forecasts'
        verbose_name = 'Deal Forecast'
        verbose_name_plural = 'Deal Forecasts'
        ordering = ['-forecast_date']
    
    def __str__(self):
        return f"{self.deal.name} - {self.forecast_period} forecast"