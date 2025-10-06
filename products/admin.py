# products/admin.py
from django.contrib import admin
from products.models import (
    ProductCategory, Product, PriceList,
)

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
        'name', 'sku', 'category', 'product_type', 'base_price',
        'currency', 'stock_quantity', 'status', 'is_featured'
    ]
    list_filter = [
        'product_type', 'status', 'category', 'is_featured',
        'is_digital', 'track_inventory', 'is_active', 'company'
    ]
    search_fields = [
        'name', 'sku', 'description', 'short_description',
        'meta_title', 'meta_description'
    ]
    ordering = ['-created_at']
    list_editable = ['status', 'is_featured']
    raw_id_fields = ['category', 'owner']
    filter_horizontal = ['tags']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'sku', 'description', 'short_description')
        }),
        ('Product Details', {
            'fields': ('product_type', 'category', 'image_url', 'gallery_urls')
        }),
        ('Pricing', {
            'fields': ('base_price', 'currency', 'cost_price')
        }),
        ('Inventory', {
            'fields': ('track_inventory', 'stock_quantity', 'min_stock_level', 'max_stock_level')
        }),
        ('Physical Properties', {
            'fields': ('weight', 'dimensions'),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'slug'),
            'classes': ('collapse',)
        }),
        ('Status and Visibility', {
            'fields': ('status', 'is_featured', 'is_digital')
        }),
        ('Assignment', {
            'fields': ('owner',)
        }),
        ('Metadata', {
            'fields': ('tags', 'metadata', 'is_active'),
            'classes': ('collapse',)
        })
    )

@admin.register(PriceList)
class PriceListAdmin(admin.ModelAdmin):
    list_display = ['name', 'currency', 'is_default', 'is_active']
    list_filter = ['is_default', 'is_active', 'currency', 'company']
    search_fields = ['name', 'description']
    ordering = ['name']
    list_editable = ['is_default', 'is_active']

# TODO: Add admin registrations for other product models when they are created:
# - ProductVariant
# - PriceListItem  
# - InventoryTransaction
# - ProductReview
# - ProductBundle
# - BundleItem
