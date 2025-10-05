# products/models.py
# Products Models

from django.db import models
from core.models import CompanyIsolatedModel

class ProductCategory(CompanyIsolatedModel):
    """
    Product category model for organizing products.
    """
    
    name = models.CharField(max_length=100, db_index=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text="Parent category for hierarchy"
    )
    is_active = models.BooleanField(default=True, db_index=True)
    
    class Meta:
        db_table = 'product_categories'
        verbose_name = 'Product Category'
        verbose_name_plural = 'Product Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class Product(CompanyIsolatedModel):
    """
    Product model for catalog management.
    """
    
    # Basic Information
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    sku = models.CharField(max_length=100, unique=True, db_index=True)
    
    # Pricing
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    cost_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    
    # Relationships
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    
    # Product Details
    unit_of_measure = models.CharField(max_length=50, blank=True, help_text="e.g., piece, kg, liter")
    weight = models.DecimalField(max_digits=10, decimal_places=3, null=True, blank=True)
    dimensions = models.CharField(max_length=100, blank=True, help_text="L x W x H")
    
    # Status
    is_active = models.BooleanField(default=True, db_index=True)
    is_digital = models.BooleanField(default=False, help_text="Digital product flag")
    
    # Custom Fields
    custom_fields = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'products'
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['name']
    
    def __str__(self):
        return self.name

class PriceList(CompanyIsolatedModel):
    """
    Price list model for managing product pricing.
    """
    
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    currency = models.CharField(max_length=3, default='USD')
    is_active = models.BooleanField(default=True, db_index=True)
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)
    
    class Meta:
        db_table = 'price_lists'
        verbose_name = 'Price List'
        verbose_name_plural = 'Price Lists'
        ordering = ['name']
    
    def __str__(self):
        return self.name