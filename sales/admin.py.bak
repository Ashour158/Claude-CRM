# sales/admin.py
from django.contrib import admin
from sales.models import (
    Quote, QuoteItem, SalesOrder, SalesOrderItem,
    Invoice, InvoiceItem, Payment
)

@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = [
        'quote_number', 'title', 'account', 'status', 'total_amount',
        'currency', 'valid_until', 'owner', 'created_at'
    ]
    list_filter = [
        'status', 'currency', 'valid_until', 'created_at', 'company'
    ]
    search_fields = [
        'quote_number', 'title', 'description', 'account__name'
    ]
    ordering = ['-created_at']
    list_editable = ['status']
    raw_id_fields = ['account', 'contact', 'deal', 'owner']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('quote_number', 'title', 'description')
        }),
        ('Relationships', {
            'fields': ('account', 'contact', 'deal')
        }),
        ('Status and Dates', {
            'fields': ('status', 'valid_until', 'sent_date', 'viewed_date', 'accepted_date')
        }),
        ('Financial Information', {
            'fields': ('subtotal', 'tax_rate', 'tax_amount', 'discount_percentage', 'discount_amount', 'total_amount', 'currency')
        }),
        ('Assignment', {
            'fields': ('owner',)
        }),
        ('Terms and Notes', {
            'fields': ('terms_conditions', 'notes')
        }),
        ('Metadata', {
            'fields': ('metadata', 'is_active'),
            'classes': ('collapse',)
        })
    )

@admin.register(QuoteItem)
class QuoteItemAdmin(admin.ModelAdmin):
    list_display = [
        'quote', 'product', 'quantity', 'unit_price', 'total_price'
    ]
    list_filter = ['quote__company', 'created_at']
    search_fields = ['quote__quote_number', 'product__name', 'product__sku']
    ordering = ['quote__quote_number', 'product__name']
    raw_id_fields = ['quote', 'product']

@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'title', 'account', 'status', 'total_amount',
        'currency', 'order_date', 'expected_delivery_date', 'owner'
    ]
    list_filter = [
        'status', 'currency', 'order_date', 'expected_delivery_date', 'company'
    ]
    search_fields = [
        'order_number', 'title', 'description', 'account__name', 'tracking_number'
    ]
    ordering = ['-created_at']
    list_editable = ['status']
    raw_id_fields = ['account', 'contact', 'quote', 'deal', 'owner']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('order_number', 'title', 'description')
        }),
        ('Relationships', {
            'fields': ('account', 'contact', 'quote', 'deal')
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
            'fields': ('shipping_address', 'billing_address', 'shipping_method', 'tracking_number')
        }),
        ('Terms and Notes', {
            'fields': ('terms_conditions', 'notes')
        }),
        ('Metadata', {
            'fields': ('metadata', 'is_active'),
            'classes': ('collapse',)
        })
    )

@admin.register(SalesOrderItem)
class SalesOrderItemAdmin(admin.ModelAdmin):
    list_display = [
        'order', 'product', 'quantity', 'unit_price', 'total_price'
    ]
    list_filter = ['order__company', 'created_at']
    search_fields = ['order__order_number', 'product__name', 'product__sku']
    ordering = ['order__order_number', 'product__name']
    raw_id_fields = ['order', 'product']

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = [
        'invoice_number', 'title', 'account', 'status', 'total_amount',
        'currency', 'paid_amount', 'balance_amount', 'invoice_date', 'due_date', 'owner'
    ]
    list_filter = [
        'status', 'currency', 'invoice_date', 'due_date', 'company'
    ]
    search_fields = [
        'invoice_number', 'title', 'description', 'account__name'
    ]
    ordering = ['-created_at']
    list_editable = ['status']
    raw_id_fields = ['account', 'contact', 'sales_order', 'deal', 'owner']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('invoice_number', 'title', 'description')
        }),
        ('Relationships', {
            'fields': ('account', 'contact', 'sales_order', 'deal')
        }),
        ('Status and Dates', {
            'fields': ('status', 'invoice_date', 'due_date', 'sent_date', 'viewed_date', 'paid_date')
        }),
        ('Financial Information', {
            'fields': ('subtotal', 'tax_rate', 'tax_amount', 'discount_percentage', 'discount_amount', 'total_amount', 'currency', 'paid_amount', 'balance_amount')
        }),
        ('Assignment', {
            'fields': ('owner',)
        }),
        ('Terms and Notes', {
            'fields': ('terms_conditions', 'notes')
        }),
        ('Metadata', {
            'fields': ('metadata', 'is_active'),
            'classes': ('collapse',)
        })
    )

@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = [
        'invoice', 'product', 'quantity', 'unit_price', 'total_price'
    ]
    list_filter = ['invoice__company', 'created_at']
    search_fields = ['invoice__invoice_number', 'product__name', 'product__sku']
    ordering = ['invoice__invoice_number', 'product__name']
    raw_id_fields = ['invoice', 'product']

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'payment_number', 'invoice', 'account', 'amount', 'currency',
        'payment_method', 'status', 'payment_date', 'reference_number'
    ]
    list_filter = [
        'status', 'payment_method', 'currency', 'payment_date', 'company'
    ]
    search_fields = [
        'payment_number', 'invoice__invoice_number', 'account__name', 'reference_number'
    ]
    ordering = ['-payment_date']
    list_editable = ['status']
    raw_id_fields = ['invoice', 'account', 'created_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('payment_number', 'amount', 'currency')
        }),
        ('Relationships', {
            'fields': ('invoice', 'account')
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
