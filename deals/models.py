# deals/models.py
# Deals Models

from django.db import models
from core.models import CompanyIsolatedModel, User
from crm.models import Account, Contact

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
    
    # Basic Information
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    
    # Financial Information
    amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
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
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_deals',
        help_text="Sales rep who owns this deal"
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
    
    # Dates
    expected_close_date = models.DateField(null=True, blank=True)
    actual_close_date = models.DateField(null=True, blank=True)
    
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

class PipelineStage(CompanyIsolatedModel):
    """Pipeline stages for deals"""
    name = models.CharField(max_length=100)
    sequence = models.IntegerField(default=0)
    probability = models.IntegerField(default=0, help_text="Win probability percentage")
    is_closed = models.BooleanField(default=False)
    is_won = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'pipeline_stages'
        ordering = ['sequence']
        unique_together = ['company', 'name']
    
    def __str__(self):
        return self.name

class DealProduct(CompanyIsolatedModel):
    """Products associated with deals"""
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='deal_products')
    name = models.CharField(max_length=255)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1)
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    total_price = models.DecimalField(max_digits=15, decimal_places=2)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    class Meta:
        db_table = 'deal_products'
    
    def __str__(self):
        return f"{self.name} - {self.deal.name}"

class DealActivity(CompanyIsolatedModel):
    """Activities related to deals"""
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='deal_activities')
    activity_type = models.CharField(max_length=50)
    subject = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        db_table = 'deal_activities'
        verbose_name_plural = 'Deal Activities'
    
    def __str__(self):
        return f"{self.activity_type} - {self.deal.name}"

class DealForecast(CompanyIsolatedModel):
    """Deal forecast tracking"""
    deal = models.ForeignKey(Deal, on_delete=models.CASCADE, related_name='forecasts')
    forecast_date = models.DateField()
    forecasted_amount = models.DecimalField(max_digits=15, decimal_places=2)
    forecasted_close_date = models.DateField()
    probability = models.IntegerField()
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'deal_forecasts'
    
    def __str__(self):
        return f"Forecast for {self.deal.name} - {self.forecast_date}"