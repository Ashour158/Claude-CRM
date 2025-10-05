# sales/models.py
# Sales documents and order management models

from django.db import models
from django.core.validators import MinValueValidator
from core.models import CompanyIsolatedModel, User
from crm.models import Account, Contact
from products.models import Product
import uuid

class Quote(CompanyIsolatedModel):
    """Sales quotes/proposals"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('viewed', 'Viewed'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    # Basic Information
    quote_number = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Relationships
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='quotes'
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quotes'
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_quotes'
    )
    
    # Financial Information
    subtotal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Tax rate percentage"
    )
    tax_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Discount percentage"
    )
    discount_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    currency = models.CharField(max_length=3, default='USD')
    
    # Dates
    quote_date = models.DateField()
    valid_until = models.DateField(
        null=True,
        blank=True,
        help_text="Quote validity period"
    )
    sent_date = models.DateTimeField(null=True, blank=True)
    viewed_date = models.DateTimeField(null=True, blank=True)
    accepted_date = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    
    # Terms and Conditions
    terms_conditions = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Conversion
    converted_to_order = models.ForeignKey(
        'SalesOrder',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='converted_from_quote'
    )
    
    class Meta:
        db_table = 'quote'
        ordering = ['-quote_date']
        indexes = [
            models.Index(fields=['company', 'quote_number']),
            models.Index(fields=['company', 'account']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'owner']),
        ]
    
    def __str__(self):
        return f"{self.quote_number} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.quote_number:
            # Generate quote number
            last_quote = Quote.objects.filter(
                company=self.company
            ).order_by('-created_at').first()
            
            if last_quote and last_quote.quote_number:
                try:
                    last_num = int(last_quote.quote_number.split('-')[-1])
                    self.quote_number = f"QUO-{last_num + 1:06d}"
                except:
                    self.quote_number = f"QUO-000001"
            else:
                self.quote_number = f"QUO-000001"
        
        # Calculate totals
        self.calculate_totals()
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calculate quote totals"""
        # Calculate subtotal from line items
        subtotal = sum(item.total_price for item in self.items.all())
        self.subtotal = subtotal
        
        # Calculate discount
        if self.discount_percentage > 0:
            self.discount_amount = (subtotal * self.discount_percentage) / 100
        else:
            self.discount_amount = 0
        
        # Calculate tax
        taxable_amount = subtotal - self.discount_amount
        self.tax_amount = (taxable_amount * self.tax_rate) / 100
        
        # Calculate total
        self.total_amount = taxable_amount + self.tax_amount

class QuoteItem(CompanyIsolatedModel):
    """Quote line items"""
    
    quote = models.ForeignKey(
        Quote,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='quote_items'
    )
    description = models.TextField(blank=True)
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
        validators=[MinValueValidator(0.01)]
    )
    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    total_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        help_text="Total price after discount"
    )
    
    class Meta:
        db_table = 'quote_item'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.quote.quote_number} - {self.product.name}"
    
    def save(self, *args, **kwargs):
        # Calculate total price
        base_price = self.quantity * self.unit_price
        discount_amount = (base_price * self.discount_percentage) / 100
        self.total_price = base_price - discount_amount
        super().save(*args, **kwargs)

