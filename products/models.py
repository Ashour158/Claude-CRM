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


class ProductVariant(CompanyIsolatedModel):
    """
    Product variant model for product variations.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants'
    )
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True, db_index=True)
    attributes = models.JSONField(
        default=dict,
        help_text="Variant attributes like size, color, etc."
    )
    unit_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    cost_price = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    stock_quantity = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'product_variants'
        verbose_name = 'Product Variant'
        verbose_name_plural = 'Product Variants'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.product.name} - {self.name}"


class PriceListItem(CompanyIsolatedModel):
    """
    Individual items in a price list.
    """
    price_list = models.ForeignKey(
        PriceList,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='price_list_items'
    )
    unit_price = models.DecimalField(max_digits=15, decimal_places=2)
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    min_quantity = models.IntegerField(default=1)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'price_list_items'
        verbose_name = 'Price List Item'
        verbose_name_plural = 'Price List Items'
        unique_together = [['price_list', 'product']]
    
    def __str__(self):
        return f"{self.price_list.name} - {self.product.name}"


class InventoryTransaction(CompanyIsolatedModel):
    """
    Inventory transaction tracking.
    """
    TRANSACTION_TYPE_CHOICES = [
        ('in', 'Stock In'),
        ('out', 'Stock Out'),
        ('adjustment', 'Adjustment'),
        ('return', 'Return'),
    ]
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='inventory_transactions'
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    quantity = models.IntegerField()
    reference = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    transaction_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'inventory_transactions'
        verbose_name = 'Inventory Transaction'
        verbose_name_plural = 'Inventory Transactions'
        ordering = ['-transaction_date']
    
    def __str__(self):
        return f"{self.product.name} - {self.transaction_type} ({self.quantity})"


class ProductReview(CompanyIsolatedModel):
    """
    Product reviews and ratings.
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    reviewer_name = models.CharField(max_length=255)
    reviewer_email = models.EmailField()
    rating = models.IntegerField(
        choices=[(i, i) for i in range(1, 6)],
        help_text="Rating from 1 to 5"
    )
    title = models.CharField(max_length=255)
    review_text = models.TextField()
    is_verified = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'product_reviews'
        verbose_name = 'Product Review'
        verbose_name_plural = 'Product Reviews'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.product.name} - {self.rating} stars"


class ProductBundle(CompanyIsolatedModel):
    """
    Product bundles for selling multiple products together.
    """
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    sku = models.CharField(max_length=100, unique=True, db_index=True)
    bundle_price = models.DecimalField(max_digits=15, decimal_places=2)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'product_bundles'
        verbose_name = 'Product Bundle'
        verbose_name_plural = 'Product Bundles'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class BundleItem(CompanyIsolatedModel):
    """
    Items within a product bundle.
    """
    bundle = models.ForeignKey(
        ProductBundle,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='bundle_items'
    )
    quantity = models.IntegerField(default=1)
    
    class Meta:
        db_table = 'bundle_items'
        verbose_name = 'Bundle Item'
        verbose_name_plural = 'Bundle Items'
        unique_together = [['bundle', 'product']]
    
    def __str__(self):
        return f"{self.bundle.name} - {self.product.name}"