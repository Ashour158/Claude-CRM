# products/admin.py
from django.contrib import admin
from products.models import ProductCategory, Product, PriceList

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    list_filter = ['is_active', 'company']
    search_fields = ['name', 'description']
    ordering = ['name']
    list_editable = ['is_active']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'sku', 'category', 'unit_price',
        'is_active'
    ]
    list_filter = [
        'category', 'is_active', 'company'
    ]
    search_fields = ['name', 'sku', 'description']
    ordering = ['-created_at']
    list_editable = ['is_active']
    raw_id_fields = ['category']

@admin.register(PriceList)
class PriceListAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'is_default']
    list_filter = ['is_active', 'is_default', 'company']
    search_fields = ['name', 'description']
    ordering = ['name']
    list_editable = ['is_active', 'is_default']