class SalesOrder(CompanyIsolatedModel):
    """Sales orders"""
    
    STATUS_CHOICES = [
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
    order_number = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Relationships
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='sales_orders'
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sales_orders'
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_sales_orders'
    )
    
    # Financial Information
    subtotal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    tax_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    discount_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    shipping_cost = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    currency = models.CharField(max_length=3, default='USD')
    
    # Dates
    order_date = models.DateField()
    required_date = models.DateField(
        null=True,
        blank=True,
        help_text="Required delivery date"
    )
    shipped_date = models.DateTimeField(null=True, blank=True)
    delivered_date = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    
    # Shipping Information
    shipping_address = models.JSONField(
        default=dict,
        help_text="Shipping address details"
    )
    billing_address = models.JSONField(
        default=dict,
        help_text="Billing address details"
    )
    
    # Payment Information
    payment_terms = models.CharField(
        max_length=100,
        default='Net 30',
        help_text="Payment terms"
    )
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('partial', 'Partial'),
            ('paid', 'Paid'),
            ('overdue', 'Overdue'),
        ],
        default='pending'
    )
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'sales_order'
        ordering = ['-order_date']
        indexes = [
            models.Index(fields=['company', 'order_number']),
            models.Index(fields=['company', 'account']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'owner']),
        ]
    
    def __str__(self):
        return f"{self.order_number} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate order number
            last_order = SalesOrder.objects.filter(
                company=self.company
            ).order_by('-created_at').first()
            
            if last_order and last_order.order_number:
                try:
                    last_num = int(last_order.order_number.split('-')[-1])
                    self.order_number = f"ORD-{last_num + 1:06d}"
                except:
                    self.order_number = f"ORD-000001"
            else:
                self.order_number = f"ORD-000001"
        
        # Calculate totals
        self.calculate_totals()
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calculate order totals"""
        # Calculate subtotal from line items
        subtotal = sum(item.total_price for item in self.items.all())
        self.subtotal = subtotal
        
        # Calculate discount
        if self.discount_percentage > 0:
            self.discount_amount = (subtotal * self.discount_percentage) / 100
        else:
            self.discount_amount = 0
        
        # Calculate tax
        taxable_amount = subtotal - self.discount_amount
        self.tax_amount = (taxable_amount * self.tax_rate) / 100
        
        # Calculate total
        self.total_amount = taxable_amount + self.tax_amount + self.shipping_cost

class SalesOrderItem(CompanyIsolatedModel):
    """Sales order line items"""
    
    order = models.ForeignKey(
        SalesOrder,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='sales_order_items'
    )
    description = models.TextField(blank=True)
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
        validators=[MinValueValidator(0.01)]
    )
    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    total_price = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )
    
    class Meta:
        db_table = 'sales_order_item'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.order.order_number} - {self.product.name}"
    
    def save(self, *args, **kwargs):
        # Calculate total price
        base_price = self.quantity * self.unit_price
        discount_amount = (base_price * self.discount_percentage) / 100
        self.total_price = base_price - discount_amount
        super().save(*args, **kwargs)

class Invoice(CompanyIsolatedModel):
    """Sales invoices"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('viewed', 'Viewed'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    invoice_number = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Relationships
    account = models.ForeignKey(
        Account,
        on_delete=models.CASCADE,
        related_name='invoices'
    )
    contact = models.ForeignKey(
        Contact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices'
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_invoices'
    )
    sales_order = models.ForeignKey(
        SalesOrder,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices'
    )
    
    # Financial Information
    subtotal = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    tax_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    tax_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    discount_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    total_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    paid_amount = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    balance_due = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0
    )
    currency = models.CharField(max_length=3, default='USD')
    
    # Dates
    invoice_date = models.DateField()
    due_date = models.DateField()
    sent_date = models.DateTimeField(null=True, blank=True)
    viewed_date = models.DateTimeField(null=True, blank=True)
    paid_date = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    
    # Payment Information
    payment_terms = models.CharField(
        max_length=100,
        default='Net 30'
    )
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'invoice'
        ordering = ['-invoice_date']
        indexes = [
            models.Index(fields=['company', 'invoice_number']),
            models.Index(fields=['company', 'account']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'due_date']),
        ]
    
    def __str__(self):
        return f"{self.invoice_number} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Generate invoice number
            last_invoice = Invoice.objects.filter(
                company=self.company
            ).order_by('-created_at').first()
            
            if last_invoice and last_invoice.invoice_number:
                try:
                    last_num = int(last_invoice.invoice_number.split('-')[-1])
                    self.invoice_number = f"INV-{last_num + 1:06d}"
                except:
                    self.invoice_number = f"INV-000001"
            else:
                self.invoice_number = f"INV-000001"
        
        # Calculate totals
        self.calculate_totals()
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calculate invoice totals"""
        # Calculate subtotal from line items
        subtotal = sum(item.total_price for item in self.items.all())
        self.subtotal = subtotal
        
        # Calculate discount
        if self.discount_percentage > 0:
            self.discount_amount = (subtotal * self.discount_percentage) / 100
        else:
            self.discount_amount = 0
        
        # Calculate tax
        taxable_amount = subtotal - self.discount_amount
        self.tax_amount = (taxable_amount * self.tax_rate) / 100
        
        # Calculate total
        self.total_amount = taxable_amount + self.tax_amount
        
        # Calculate balance due
        self.balance_due = self.total_amount - self.paid_amount

class InvoiceItem(CompanyIsolatedModel):
    """Invoice line items"""
    
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='invoice_items'
    )
    description = models.TextField(blank=True)
    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=1,
        validators=[MinValueValidator(0.01)]
    )
    unit_price = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    discount_percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )
    total_price = models.DecimalField(
        max_digits=15,
        decimal_places=2
    )
    
    class Meta:
        db_table = 'invoice_item'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.invoice.invoice_number} - {self.product.name}"
    
    def save(self, *args, **kwargs):
        # Calculate total price
        base_price = self.quantity * self.unit_price
        discount_amount = (base_price * self.discount_percentage) / 100
        self.total_price = base_price - discount_amount
        super().save(*args, **kwargs)