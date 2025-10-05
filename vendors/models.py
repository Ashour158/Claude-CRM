# vendors/models.py
# Vendor and supplier management models

from django.db import models
from django.core.validators import EmailValidator, MinValueValidator
from core.models import CompanyIsolatedModel, User
import uuid

class Vendor(CompanyIsolatedModel):
    """Vendor/Supplier model"""
    
    VENDOR_TYPES = [
        ('supplier', 'Supplier'),
        ('service_provider', 'Service Provider'),
        ('consultant', 'Consultant'),
        ('partner', 'Partner'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('blacklisted', 'Blacklisted'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=255)
    legal_name = models.CharField(max_length=255, blank=True)
    vendor_code = models.CharField(
        max_length=100,
        unique=True,
        help_text="Unique vendor identifier"
    )
    website = models.URLField(blank=True)
    
    # Classification
    vendor_type = models.CharField(
        max_length=50,
        choices=VENDOR_TYPES,
        default='supplier'
    )
    industry = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=100, blank=True)
    
    # Contact Information
    primary_contact_name = models.CharField(max_length=255, blank=True)
    primary_contact_email = models.EmailField(blank=True, validators=[EmailValidator()])
    primary_contact_phone = models.CharField(max_length=50, blank=True)
    primary_contact_title = models.CharField(max_length=100, blank=True)
    
    # Business Information
    tax_id = models.CharField(max_length=100, blank=True)
    registration_number = models.CharField(max_length=100, blank=True)
    annual_revenue = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    employee_count = models.IntegerField(null=True, blank=True)
    established_year = models.IntegerField(null=True, blank=True)
    
    # Address Information
    billing_address_line1 = models.CharField(max_length=255, blank=True)
    billing_address_line2 = models.CharField(max_length=255, blank=True)
    billing_city = models.CharField(max_length=100, blank=True)
    billing_state = models.CharField(max_length=100, blank=True)
    billing_postal_code = models.CharField(max_length=20, blank=True)
    billing_country = models.CharField(max_length=100, blank=True)
    
    shipping_address_line1 = models.CharField(max_length=255, blank=True)
    shipping_address_line2 = models.CharField(max_length=255, blank=True)
    shipping_city = models.CharField(max_length=100, blank=True)
    shipping_state = models.CharField(max_length=100, blank=True)
    shipping_postal_code = models.CharField(max_length=20, blank=True)
    shipping_country = models.CharField(max_length=100, blank=True)
    
    # Financial Information
    payment_terms = models.CharField(
        max_length=100,
        default='Net 30',
        help_text="Payment terms with this vendor"
    )
    credit_limit = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        null=True,
        blank=True
    )
    currency = models.CharField(max_length=3, default='USD')
    
    # Relationships
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='owned_vendors',
        help_text="Vendor manager/owner"
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    is_approved = models.BooleanField(default=False)
    is_preferred = models.BooleanField(default=False)
    
    # Rating and Performance
    rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Vendor rating (1-5)"
    )
    performance_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Performance score (0-100)"
    )
    
    # Notes
    description = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # Custom Fields
    custom_fields = models.JSONField(null=True, blank=True)
    
    class Meta:
        db_table = 'vendor'
        ordering = ['name']
        indexes = [
            models.Index(fields=['company', 'name']),
            models.Index(fields=['company', 'vendor_type']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'owner']),
        ]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # Auto-generate vendor code if not provided
        if not self.vendor_code:
            last_vendor = Vendor.objects.filter(
                company=self.company
            ).order_by('-created_at').first()
            
            if last_vendor and last_vendor.vendor_code:
                try:
                    last_num = int(last_vendor.vendor_code.split('-')[-1])
                    self.vendor_code = f"VEN-{last_num + 1:06d}"
                except:
                    self.vendor_code = f"VEN-000001"
            else:
                self.vendor_code = f"VEN-000001"
        
        super().save(*args, **kwargs)
    
    def get_full_address(self, address_type='billing'):
        """Get formatted address"""
        if address_type == 'billing':
            parts = [
                self.billing_address_line1,
                self.billing_address_line2,
                self.billing_city,
                self.billing_state,
                self.billing_postal_code,
                self.billing_country
            ]
        else:
            parts = [
                self.shipping_address_line1,
                self.shipping_address_line2,
                self.shipping_city,
                self.shipping_state,
                self.shipping_postal_code,
                self.shipping_country
            ]
        
        return ', '.join([p for p in parts if p])

