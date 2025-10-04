# vendors/models.py
from django.db import models
from django.contrib.auth import get_user_model
from core.models import CompanyIsolatedModel
import uuid

User = get_user_model()

class Vendor(CompanyIsolatedModel):
    """
    Vendor/Supplier management
    """
    VENDOR_TYPES = [
        ('supplier', 'Supplier'),
        ('service_provider', 'Service Provider'),
        ('contractor', 'Contractor'),
        ('consultant', 'Consultant'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('blacklisted', 'Blacklisted'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255, help_text="Vendor name")
    vendor_code = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique vendor code"
    )
    vendor_type = models.CharField(
        max_length=20,
        choices=VENDOR_TYPES,
        default='supplier'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    
    # Contact Information
    primary_contact_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Primary contact person name"
    )
    primary_contact_email = models.EmailField(
        blank=True,
        help_text="Primary contact email"
    )
    primary_contact_phone = models.CharField(
        max_length=50,
        blank=True,
        help_text="Primary contact phone"
    )
    
    # Business Information
    business_registration_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Business registration number"
    )
    tax_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Tax ID/VAT number"
    )
    website = models.URLField(blank=True, help_text="Vendor website")
    
    # Address Information
    billing_address = models.TextField(blank=True, help_text="Billing address")
    shipping_address = models.TextField(blank=True, help_text="Shipping address")
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)
    country = models.CharField(max_length=100, blank=True)
    
    # Financial Information
    currency = models.CharField(max_length=3, default='USD', help_text="Preferred currency")
    payment_terms = models.CharField(
        max_length=100,
        blank=True,
        help_text="Payment terms (e.g., Net 30, COD)"
    )
    credit_limit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Credit limit"
    )
    
    # Performance Metrics
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Vendor rating (1-5)"
    )
    on_time_delivery_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="On-time delivery rate percentage"
    )
    quality_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Quality rating (1-5)"
    )
    
    # Assignment
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_vendors',
        help_text="Vendor owner/manager"
    )
    
    # Additional Information
    description = models.TextField(blank=True, help_text="Vendor description")
    notes = models.TextField(blank=True, help_text="Internal notes")
    
    # Metadata
    tags = models.ManyToManyField('crm.Tag', blank=True, related_name='vendors')
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'vendor_type']),
            models.Index(fields=['company', 'owner']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.vendor_code})"
    
    def save(self, *args, **kwargs):
        if not self.vendor_code:
            # Generate vendor code
            from django.utils import timezone
            year = timezone.now().year
            count = Vendor.objects.filter(
                company=self.company,
                created_at__year=year
            ).count() + 1
            self.vendor_code = f"V{year}{count:04d}"
        super().save(*args, **kwargs)

class VendorContact(CompanyIsolatedModel):
    """
    Additional contacts for vendors
    """
    CONTACT_TYPES = [
        ('primary', 'Primary'),
        ('billing', 'Billing'),
        ('shipping', 'Shipping'),
        ('technical', 'Technical'),
        ('sales', 'Sales'),
        ('support', 'Support'),
        ('other', 'Other'),
    ]
    
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name='contacts'
    )
    contact_type = models.CharField(
        max_length=20,
        choices=CONTACT_TYPES,
        default='other'
    )
    name = models.CharField(max_length=255, help_text="Contact name")
    title = models.CharField(max_length=100, blank=True, help_text="Job title")
    email = models.EmailField(help_text="Contact email")
    phone = models.CharField(max_length=50, blank=True, help_text="Contact phone")
    mobile = models.CharField(max_length=50, blank=True, help_text="Mobile phone")
    department = models.CharField(max_length=100, blank=True, help_text="Department")
    is_primary = models.BooleanField(default=False, help_text="Is this the primary contact?")
    
    class Meta:
        ordering = ['name']
        unique_together = ('vendor', 'email')
    
    def __str__(self):
        return f"{self.name} - {self.vendor.name}"

