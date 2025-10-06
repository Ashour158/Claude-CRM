# sales/admin.py
from django.contrib import admin
from sales.models import Quote, QuoteItem, SalesOrder, SalesOrderItem, Invoice, InvoiceItem

@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ['quote_number', 'account', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'company']
    search_fields = ['quote_number', 'account__name']
    ordering = ['-created_at']
    raw_id_fields = ['account', 'contact', 'owner']

@admin.register(QuoteItem)
class QuoteItemAdmin(admin.ModelAdmin):
    list_display = ['quote', 'product', 'quantity', 'unit_price', 'total_price']
    raw_id_fields = ['quote', 'product']

@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'account', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'company']
    search_fields = ['order_number', 'account__name']
    ordering = ['-created_at']
    raw_id_fields = ['account', 'contact', 'owner', 'quote']

@admin.register(SalesOrderItem)
class SalesOrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'unit_price', 'total_price']
    raw_id_fields = ['order', 'product']

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'account', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'company']
    search_fields = ['invoice_number', 'account__name']
    ordering = ['-created_at']
    raw_id_fields = ['account', 'contact', 'owner', 'order']

@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'product', 'quantity', 'unit_price', 'total_price']
    raw_id_fields = ['invoice', 'product']