class VendorContact(CompanyIsolatedModel):
    """Vendor contacts"""
    
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name='contacts'
    )
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True, validators=[EmailValidator()])
    phone = models.CharField(max_length=50, blank=True)
    mobile = models.CharField(max_length=50, blank=True)
    fax = models.CharField(max_length=50, blank=True)
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'vendor_contact'
        ordering = ['name']
    
    def __str__(self):
        return f"{self.vendor.name} - {self.name}"

class PurchaseOrder(CompanyIsolatedModel):
    """Purchase orders"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('acknowledged', 'Acknowledged'),
        ('partially_received', 'Partially Received'),
        ('received', 'Received'),
        ('invoiced', 'Invoiced'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    # Basic Information
    po_number = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Relationships
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name='purchase_orders'
    )
    vendor_contact = models.ForeignKey(
        VendorContact,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='purchase_orders'
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_purchase_orders'
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
    sent_date = models.DateTimeField(null=True, blank=True)
    acknowledged_date = models.DateTimeField(null=True, blank=True)
    received_date = models.DateTimeField(null=True, blank=True)
    
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
    
    # Terms and Conditions
    terms_conditions = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'purchase_order'
        ordering = ['-order_date']
        indexes = [
            models.Index(fields=['company', 'po_number']),
            models.Index(fields=['company', 'vendor']),
            models.Index(fields=['company', 'status']),
            models.Index(fields=['company', 'owner']),
        ]
    
    def __str__(self):
        return f"{self.po_number} - {self.title}"
    
    def save(self, *args, **kwargs):
        if not self.po_number:
            # Generate PO number
            last_po = PurchaseOrder.objects.filter(
                company=self.company
            ).order_by('-created_at').first()
            
            if last_po and last_po.po_number:
                try:
                    last_num = int(last_po.po_number.split('-')[-1])
                    self.po_number = f"PO-{last_num + 1:06d}"
                except:
                    self.po_number = f"PO-000001"
            else:
                self.po_number = f"PO-000001"
        
        # Calculate totals
        self.calculate_totals()
        super().save(*args, **kwargs)
    
    def calculate_totals(self):
        """Calculate PO totals"""
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

class PurchaseOrderItem(CompanyIsolatedModel):
    """Purchase order line items"""
    
    purchase_order = models.ForeignKey(
        PurchaseOrder,
        on_delete=models.CASCADE,
        related_name='items'
    )
    product_name = models.CharField(max_length=255, help_text="Product/service name")
    description = models.TextField(blank=True)
    sku = models.CharField(max_length=100, blank=True, help_text="Vendor SKU")
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
    
    # Receiving
    received_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Quantity received"
    )
    pending_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text="Quantity pending"
    )
    
    class Meta:
        db_table = 'purchase_order_item'
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.purchase_order.po_number} - {self.product_name}"
    
    def save(self, *args, **kwargs):
        # Calculate total price
        base_price = self.quantity * self.unit_price
        discount_amount = (base_price * self.discount_percentage) / 100
        self.total_price = base_price - discount_amount
        
        # Calculate pending quantity
        self.pending_quantity = self.quantity - self.received_quantity
        
        super().save(*args, **kwargs)

class VendorPerformance(CompanyIsolatedModel):
    """Vendor performance tracking"""
    
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name='performance_records'
    )
    period_start = models.DateField()
    period_end = models.DateField()
    
    # Performance Metrics
    delivery_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Delivery performance score (0-100)"
    )
    quality_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Quality performance score (0-100)"
    )
    communication_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Communication score (0-100)"
    )
    overall_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Overall performance score (0-100)"
    )
    
    # Metrics
    on_time_delivery_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="On-time delivery rate percentage"
    )
    quality_issues_count = models.IntegerField(default=0)
    communication_issues_count = models.IntegerField(default=0)
    
    # Notes
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'vendor_performance'
        ordering = ['-period_end']
        unique_together = ('vendor', 'period_start', 'period_end')
    
    def __str__(self):
        return f"{self.vendor.name} - {self.period_start} to {self.period_end}"
    
    def save(self, *args, **kwargs):
        # Calculate overall score
        self.overall_score = (
            self.delivery_score + 
            self.quality_score + 
            self.communication_score
        ) / 3
        super().save(*args, **kwargs)