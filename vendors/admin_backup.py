# vendors/admin.py
from django.contrib import admin
from vendors.models import (
    Vendor, VendorContact, PurchaseOrder,
    PurchaseOrderItem, VendorPerformance
)

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'vendor_code', 'status',
        'email', 'phone', 'created_at'
    ]
    list_filter = [
        'status', 'created_at', 'company'
    ]
    search_fields = ['name', 'vendor_code', 'email', 'phone']
    ordering = ['-created_at']

@admin.register(VendorContact)
class VendorContactAdmin(admin.ModelAdmin):
    list_display = [
        'vendor', 'name', 'title', 'email', 'phone', 'is_primary'
    ]
    list_filter = ['is_primary', 'vendor__company']
    search_fields = ['name', 'email', 'phone', 'vendor__name']
    ordering = ['vendor__name', 'name']
    raw_id_fields = ['vendor']

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = [
        'po_number', 'vendor', 'status', 'total_amount',
        'order_date', 'expected_delivery_date', 'created_at'
    ]
    list_filter = [
        'status', 'order_date', 'expected_delivery_date', 'company'
    ]
    search_fields = [
        'po_number', 'vendor__name', 'notes'
    ]
    ordering = ['-created_at']
    raw_id_fields = ['vendor']

@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = [
        'purchase_order', 'product', 'quantity', 'unit_price', 'total_price'
    ]
    list_filter = ['purchase_order__company', 'created_at']
    search_fields = ['purchase_order__po_number', 'product__name']
    ordering = ['purchase_order__po_number']
    raw_id_fields = ['purchase_order', 'product']

@admin.register(VendorPerformance)
class VendorPerformanceAdmin(admin.ModelAdmin):
    list_display = [
        'vendor', 'evaluation_date', 'overall_score', 'quality_score',
        'delivery_score', 'pricing_score'
    ]
    list_filter = ['evaluation_date', 'vendor__company']
    search_fields = ['vendor__name', 'notes']
    ordering = ['-evaluation_date']
    raw_id_fields = ['vendor', 'evaluated_by']
