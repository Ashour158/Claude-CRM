# territories/models.py
# Territory management models

from django.db import models
from core.models import CompanyIsolatedModel, User

class Territory(CompanyIsolatedModel):
    """Sales territory model"""
    
    TYPE_CHOICES = [
        ('geographic', 'Geographic'),
        ('industry', 'Industry'),
        ('account_size', 'Account Size'),
        ('product_line', 'Product Line'),
    ]
    
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='geographic')
    description = models.TextField(blank=True)
    
    # Geographic boundaries
    countries = models.JSONField(null=True, blank=True, help_text="List of country codes")
    states = models.JSONField(null=True, blank=True, help_text="List of state/province codes")
    cities = models.JSONField(null=True, blank=True, help_text="List of cities")
    
    # Industry/Product filters
    industries = models.JSONField(null=True, blank=True, help_text="List of industries")
    account_sizes = models.JSONField(null=True, blank=True, help_text="Account size ranges")
    product_lines = models.JSONField(null=True, blank=True, help_text="Product line IDs")
    
    # Territory hierarchy
    parent_territory = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='sub_territories'
    )
    
    # Assignment rules
    assignment_rules = models.JSONField(null=True, blank=True, help_text="Auto-assignment rules")
    
    # Territory manager
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_territories'
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'territory'
        ordering = ['name']
        indexes = [
            models.Index(fields=['company', 'name']),
            models.Index(fields=['company', 'type']),
            models.Index(fields=['company', 'manager']),
            models.Index(fields=['company', 'is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    @property
    def accounts_count(self):
        """Count of accounts in this territory"""
        return self.accounts.count()
    
    @property
    def leads_count(self):
        """Count of leads in this territory"""
        return self.leads.count()
    
    def get_territory_hierarchy(self):
        """Get full territory hierarchy"""
        hierarchy = [self]
        current = self.parent_territory
        while current:
            hierarchy.insert(0, current)
            current = current.parent_territory
        return hierarchy