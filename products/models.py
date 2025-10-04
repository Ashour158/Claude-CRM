# products/models.py
from django.db import models
from django.contrib.auth import get_user_model
from core.models import CompanyIsolatedModel
import uuid

User = get_user_model()

class ProductCategory(CompanyIsolatedModel):
    """
    Product categories for organizing products
    """
    name = models.CharField(max_length=100, help_text="Category name")
    description = models.TextField(blank=True, help_text="Category description")
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        help_text="Parent category for hierarchical structure"
    )
    image_url = models.URLField(blank=True, help_text="Category image URL")
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ('company', 'name')
        verbose_name_plural = "Product Categories"
    
    def __str__(self):
        return self.name
    
    @property
    def full_path(self):
        """Get full category path (e.g., 'Electronics > Phones > Smartphones')"""
        path = [self.name]
        parent = self.parent
        while parent:
            path.insert(0, parent.name)
            parent = parent.parent
        return ' > '.join(path)

class Product(CompanyIsolatedModel):
    """
    Product catalog with pricing and inventory
    """
    PRODUCT_TYPES = [
        ('product', 'Product'),
        ('service', 'Service'),
        ('digital', 'Digital Product'),
        ('subscription', 'Subscription'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('discontinued', 'Discontinued'),
        ('draft', 'Draft'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255, help_text="Product name")
    sku = models.CharField(
        max_length=100,
        unique=True,
        help_text="Stock Keeping Unit (SKU)"
    )
    description = models.TextField(blank=True, help_text="Product description")
    short_description = models.CharField(
        max_length=500,
        blank=True,
        help_text="Short product description"
    )
    
    # Product Details
    product_type = models.CharField(
        max_length=20,
        choices=PRODUCT_TYPES,
        default='product'
    )
    category = models.ForeignKey(
        ProductCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        help_text="Product category"
    )
    
    # Pricing
    base_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Base price of the product"
    )
    currency = models.CharField(max_length=3, default='USD', help_text="Currency code")
    cost_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Cost price for margin calculation"
    )
    
    # Inventory
    track_inventory = models.BooleanField(
        default=True,
        help_text="Whether to track inventory for this product"
    )
    stock_quantity = models.PositiveIntegerField(
        default=0,
        help_text="Current stock quantity"
    )
    min_stock_level = models.PositiveIntegerField(
        default=0,
        help_text="Minimum stock level for alerts"
    )
    max_stock_level = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum stock level"
    )
    
    # Physical Properties
    weight = models.DecimalField(
        max_digits=8,
        decimal_places=3,
        null=True,
        blank=True,
        help_text="Product weight in kg"
    )
    dimensions = models.CharField(
        max_length=100,
        blank=True,
        help_text="Product dimensions (L x W x H)"
    )
    
    # Media
    image_url = models.URLField(blank=True, help_text="Main product image URL")
    gallery_urls = models.JSONField(
        default=list,
        blank=True,
        help_text="Additional product images"
    )
    
    # SEO
    meta_title = models.CharField(
        max_length=255,
        blank=True,
        help_text="SEO meta title"
    )
    meta_description = models.TextField(
        blank=True,
        help_text="SEO meta description"
    )
    slug = models.SlugField(
        unique=True,
        help_text="URL-friendly product name"
    )
    
    # Status and Visibility
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    is_featured = models.BooleanField(
        default=False,
        help_text="Is this a featured product?"
    )
    is_digital = models.BooleanField(
        default=False,
        help_text="Is this a digital product?"
    )
    
    # Assignment
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_products',
        help_text="Product owner/manager"
    )
    
    # Metadata
    tags = models.ManyToManyField('crm.Tag', blank=True, related_name='products')
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'category']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'product_type']),
            models.Index(fields=['company', 'is_featured']),
            models.Index(fields=['company', 'sku']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.sku})"
    
    @property
    def margin_percentage(self):
        """Calculate profit margin percentage"""
        if self.cost_price and self.base_price:
            return ((self.base_price - self.cost_price) / self.base_price) * 100
        return 0
    
    @property
    def is_low_stock(self):
        """Check if product is low on stock"""
        return self.track_inventory and self.stock_quantity <= self.min_stock_level
    
    @property
    def is_out_of_stock(self):
        """Check if product is out of stock"""
        return self.track_inventory and self.stock_quantity <= 0

