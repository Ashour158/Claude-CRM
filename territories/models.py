# territories/models.py
# Territory Management Models

from django.db import models
from core.models import CompanyIsolatedModel, User

class Territory(CompanyIsolatedModel):
    """
    Sales territories with hierarchical structure and assignment rules
    """
    
    TYPE_CHOICES = [
        ('geographic', 'Geographic'),
        ('product', 'Product-based'),
        ('customer_segment', 'Customer Segment'),
        ('industry', 'Industry'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255, db_index=True)
    code = models.CharField(max_length=50, db_index=True)
    description = models.TextField(blank=True)
    
    # Territory Type
    type = models.CharField(
        max_length=50,
        choices=TYPE_CHOICES,
        default='geographic',
        db_index=True
    )
    
    # Hierarchy
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
        help_text="Parent territory for hierarchy"
    )
    
    # Manager
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_territories',
        help_text="Territory manager"
    )
    
    # Geographic Criteria
    countries = models.JSONField(
        null=True,
        blank=True,
        help_text="List of country codes (ISO 3166-1 alpha-3)"
    )
    states = models.JSONField(
        null=True,
        blank=True,
        help_text="List of states/provinces"
    )
    cities = models.JSONField(
        null=True,
        blank=True,
        help_text="List of cities"
    )
    postal_codes = models.JSONField(
        null=True,
        blank=True,
        help_text="List of postal codes or ranges"
    )
    
    # Product Criteria
    product_categories = models.JSONField(
        null=True,
        blank=True,
        help_text="List of product categories"
    )
    product_ids = models.JSONField(
        null=True,
        blank=True,
        help_text="List of specific product IDs"
    )
    
    # Customer Criteria
    customer_types = models.JSONField(
        null=True,
        blank=True,
        help_text="List of customer types"
    )
    revenue_min = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Minimum customer revenue"
    )
    revenue_max = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Maximum customer revenue"
    )
    industries = models.JSONField(
        null=True,
        blank=True,
        help_text="List of industries"
    )
    
    # Territory Settings
    currency = models.CharField(max_length=3, default='USD')
    quota_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Territory quota amount"
    )
    quota_period = models.CharField(
        max_length=20,
        blank=True,
        help_text="Quota period: monthly, quarterly, annual"
    )
    
    # Status
    is_active = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        db_table = 'territories'
        verbose_name = 'Territory'
        verbose_name_plural = 'Territories'
        unique_together = [['company', 'code']]
        ordering = ['name']
        indexes = [
            models.Index(fields=['company', 'type']),
            models.Index(fields=['company', 'manager']),
            models.Index(fields=['company', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    def get_full_path(self):
        """Get full territory path including parents"""
        path = [self.name]
        parent = self.parent
        while parent:
            path.insert(0, parent.name)
            parent = parent.parent
        return ' > '.join(path)
    
    def get_children_recursive(self):
        """Get all children territories recursively"""
        children = list(self.children.all())
        for child in children:
            children.extend(child.get_children_recursive())
        return children
    
    def get_all_users(self):
        """Get all users assigned to this territory and its children"""
        from core.models import UserCompanyAccess
        
        territory_ids = [self.id] + [t.id for t in self.get_children_recursive()]
        
        return User.objects.filter(
            company_access__company=self.company,
            company_access__is_active=True,
            company_access__territory_id__in=territory_ids
        ).distinct()


class TerritoryRule(CompanyIsolatedModel):
    """
    Automated territory assignment rules
    """
    
    territory = models.ForeignKey(
        Territory,
        on_delete=models.CASCADE,
        related_name='rules'
    )
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    priority = models.IntegerField(
        default=0,
        help_text="Higher priority rules run first"
    )
    
    # Rule Conditions (JSON)
    conditions = models.JSONField(
        help_text="Rule conditions in JSON format"
    )
    
    # Rule Actions
    auto_assign = models.BooleanField(
        default=True,
        help_text="Automatically assign entities to territory"
    )
    notify_manager = models.BooleanField(
        default=False,
        help_text="Notify territory manager of new assignments"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'territory_rules'
        verbose_name = 'Territory Rule'
        verbose_name_plural = 'Territory Rules'
        ordering = ['-priority', 'name']
        indexes = [
            models.Index(fields=['company', 'territory']),
            models.Index(fields=['company', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} (Priority: {self.priority})"
    
    def evaluate_conditions(self, entity_data):
        """
        Evaluate rule conditions against entity data
        Returns True if conditions match
        """
        # This would implement the rule evaluation logic
        # For now, return True as a placeholder
        return True
    
    def apply_rule(self, entity, entity_type):
        """
        Apply the rule to assign entity to territory
        """
        if self.auto_assign:
            if entity_type == 'account':
                entity.territory = self.territory
                entity.save()
            elif entity_type == 'lead':
                entity.territory = self.territory
                entity.save()
        
        if self.notify_manager and self.territory.manager:
            # Send notification to territory manager
            pass


class TerritoryAssignment(CompanyIsolatedModel):
    """
    Track territory assignments for audit and reporting
    """
    
    ENTITY_TYPE_CHOICES = [
        ('account', 'Account'),
        ('lead', 'Lead'),
        ('contact', 'Contact'),
    ]
    
    territory = models.ForeignKey(
        Territory,
        on_delete=models.CASCADE,
        related_name='assignments'
    )
    
    # Assigned Entity
    entity_type = models.CharField(
        max_length=50,
        choices=ENTITY_TYPE_CHOICES
    )
    entity_id = models.UUIDField()
    
    # Assignment Details
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='territory_assignments_made'
    )
    assignment_reason = models.CharField(
        max_length=100,
        blank=True,
        help_text="Reason for assignment: manual, rule, import"
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'territory_assignments'
        verbose_name = 'Territory Assignment'
        verbose_name_plural = 'Territory Assignments'
        unique_together = [['territory', 'entity_type', 'entity_id']]
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'territory']),
            models.Index(fields=['company', 'entity_type', 'entity_id']),
            models.Index(fields=['company', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.territory.name} - {self.entity_type} {self.entity_id}"