class VendorProduct(CompanyIsolatedModel):
    """
    Products/services offered by vendors
    """
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name='products'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='vendor_products'
    )
    vendor_sku = models.CharField(
        max_length=100,
        blank=True,
        help_text="Vendor's SKU for this product"
    )
    vendor_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Vendor's price for this product"
    )
    currency = models.CharField(max_length=3, default='USD', help_text="Currency")
    minimum_order_quantity = models.PositiveIntegerField(
        default=1,
        help_text="Minimum order quantity"
    )
    lead_time_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Lead time in days"
    )
    is_preferred = models.BooleanField(
        default=False,
        help_text="Is this the preferred vendor for this product?"
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['product__name']
        unique_together = ('vendor', 'product')
    
    def __str__(self):
        return f"{self.vendor.name} - {self.product.name}"

class PurchaseOrder(CompanyIsolatedModel):
    """
    Purchase orders to vendors
    """
    ORDER_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('acknowledged', 'Acknowledged'),
        ('confirmed', 'Confirmed'),
        ('partially_received', 'Partially Received'),
        ('received', 'Received'),
        ('cancelled', 'Cancelled'),
        ('closed', 'Closed'),
    ]
    
    # Basic Information
    order_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique purchase order number"
    )
    title = models.CharField(max_length=255, help_text="Purchase order title")
    description = models.TextField(blank=True, help_text="Purchase order description")
    
    # Relationships
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name='purchase_orders',
        help_text="Vendor"
    )
    vendor_contact = models.ForeignKey(
        VendorContact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_orders',
        help_text="Vendor contact"
    )
    
    # Status and Dates
    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default='draft'
    )
    order_date = models.DateField(help_text="Order date")
    expected_delivery_date = models.DateField(
        null=True,
        blank=True,
        help_text="Expected delivery date"
    )
    actual_delivery_date = models.DateField(
        null=True,
        blank=True,
        help_text="Actual delivery date"
    )
    
    # Financial Information
    subtotal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Subtotal before taxes and discounts"
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Tax rate percentage"
    )
    tax_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Tax amount"
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Discount percentage"
    )
    discount_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Discount amount"
    )
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Total amount"
    )
    currency = models.CharField(max_length=3, default='USD', help_text="Currency code")
    
    # Assignment
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_purchase_orders',
        help_text="Purchase order owner"
    )
    
    # Shipping Information
    shipping_address = models.TextField(blank=True, help_text="Shipping address")
    shipping_method = models.CharField(
        max_length=100,
        blank=True,
        help_text="Shipping method"
    )
    tracking_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Tracking number"
    )
    
    # Terms and Conditions
    terms_conditions = models.TextField(
        blank=True,
        help_text="Terms and conditions"
    )
    notes = models.TextField(blank=True, help_text="Internal notes")
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'vendor']),
            models.Index(fields=['company', 'owner']),
            models.Index(fields=['company', 'order_date']),
        ]
    
    def __str__(self):
        return f"{self.order_number} - {self.vendor.name}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number
            from django.utils import timezone
            year = timezone.now().year
            month = timezone.now().month
            count = PurchaseOrder.objects.filter(
                company=self.company,
                created_at__year=year,
                created_at__month=month
            ).count() + 1
            self.order_number = f"PO{year}{month:02d}{count:04d}"
        super().save(*args, **kwargs)

class PurchaseOrderItem(CompanyIsolatedModel):
    """
    Items in a purchase order
    """
    order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='purchase_order_items'
    )
    vendor_product = models.ForeignKey(
        VendorProduct,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_order_items'
    )
    description = models.TextField(blank=True, help_text="Item description")
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
        help_text="Item discount percentage"
    )
    discount_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Item discount amount"
    )
    total_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Total price after discount"
    )
    received_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Quantity received"
    )
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.order.order_number} - {self.product.name}"
    
    def save(self, *args, **kwargs):
        # Calculate total price
        base_price = self.quantity * self.unit_price
        self.discount_amount = (base_price * self.discount_percentage) / 100
        self.total_price = base_price - self.discount_amount
        super().save(*args, **kwargs)
    
    @property
    def is_fully_received(self):
        """Check if item is fully received"""
        return self.received_quantity >= self.quantity
    
    @property
    def remaining_quantity(self):
        """Calculate remaining quantity to be received"""
        return self.quantity - self.received_quantity

