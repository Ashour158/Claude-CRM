# vendors/admin.py
from django.contrib import admin
from vendors.models import Vendor, VendorContact, PurchaseOrder, PurchaseOrderItem, VendorPerformance

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['name', 'vendor_code', 'status', 'is_active']
    list_filter = ['status', 'is_active', 'company']
    search_fields = ['name', 'vendor_code']
    ordering = ['name']

@admin.register(VendorContact)
class VendorContactAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'first_name', 'last_name', 'email', 'is_primary']
    list_filter = ['is_primary', 'vendor__company']
    search_fields = ['first_name', 'last_name', 'email', 'vendor__name']
    raw_id_fields = ['vendor']

@admin.register(PurchaseOrder)
class PurchaseOrderAdmin(admin.ModelAdmin):
    list_display = ['po_number', 'vendor', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'company']
    search_fields = ['po_number', 'vendor__name']
    ordering = ['-created_at']
    raw_id_fields = ['vendor']

@admin.register(PurchaseOrderItem)
class PurchaseOrderItemAdmin(admin.ModelAdmin):
    list_display = ['purchase_order', 'product', 'quantity', 'unit_price', 'total_price']
    raw_id_fields = ['purchase_order', 'product']

@admin.register(VendorPerformance)
class VendorPerformanceAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'quality_score', 'delivery_score', 'created_at']
    list_filter = ['vendor__company']
    raw_id_fields = ['vendor']
