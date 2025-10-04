# sales/models.py
from django.db import models
from django.contrib.auth import get_user_model
from core.models import CompanyIsolatedModel
import uuid

User = get_user_model()

class Quote(CompanyIsolatedModel):
    """
    Sales quotes/proposals
    """
    QUOTE_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('viewed', 'Viewed'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
        ('converted', 'Converted to Order'),
    ]
    
    # Basic Information
    quote_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique quote number"
    )
    title = models.CharField(max_length=255, help_text="Quote title")
    description = models.TextField(blank=True, help_text="Quote description")
    
    # Relationships
    account = models.ForeignKey(
        'crm.Account',
        on_delete=models.CASCADE,
        related_name='quotes',
        help_text="Associated account"
    )
    contact = models.ForeignKey(
        'crm.Contact',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quotes',
        help_text="Primary contact"
    )
    deal = models.ForeignKey(
        'deals.Deal',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quotes',
        help_text="Associated deal"
    )
    
    # Status and Dates
    status = models.CharField(
        max_length=20,
        choices=QUOTE_STATUS_CHOICES,
        default='draft'
    )
    valid_until = models.DateField(
        null=True,
        blank=True,
        help_text="Quote validity date"
    )
    sent_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When quote was sent"
    )
    viewed_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When quote was viewed"
    )
    accepted_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When quote was accepted"
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
        related_name='owned_quotes',
        help_text="Quote owner"
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
            models.Index(fields=['company', 'account']),
            models.Index(fields=['company', 'owner']),
            models.Index(fields=['company', 'valid_until']),
        ]
    
    def __str__(self):
        return f"{self.quote_number} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.quote_number:
            # Generate quote number
            from django.utils import timezone
            year = timezone.now().year
            month = timezone.now().month
            count = Quote.objects.filter(
                company=self.company,
                created_at__year=year,
                created_at__month=month
            ).count() + 1
            self.quote_number = f"Q{year}{month:02d}{count:04d}"
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Check if quote is expired"""
        if self.valid_until and self.status in ['sent', 'viewed']:
            from django.utils import timezone
            return timezone.now().date() > self.valid_until
        return False

class QuoteItem(CompanyIsolatedModel):
    """
    Items in a quote
    """
    quote = models.ForeignKey(
        Quote,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='quote_items'
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
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.quote.quote_number} - {self.product.name}"
    
    def save(self, *args, **kwargs):
        # Calculate total price
        base_price = self.quantity * self.unit_price
        self.discount_amount = (base_price * self.discount_percentage) / 100
        self.total_price = base_price - self.discount_amount
        super().save(*args, **kwargs)

class SalesOrder(CompanyIsolatedModel):
    """
    Sales orders
    """
    ORDER_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
        ('returned', 'Returned'),
    ]
    
    # Basic Information
    order_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique order number"
    )
    title = models.CharField(max_length=255, help_text="Order title")
    description = models.TextField(blank=True, help_text="Order description")
    
    # Relationships
    account = models.ForeignKey(
        'crm.Account',
        on_delete=models.CASCADE,
        related_name='sales_orders',
        help_text="Associated account"
    )
    contact = models.ForeignKey(
        'crm.Contact',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales_orders',
        help_text="Primary contact"
    )
    quote = models.ForeignKey(
        Quote,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales_orders',
        help_text="Source quote"
    )
    deal = models.ForeignKey(
        'deals.Deal',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales_orders',
        help_text="Associated deal"
    )
    
    # Status and Dates
    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default='draft'
    )
    order_date = models.DateField(
        help_text="Order date"
    )
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
        related_name='owned_sales_orders',
        help_text="Order owner"
    )
    
    # Shipping Information
    shipping_address = models.TextField(blank=True, help_text="Shipping address")
    billing_address = models.TextField(blank=True, help_text="Billing address")
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
            models.Index(fields=['company', 'account']),
            models.Index(fields=['company', 'owner']),
            models.Index(fields=['company', 'order_date']),
        ]
    
    def __str__(self):
        return f"{self.order_number} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number
            from django.utils import timezone
            year = timezone.now().year
            month = timezone.now().month
            count = SalesOrder.objects.filter(
                company=self.company,
                created_at__year=year,
                created_at__month=month
            ).count() + 1
            self.order_number = f"SO{year}{month:02d}{count:04d}"
        super().save(*args, **kwargs)

class SalesOrderItem(CompanyIsolatedModel):
    """
    Items in a sales order
    """
    order = models.ForeignKey(
        SalesOrder,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='sales_order_items'
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

class Invoice(CompanyIsolatedModel):
    """
    Sales invoices
    """
    INVOICE_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('viewed', 'Viewed'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        help_text="Unique invoice number"
    )
    title = models.CharField(max_length=255, help_text="Invoice title")
    description = models.TextField(blank=True, help_text="Invoice description")
    
    # Relationships
    account = models.ForeignKey(
        'crm.Account',
        on_delete=models.CASCADE,
        related_name='invoices',
        help_text="Associated account"
    )
    contact = models.ForeignKey(
        'crm.Contact',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        help_text="Primary contact"
    )
    sales_order = models.ForeignKey(
        SalesOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        help_text="Source sales order"
    )
    deal = models.ForeignKey(
        'deals.Deal',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices',
        help_text="Associated deal"
    )
    
    # Status and Dates
    status = models.CharField(
        max_length=20,
        choices=INVOICE_STATUS_CHOICES,
        default='draft'
    )
    invoice_date = models.DateField(
        help_text="Invoice date"
    )
    due_date = models.DateField(
        help_text="Payment due date"
    )
    sent_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When invoice was sent"
    )
    viewed_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When invoice was viewed"
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
    paid_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Amount paid"
    )
    balance_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        help_text="Outstanding balance"
    )
    currency = models.CharField(max_length=3, default='USD', help_text="Currency code")
    
    # Assignment
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_invoices',
        help_text="Invoice owner"
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
            models.Index(fields=['company', 'account']),
            models.Index(fields=['company', 'owner']),
            models.Index(fields=['company', 'due_date']),
        ]
    
    def __str__(self):
        return f"{self.invoice_number} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Generate invoice number
            from django.utils import timezone
            year = timezone.now().year
            month = timezone.now().month
            count = Invoice.objects.filter(
                company=self.company,
                created_at__year=year,
                created_at__month=month
            ).count() + 1
            self.invoice_number = f"INV{year}{month:02d}{count:04d}"
        
        # Calculate balance
        self.balance_amount = self.total_amount - self.paid_amount
        super().save(*args, **kwargs)
    
    @property
    def is_overdue(self):
        """Check if invoice is overdue"""
        if self.status in ['sent', 'viewed'] and self.due_date:
            from django.utils import timezone
            return timezone.now().date() > self.due_date
        return False

class InvoiceItem(CompanyIsolatedModel):
    """
    Items in an invoice
    """
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='invoice_items'
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
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.product.name}"
    
    def save(self, *args, **kwargs):
        # Calculate total price
        base_price = self.quantity * self.unit_price
        self.discount_amount = (base_price * self.discount_percentage) / 100
        self.total_price = base_price - self.discount_amount
        super().save(*args, **kwargs)

class Payment(CompanyIsolatedModel):
    """
    Payment records
    """
    PAYMENT_METHODS = [
        ('cash', 'Cash'),
        ('check', 'Check'),
        ('credit_card', 'Credit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
        ('other', 'Other'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
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
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='payments',
        help_text="Associated invoice"
    )
    account = models.ForeignKey(
        'crm.Account',
        on_delete=models.CASCADE,
        related_name='payments',
        help_text="Associated account"
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
    payment_date = models.DateTimeField(
        help_text="Payment date and time"
    )
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
            models.Index(fields=['company', 'invoice']),
            models.Index(fields=['company', 'account']),
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
            count = Payment.objects.filter(
                company=self.company,
                created_at__year=year,
                created_at__month=month
            ).count() + 1
            self.payment_number = f"PAY{year}{month:02d}{count:04d}"
        super().save(*args, **kwargs)