class VendorInvoice(CompanyIsolatedModel):
    """
    Invoices received from vendors
    """
    INVOICE_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('received', 'Received'),
        ('verified', 'Verified'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('disputed', 'Disputed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    invoice_number = models.CharField(
        max_length=100,
        help_text="Vendor invoice number"
    )
    title = models.CharField(max_length=255, help_text="Invoice title")
    description = models.TextField(blank=True, help_text="Invoice description")
    
    # Relationships
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name='invoices'
    )
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        help_text="Related purchase order"
    )
    
    # Status and Dates
    status = models.CharField(
        max_length=20,
        choices=INVOICE_STATUS_CHOICES,
        default='draft'
    )
    invoice_date = models.DateField(help_text="Invoice date")
    due_date = models.DateField(help_text="Payment due date")
    received_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When invoice was received"
    )
    paid_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When invoice was paid"
    )
    
    # Financial Information
    subtotal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Subtotal before taxes and discounts"
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Tax rate percentage"
    )
    tax_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Tax amount"
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Discount percentage"
    )
    discount_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Discount amount"
    )
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Total amount"
    )
    currency = models.CharField(max_length=3, default='USD', help_text="Currency code")
    
    # Assignment
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_vendor_invoices',
        help_text="Invoice owner"
    )
    
    # Additional Information
    notes = models.TextField(blank=True, help_text="Internal notes")
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'vendor']),
            models.Index(fields=['company', 'owner']),
            models.Index(fields=['company', 'due_date']),
        ]
    
    def __str__(self):
        return f"{self.invoice_number} - {self.vendor.name}"
    
    @property
    def is_overdue(self):
        """Check if invoice is overdue"""
        if self.status in ['received', 'verified', 'approved'] and self.due_date:
            from django.utils import timezone
            return timezone.now().date() > self.due_date
        return False

class VendorPayment(CompanyIsolatedModel):
    """
    Payments made to vendors
    """
    PAYMENT_METHODS = [
        ('check', 'Check'),
        ('bank_transfer', 'Bank Transfer'),
        ('credit_card', 'Credit Card'),
        ('cash', 'Cash'),
        ('other', 'Other'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    payment_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique payment number"
    )
    amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Payment amount"
    )
    currency = models.CharField(max_length=3, default='USD', help_text="Currency code")
    
    # Relationships
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    invoice = models.ForeignKey(
        VendorInvoice,
        on_delete=models.CASCADE,
        related_name='payments',
        help_text="Related vendor invoice"
    )
    
    # Payment Details
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHODS,
        help_text="Payment method"
    )
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    payment_date = models.DateTimeField(help_text="Payment date and time")
    reference_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="Payment reference number"
    )
    
    # Notes
    notes = models.TextField(blank=True, help_text="Payment notes")
    
    # Metadata
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'vendor']),
            models.Index(fields=['company', 'payment_date']),
        ]
    
    def __str__(self):
        return f"{self.payment_number} - {self.amount} {self.currency}"
    
    def save(self, *args, **kwargs):
        if not self.payment_number:
            # Generate payment number
            from django.utils import timezone
            year = timezone.now().year
            month = timezone.now().month
            count = VendorPayment.objects.filter(
                company=self.company,
                created_at__year=year,
                created_at__month=month
            ).count() + 1
            self.payment_number = f"VP{year}{month:02d}{count:04d}"
        super().save(*args, **kwargs)
