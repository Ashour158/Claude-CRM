# deals/models.py
from django.db import models
from django.contrib.auth import get_user_model
from core.models import CompanyIsolatedModel
import uuid

User = get_user_model()

class PipelineStage(CompanyIsolatedModel):
    """
    Defines stages in the sales pipeline (e.g., Lead, Qualification, Proposal, Negotiation, Closed Won/Lost)
    """
    name = models.CharField(max_length=100, help_text="Stage name (e.g., 'Lead', 'Qualification', 'Proposal')")
    description = models.TextField(blank=True, null=True, help_text="Stage description")
    sequence = models.PositiveIntegerField(default=0, help_text="Order in pipeline")
    probability = models.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        default=0.00,
        help_text="Default probability percentage (0-100)"
    )
    is_closed = models.BooleanField(default=False, help_text="Is this a closed stage?")
    is_won = models.BooleanField(default=False, help_text="Is this a won stage?")
    color = models.CharField(max_length=7, default="#3B82F6", help_text="Hex color for UI display")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['sequence']
        unique_together = ('company', 'name')
    
    def __str__(self):
        return f"{self.name} ({self.probability}%)"

class Deal(CompanyIsolatedModel):
    """
    Sales opportunities/deals in the pipeline
    """
    DEAL_STATUS_CHOICES = [
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
    
    # Basic Information
    name = models.CharField(max_length=255, help_text="Deal name/opportunity title")
    description = models.TextField(blank=True, null=True)
    
    # Relationships
    account = models.ForeignKey(
        'crm.Account',
        on_delete=models.CASCADE,
        related_name='deals',
        help_text="Associated account/company"
    )
    contact = models.ForeignKey(
        'crm.Contact',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deals',
        help_text="Primary contact for this deal"
    )
    lead = models.ForeignKey(
        'crm.Lead',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='converted_deals',
        help_text="Original lead if converted"
    )
    
    # Pipeline Information
    stage = models.ForeignKey(
        PipelineStage,
        on_delete=models.SET_NULL,
        null=True,
        related_name='deals',
        help_text="Current pipeline stage"
    )
    status = models.CharField(
        max_length=20,
        choices=DEAL_STATUS_CHOICES,
        default='open',
        help_text="Deal status"
    )
    
    # Financial Information
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Deal value/amount"
    )
    currency = models.CharField(max_length=3, default='USD', help_text="Currency code")
    probability = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Probability percentage (0-100)"
    )
    expected_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Expected revenue (amount * probability)"
    )
    
    # Dates
    expected_close_date = models.DateField(
        null=True,
        blank=True,
        help_text="Expected close date"
    )
    actual_close_date = models.DateField(
        null=True,
        blank=True,
        help_text="Actual close date"
    )
    
    # Assignment
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_deals',
        help_text="Deal owner/assigned user"
    )
    territory = models.ForeignKey(
        'territories.Territory',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deals',
        help_text="Sales territory"
    )
    
    # Additional Information
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='medium'
    )
    source = models.CharField(
        max_length=100,
        blank=True,
        help_text="Deal source (e.g., 'Website', 'Referral', 'Cold Call')"
    )
    competitor = models.CharField(
        max_length=100,
        blank=True,
        help_text="Main competitor"
    )
    next_step = models.TextField(
        blank=True,
        help_text="Next step/action"
    )
    notes = models.TextField(blank=True, help_text="Additional notes")
    
    # Metadata
    tags = models.ManyToManyField('crm.Tag', blank=True, related_name='deals')
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'stage']),
            models.Index(fields=['company', 'owner']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'expected_close_date']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.account.name}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate expected revenue
        if self.amount and self.probability:
            self.expected_revenue = (self.amount * self.probability) / 100
        super().save(*args, **kwargs)
    
    @property
    def days_in_stage(self):
        """Calculate days in current stage"""
        if self.stage and self.updated_at:
            from django.utils import timezone
            return (timezone.now().date() - self.updated_at.date()).days
        return 0
    
    @property
    def is_overdue(self):
        """Check if deal is overdue"""
        if self.expected_close_date and self.status == 'open':
            from django.utils import timezone
            return timezone.now().date() > self.expected_close_date
        return False

class DealProduct(CompanyIsolatedModel):
    """
    Products/services associated with a deal
    """
    deal = models.ForeignKey(
        Deal,
        on_delete=models.CASCADE,
        related_name='products'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='deal_products'
    )
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1.00
    )
    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Discount percentage (0-100)"
    )
    total_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Total price after discount"
    )
    description = models.TextField(blank=True, help_text="Product description for this deal")
    
    class Meta:
        ordering = ['created_at']
        unique_together = ('deal', 'product')
    
    def __str__(self):
        return f"{self.deal.name} - {self.product.name}"
    
    def save(self, *args, **kwargs):
        # Calculate total price
        base_price = self.quantity * self.unit_price
        discount_amount = (base_price * self.discount_percentage) / 100
        self.total_price = base_price - discount_amount
        super().save(*args, **kwargs)

class DealActivity(CompanyIsolatedModel):
    """
    Activities related to a deal (calls, emails, meetings, etc.)
    """
    ACTIVITY_TYPES = [
        ('call', 'Phone Call'),
        ('email', 'Email'),
        ('meeting', 'Meeting'),
        ('demo', 'Demo'),
        ('proposal', 'Proposal'),
        ('follow_up', 'Follow Up'),
        ('other', 'Other'),
    ]
    
    deal = models.ForeignKey(
        Deal,
        on_delete=models.CASCADE,
        related_name='activities'
    )
    activity_type = models.CharField(
        max_length=20,
        choices=ACTIVITY_TYPES
    )
    subject = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    activity_date = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Activity duration in minutes"
    )
    outcome = models.TextField(blank=True, help_text="Activity outcome/result")
    next_action = models.TextField(blank=True, help_text="Next action required")
    next_action_date = models.DateTimeField(null=True, blank=True)
    
    # Participants
    participants = models.ManyToManyField(
        User,
        blank=True,
        related_name='deal_activities'
    )
    
    class Meta:
        ordering = ['-activity_date']
    
    def __str__(self):
        return f"{self.get_activity_type_display()} - {self.subject}"

class DealForecast(CompanyIsolatedModel):
    """
    Sales forecasting data for deals
    """
    deal = models.OneToOneField(
        Deal,
        on_delete=models.CASCADE,
        related_name='forecast'
    )
    forecast_period = models.CharField(
        max_length=20,
        choices=[
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('yearly', 'Yearly'),
        ],
        default='monthly'
    )
    forecast_date = models.DateField()
    forecast_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )
    confidence_level = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=50.00,
        help_text="Confidence level percentage (0-100)"
    )
    notes = models.TextField(blank=True)
    
    class Meta:
        ordering = ['-forecast_date']
    
    def __str__(self):
        return f"{self.deal.name} - {self.forecast_date}"