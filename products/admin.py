# products/admin.py
from django.contrib import admin
from products.models import ProductCategory, Product, PriceList

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'is_active']
    list_filter = ['is_active', 'parent', 'company']
    search_fields = ['name', 'description']
    ordering = ['name']
    list_editable = ['is_active']
    raw_id_fields = ['parent']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'category', 'is_active']
    list_filter = ['category', 'is_active', 'company']
    search_fields = ['name', 'sku', 'description']
    ordering = ['name']
    raw_id_fields = ['category']

@admin.register(PriceList)
class PriceListAdmin(admin.ModelAdmin):
    list_display = ['name', 'currency', 'is_active']
    list_filter = ['is_active', 'company']
    search_fields = ['name', 'description']
    ordering = ['name']