class ProductVariant(CompanyIsolatedModel):
    """
    Product variants (size, color, etc.)
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='variants'
    )
    name = models.CharField(max_length=255, help_text="Variant name (e.g., 'Red - Large')")
    sku = models.CharField(
        max_length=100,
        unique=True,
        help_text="Variant SKU"
    )
    price_adjustment = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Price adjustment from base price"
    )
    stock_quantity = models.PositiveIntegerField(
        default=0,
        help_text="Variant stock quantity"
    )
    attributes = models.JSONField(
        default=dict,
        blank=True,
        help_text="Variant attributes (color, size, etc.)"
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        unique_together = ('product', 'sku')
    
    def __str__(self):
        return f"{self.product.name} - {self.name}"
    
    @property
    def total_price(self):
        """Calculate total price including adjustment"""
        return self.product.base_price + self.price_adjustment

class PriceList(CompanyIsolatedModel):
    """
    Price lists for different customer segments
    """
    name = models.CharField(max_length=255, help_text="Price list name")
    description = models.TextField(blank=True, help_text="Price list description")
    currency = models.CharField(max_length=3, default='USD', help_text="Currency code")
    is_default = models.BooleanField(
        default=False,
        help_text="Is this the default price list?"
    )
    is_active = models.BooleanField(default=True)
    valid_from = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Price list valid from date"
    )
    valid_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Price list valid until date"
    )
    
    class Meta:
        ordering = ['name']
        unique_together = ('company', 'name')
    
    def __str__(self):
        return self.name

class PriceListItem(CompanyIsolatedModel):
    """
    Individual items in price lists
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
    price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Price for this product in this price list"
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Discount percentage (0-100)"
    )
    min_quantity = models.PositiveIntegerField(
        default=1,
        help_text="Minimum quantity for this price"
    )
    max_quantity = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Maximum quantity for this price"
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['product__name']
        unique_together = ('price_list', 'product')
    
    def __str__(self):
        return f"{self.price_list.name} - {self.product.name}"
    
    @property
    def discounted_price(self):
        """Calculate price after discount"""
        discount_amount = (self.price * self.discount_percentage) / 100
        return self.price - discount_amount

class InventoryTransaction(CompanyIsolatedModel):
    """
    Inventory movement transactions
    """
    TRANSACTION_TYPES = [
        ('in', 'Stock In'),
        ('out', 'Stock Out'),
        ('adjustment', 'Adjustment'),
        ('transfer', 'Transfer'),
        ('return', 'Return'),
    ]
    
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='inventory_transactions'
    )
    transaction_type = models.CharField(
        max_length=20,
        choices=TRANSACTION_TYPES
    )
    quantity = models.IntegerField(help_text="Quantity change (positive for in, negative for out)")
    reference = models.CharField(
        max_length=255,
        blank=True,
        help_text="Reference (PO number, SO number, etc.)"
    )
    notes = models.TextField(blank=True, help_text="Transaction notes")
    
    # Related entities
    related_quote = models.ForeignKey(
        'sales.Quote',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_transactions'
    )
    related_order = models.ForeignKey(
        'sales.SalesOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='inventory_transactions'
    )
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'product']),
            models.Index(fields=['company', 'transaction_type']),
            models.Index(fields=['company', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.product.name} - {self.get_transaction_type_display()} ({self.quantity})"

class ProductReview(CompanyIsolatedModel):
    """
    Product reviews and ratings
    """
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    reviewer_name = models.CharField(max_length=255, help_text="Reviewer name")
    reviewer_email = models.EmailField(help_text="Reviewer email")
    rating = models.PositiveIntegerField(
        choices=[(i, i) for i in range(1, 6)],
        help_text="Rating from 1 to 5"
    )
    title = models.CharField(max_length=255, help_text="Review title")
    content = models.TextField(help_text="Review content")
    is_verified = models.BooleanField(
        default=False,
        help_text="Is this a verified purchase review?"
    )
    is_approved = models.BooleanField(
        default=False,
        help_text="Is this review approved for display?"
    )
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ('product', 'reviewer_email')
    
    def __str__(self):
        return f"{self.product.name} - {self.rating} stars by {self.reviewer_name}"

class ProductBundle(CompanyIsolatedModel):
    """
    Product bundles (grouped products sold together)
    """
    name = models.CharField(max_length=255, help_text="Bundle name")
    description = models.TextField(blank=True, help_text="Bundle description")
    products = models.ManyToManyField(
        Product,
        through='BundleItem',
        related_name='bundles'
    )
    bundle_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Bundle price (usually less than sum of individual products)"
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def total_individual_price(self):
        """Calculate total price if products were sold individually"""
        return sum(item.product.base_price * item.quantity for item in self.bundle_items.all())
    
    @property
    def savings_amount(self):
        """Calculate savings amount"""
        return self.total_individual_price - self.bundle_price
    
    @property
    def savings_percentage(self):
        """Calculate savings percentage"""
        if self.total_individual_price > 0:
            return (self.savings_amount / self.total_individual_price) * 100
        return 0

class BundleItem(CompanyIsolatedModel):
    """
    Items within a product bundle
    """
    bundle = models.ForeignKey(
        ProductBundle,
        on_delete=models.CASCADE,
        related_name='bundle_items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='bundle_items'
    )
    quantity = models.PositiveIntegerField(
        default=1,
        help_text="Quantity of this product in the bundle"
    )
    
    class Meta:
        unique_together = ('bundle', 'product')
    
    def __str__(self):
        return f"{self.bundle.name} - {self.product.name} x{self.quantity}"