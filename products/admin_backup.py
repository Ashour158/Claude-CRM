# products/admin.py
from django.contrib import admin
from products.models import ProductCategory, Product, PriceList

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'is_active', 'product_count']
    list_filter = ['is_active', 'parent', 'company']
    search_fields = ['name', 'description']
    ordering = ['name']
    list_editable = ['is_active']
    raw_id_fields = ['parent']
    
    def product_count(self, obj):
        return obj.products.filter(is_active=True).count()
    product_count.short_description = 'Products'

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'sku', 'category', 'unit_price',
        'cost_price', 'is_active'
    ]
    list_filter = [
        'category', 'is_active', 'is_digital', 'company'
    ]
    search_fields = ['name', 'sku', 'description']
    ordering = ['name']
    list_editable = ['is_active']
    raw_id_fields = ['category']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'sku', 'category')
        }),
        ('Pricing', {
            'fields': ('unit_price', 'cost_price')
        }),
        ('Product Details', {
            'fields': ('unit_of_measure', 'weight', 'dimensions')
        }),
        ('Status', {
            'fields': ('is_active', 'is_digital')
        }),
        ('Custom Fields', {
            'fields': ('custom_fields',),
            'classes': ('collapse',)
        })
    )

@admin.register(PriceList)
class PriceListAdmin(admin.ModelAdmin):
    list_display = ['name', 'currency', 'is_active', 'valid_from', 'valid_to']
    list_filter = ['is_active', 'currency', 'company']
    search_fields = ['name', 'description']
    ordering = ['name']
    list_editable = ['is_active']
    date_hierarchy = 'valid_from'
