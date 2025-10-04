# products/admin.py
from django.contrib import admin
from products.models import (
    ProductCategory, Product, ProductVariant, PriceList,
    PriceListItem, InventoryTransaction, ProductReview,
    ProductBundle, BundleItem
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

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'sku', 'price_adjustment', 'stock_quantity', 'is_active']
    list_filter = ['is_active', 'product__company']
    search_fields = ['name', 'sku', 'product__name']
    ordering = ['product__name', 'name']
    list_editable = ['is_active']
    raw_id_fields = ['product']

@admin.register(PriceList)
class PriceListAdmin(admin.ModelAdmin):
    list_display = ['name', 'currency', 'is_default', 'is_active', 'item_count']
    list_filter = ['is_default', 'is_active', 'currency', 'company']
    search_fields = ['name', 'description']
    ordering = ['name']
    list_editable = ['is_default', 'is_active']
    
    def item_count(self, obj):
        return obj.items.filter(is_active=True).count()
    item_count.short_description = 'Items'

@admin.register(PriceListItem)
class PriceListItemAdmin(admin.ModelAdmin):
    list_display = ['price_list', 'product', 'price', 'discount_percentage', 'is_active']
    list_filter = ['is_active', 'price_list__company']
    search_fields = ['product__name', 'product__sku']
    ordering = ['price_list__name', 'product__name']
    list_editable = ['is_active']
    raw_id_fields = ['price_list', 'product']

@admin.register(InventoryTransaction)
class InventoryTransactionAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'transaction_type', 'quantity', 'reference',
        'created_at', 'created_by'
    ]
    list_filter = [
        'transaction_type', 'created_at', 'product__company'
    ]
    search_fields = [
        'product__name', 'product__sku', 'reference', 'notes'
    ]
    ordering = ['-created_at']
    raw_id_fields = ['product', 'created_by', 'related_quote', 'related_order']
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('product', 'transaction_type', 'quantity', 'reference', 'notes')
        }),
        ('Related Entities', {
            'fields': ('related_quote', 'related_order'),
            'classes': ('collapse',)
        })
    )

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'reviewer_name', 'rating', 'title',
        'is_verified', 'is_approved', 'created_at'
    ]
    list_filter = [
        'rating', 'is_verified', 'is_approved', 'created_at', 'product__company'
    ]
    search_fields = [
        'product__name', 'reviewer_name', 'reviewer_email', 'title', 'content'
    ]
    ordering = ['-created_at']
    list_editable = ['is_verified', 'is_approved']
    raw_id_fields = ['product']
    
    fieldsets = (
        ('Review Details', {
            'fields': ('product', 'reviewer_name', 'reviewer_email', 'rating', 'title', 'content')
        }),
        ('Status', {
            'fields': ('is_verified', 'is_approved')
        })
    )

@admin.register(ProductBundle)
class ProductBundleAdmin(admin.ModelAdmin):
    list_display = ['name', 'bundle_price', 'is_active', 'item_count']
    list_filter = ['is_active', 'company']
    search_fields = ['name', 'description']
    ordering = ['name']
    list_editable = ['is_active']
    
    def item_count(self, obj):
        return obj.bundle_items.count()
    item_count.short_description = 'Items'

@admin.register(BundleItem)
class BundleItemAdmin(admin.ModelAdmin):
    list_display = ['bundle', 'product', 'quantity']
    list_filter = ['bundle__company']
    search_fields = ['bundle__name', 'product__name', 'product__sku']
    ordering = ['bundle__name', 'product__name']
    raw_id_fields = ['bundle', 'product']