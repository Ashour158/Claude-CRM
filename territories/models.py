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
    hierarchy_level = models.IntegerField(
        default=0,
        help_text="Depth level in hierarchy tree (0 = root)"
    )
    hierarchy_path = models.CharField(
        max_length=500,
        blank=True,
        help_text="Full path in hierarchy (e.g., /north-america/west/california/)"
    )
    
    # Sharing and Roll-up
    share_with_parent = models.BooleanField(
        default=True,
        help_text="Share records with parent territory"
    )
    share_with_children = models.BooleanField(
        default=False,
        help_text="Share records with child territories"
    )
    recursive_sharing = models.BooleanField(
        default=False,
        help_text="Recursively share with all descendants"
    )
    rollup_metrics = models.BooleanField(
        default=True,
        help_text="Roll up metrics to parent territories"
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
    
    def get_all_children(self, include_self=False):
        """Get all child territories recursively"""
        children = []
        if include_self:
            children.append(self)
        
        for child in self.sub_territories.all():
            children.append(child)
            children.extend(child.get_all_children(include_self=False))
        
        return children
    
    def get_all_parents(self, include_self=False):
        """Get all parent territories recursively"""
        parents = []
        if include_self:
            parents.append(self)
        
        current = self.parent_territory
        while current:
            parents.append(current)
            current = current.parent_territory
        
        return parents
    
    def update_hierarchy_path(self):
        """Update hierarchy path based on parent"""
        if self.parent_territory:
            parent_path = self.parent_territory.hierarchy_path or '/'
            self.hierarchy_path = f"{parent_path}{self.code}/"
            self.hierarchy_level = self.parent_territory.hierarchy_level + 1
        else:
            self.hierarchy_path = f"/{self.code}/"
            self.hierarchy_level = 0
        self.save(update_fields=['hierarchy_path', 'hierarchy_level'])