# vendors/admin.py
from django.contrib import admin
from vendors.models import (
    Vendor, VendorContact, PurchaseOrder,
    PurchaseOrderItem, VendorPerformance
)

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'vendor_code', 'vendor_type', 'status',
        'primary_contact_name', 'primary_contact_email', 'city', 'country',
        'rating', 'owner', 'created_at'
    ]
    list_filter = [
        'vendor_type', 'status', 'country', 'currency', 'is_active', 'company'
    ]
    search_fields = [
        'name', 'vendor_code', 'primary_contact_name', 'primary_contact_email',
        'business_registration_number', 'tax_id'
    ]
    ordering = ['name']
    list_editable = ['status']
    raw_id_fields = ['owner']
    filter_horizontal = ['tags']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'vendor_code', 'vendor_type', 'status')
        }),
        ('Contact Information', {
            'fields': ('primary_contact_name', 'primary_contact_email', 'primary_contact_phone')
        }),
        ('Business Information', {
            'fields': ('business_registration_number', 'tax_id', 'website')
        }),
        ('Address Information', {
            'fields': ('billing_address', 'shipping_address', 'city', 'state', 'postal_code', 'country')
        }),
        ('Financial Information', {
            'fields': ('currency', 'payment_terms', 'credit_limit')
        }),
        ('Performance Metrics', {
            'fields': ('rating', 'on_time_delivery_rate', 'quality_rating')
        }),
        ('Assignment', {
            'fields': ('owner',)
        }),
        ('Additional Information', {
            'fields': ('description', 'notes')
        }),
        ('Metadata', {
            'fields': ('tags', 'metadata', 'is_active'),
            'classes': ('collapse',)
        })
    )

@admin.register(VendorContact)
class VendorContactAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'vendor', 'contact_type', 'title', 'email',
        'phone', 'is_primary', 'created_at'
    ]
    list_filter = [
        'contact_type', 'is_primary', 'vendor__company', 'created_at'
    ]
    search_fields = [
        'name', 'title', 'email', 'phone', 'department', 'vendor__name'
    ]
    ordering = ['vendor__name', 'name']
    list_editable = ['is_primary']
    raw_id_fields = ['vendor']

@admin.register(VendorProduct)
class VendorProductAdmin(admin.ModelAdmin):
    list_display = [
        'vendor', 'product', 'vendor_sku', 'vendor_price',
        'currency', 'minimum_order_quantity', 'lead_time_days',
        'is_preferred', 'is_active'
    ]
    list_filter = [
        'is_preferred', 'is_active', 'currency', 'vendor__company'
    ]
    search_fields = [
        'vendor__name', 'product__name', 'product__sku', 'vendor_sku'
    ]
    ordering = ['vendor__name', 'product__name']
    list_editable = ['is_preferred', 'is_active']
    raw_id_fields = ['vendor', 'product']

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'title', 'vendor', 'status', 'total_amount',
        'currency', 'order_date', 'expected_delivery_date', 'owner'
    ]
    list_filter = [
        'status', 'currency', 'order_date', 'expected_delivery_date', 'company'
    ]
    search_fields = [
        'order_number', 'title', 'description', 'vendor__name', 'tracking_number'
    ]
    ordering = ['-created_at']
    list_editable = ['status']
    raw_id_fields = ['vendor', 'vendor_contact', 'owner']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('order_number', 'title', 'description')
        }),
        ('Relationships', {
            'fields': ('vendor', 'vendor_contact')
        }),
        ('Status and Dates', {
            'fields': ('status', 'order_date', 'expected_delivery_date', 'actual_delivery_date')
        }),
        ('Financial Information', {
            'fields': ('subtotal', 'tax_rate', 'tax_amount', 'discount_percentage', 'discount_amount', 'total_amount', 'currency')
        }),
        ('Assignment', {
            'fields': ('owner',)
        }),
        ('Shipping Information', {
            'fields': ('shipping_address', 'shipping_method', 'tracking_number')
        }),
        ('Terms and Notes', {
            'fields': ('terms_conditions', 'notes')
        }),
        ('Metadata', {
            'fields': ('metadata', 'is_active'),
            'classes': ('collapse',)
        })
    )

@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = [
        'order', 'product', 'quantity', 'unit_price', 'total_price',
        'received_quantity', 'is_fully_received'
    ]
    list_filter = ['order__company', 'created_at']
    search_fields = [
        'order__order_number', 'product__name', 'product__sku'
    ]
    ordering = ['order__order_number', 'product__name']
    raw_id_fields = ['order', 'product', 'vendor_product']
    
    def is_fully_received(self, obj):
        return obj.is_fully_received
    is_fully_received.boolean = True
    is_fully_received.short_description = 'Fully Received'

@admin.register(VendorInvoice)
class VendorInvoiceAdmin(admin.ModelAdmin):
    list_display = [
        'invoice_number', 'title', 'vendor', 'status', 'total_amount',
        'currency', 'invoice_date', 'due_date', 'is_overdue', 'owner'
    ]
    list_filter = [
        'status', 'currency', 'invoice_date', 'due_date', 'company'
    ]
    search_fields = [
        'invoice_number', 'title', 'description', 'vendor__name'
    ]
    ordering = ['-created_at']
    list_editable = ['status']
    raw_id_fields = ['vendor', 'purchase_order', 'owner']
    
    def is_overdue(self, obj):
        return obj.is_overdue
    is_overdue.boolean = True
    is_overdue.short_description = 'Overdue'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('invoice_number', 'title', 'description')
        }),
        ('Relationships', {
            'fields': ('vendor', 'purchase_order')
        }),
        ('Status and Dates', {
            'fields': ('status', 'invoice_date', 'due_date', 'received_date', 'paid_date')
        }),
        ('Financial Information', {
            'fields': ('subtotal', 'tax_rate', 'tax_amount', 'discount_percentage', 'discount_amount', 'total_amount', 'currency')
        }),
        ('Assignment', {
            'fields': ('owner',)
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('metadata', 'is_active'),
            'classes': ('collapse',)
        })
    )

@admin.register(VendorPayment)
class VendorPaymentAdmin(admin.ModelAdmin):
    list_display = [
        'payment_number', 'vendor', 'invoice', 'amount', 'currency',
        'payment_method', 'status', 'payment_date', 'reference_number'
    ]
    list_filter = [
        'status', 'payment_method', 'currency', 'payment_date', 'company'
    ]
    search_fields = [
        'payment_number', 'vendor__name', 'invoice__invoice_number', 'reference_number'
    ]
    ordering = ['-payment_date']
    list_editable = ['status']
    raw_id_fields = ['vendor', 'invoice', 'created_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('payment_number', 'amount', 'currency')
        }),
        ('Relationships', {
            'fields': ('vendor', 'invoice')
        }),
        ('Payment Details', {
            'fields': ('payment_method', 'status', 'payment_date', 'reference_number')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Metadata', {
            'fields': ('metadata', 'is_active'),
            'classes': ('collapse',)
        })
    )
