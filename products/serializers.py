# products/serializers.py
from rest_framework import serializers
from products.models import (
    ProductCategory, Product, ProductVariant, PriceList,
    PriceListItem, InventoryTransaction, ProductReview,
    ProductBundle, BundleItem
)
from core.serializers import UserBasicSerializer

class ProductCategorySerializer(serializers.ModelSerializer):
    """Serializer for ProductCategory"""
    parent_name = serializers.CharField(source='parent.name', read_only=True)
    full_path = serializers.ReadOnlyField()
    product_count = serializers.SerializerMethodField()
    children_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductCategory
        fields = [
            'id', 'name', 'description', 'parent', 'parent_name',
            'image_url', 'is_active', 'full_path', 'product_count',
            'children_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()
    
    def get_children_count(self, obj):
        return obj.children.filter(is_active=True).count()

class ProductCategoryListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for product category lists"""
    full_path = serializers.ReadOnlyField()
    
    class Meta:
        model = ProductCategory
        fields = ['id', 'name', 'parent', 'full_path', 'is_active']

class ProductVariantSerializer(serializers.ModelSerializer):
    """Serializer for ProductVariant"""
    total_price = serializers.ReadOnlyField()
    
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'name', 'sku', 'price_adjustment', 'stock_quantity',
            'attributes', 'is_active', 'total_price', 'created_at'
        ]
        read_only_fields = ['id', 'total_price', 'created_at']

class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for product lists"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    margin_percentage = serializers.ReadOnlyField()
    is_low_stock = serializers.ReadOnlyField()
    is_out_of_stock = serializers.ReadOnlyField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'product_type', 'category', 'category_name',
            'base_price', 'currency', 'stock_quantity', 'status',
            'is_featured', 'owner', 'owner_name', 'margin_percentage',
            'is_low_stock', 'is_out_of_stock', 'created_at'
        ]

class ProductSerializer(serializers.ModelSerializer):
    """Full serializer for Product"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_detail = ProductCategorySerializer(source='category', read_only=True)
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    owner_detail = UserBasicSerializer(source='owner', read_only=True)
    margin_percentage = serializers.ReadOnlyField()
    is_low_stock = serializers.ReadOnlyField()
    is_out_of_stock = serializers.ReadOnlyField()
    variants = ProductVariantSerializer(many=True, read_only=True)
    variant_count = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'sku', 'description', 'short_description',
            'product_type', 'category', 'category_name', 'category_detail',
            'base_price', 'currency', 'cost_price', 'margin_percentage',
            'track_inventory', 'stock_quantity', 'min_stock_level', 'max_stock_level',
            'weight', 'dimensions', 'image_url', 'gallery_urls',
            'meta_title', 'meta_description', 'slug',
            'status', 'is_featured', 'is_digital',
            'owner', 'owner_name', 'owner_detail',
            'tags', 'metadata', 'is_active',
            'variants', 'variant_count', 'review_count', 'average_rating',
            'is_low_stock', 'is_out_of_stock',
            'created_at', 'updated_at', 'created_by_name'
        ]
        read_only_fields = [
            'id', 'margin_percentage', 'is_low_stock', 'is_out_of_stock',
            'created_at', 'updated_at'
        ]
    
    def get_variant_count(self, obj):
        return obj.variants.count()
    
    def get_review_count(self, obj):
        return obj.reviews.filter(is_approved=True).count()
    
    def get_average_rating(self, obj):
        reviews = obj.reviews.filter(is_approved=True)
        if reviews.exists():
            return sum(review.rating for review in reviews) / reviews.count()
        return 0
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['company'] = request.active_company
        validated_data['created_by'] = request.user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        request = self.context.get('request')
        validated_data['updated_by'] = request.user
        return super().update(instance, validated_data)

class PriceListSerializer(serializers.ModelSerializer):
    """Serializer for PriceList"""
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PriceList
        fields = [
            'id', 'name', 'description', 'currency', 'is_default',
            'is_active', 'valid_from', 'valid_until', 'item_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_item_count(self, obj):
        return obj.items.filter(is_active=True).count()

class PriceListItemSerializer(serializers.ModelSerializer):
    """Serializer for PriceListItem"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    discounted_price = serializers.ReadOnlyField()
    
    class Meta:
        model = PriceListItem
        fields = [
            'id', 'product', 'product_name', 'product_sku',
            'price', 'discount_percentage', 'discounted_price',
            'min_quantity', 'max_quantity', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'discounted_price', 'created_at']

class InventoryTransactionSerializer(serializers.ModelSerializer):
    """Serializer for InventoryTransaction"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    
    class Meta:
        model = InventoryTransaction
        fields = [
            'id', 'product', 'product_name', 'product_sku',
            'transaction_type', 'quantity', 'reference', 'notes',
            'related_quote', 'related_order', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class ProductReviewSerializer(serializers.ModelSerializer):
    """Serializer for ProductReview"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = ProductReview
        fields = [
            'id', 'product', 'product_name', 'reviewer_name',
            'reviewer_email', 'rating', 'title', 'content',
            'is_verified', 'is_approved', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class BundleItemSerializer(serializers.ModelSerializer):
    """Serializer for BundleItem"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    product_price = serializers.DecimalField(source='product.base_price', read_only=True, max_digits=15, decimal_places=2)
    
    class Meta:
        model = BundleItem
        fields = [
            'id', 'product', 'product_name', 'product_sku',
            'product_price', 'quantity', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class ProductBundleSerializer(serializers.ModelSerializer):
    """Serializer for ProductBundle"""
    bundle_items = BundleItemSerializer(many=True, read_only=True)
    total_individual_price = serializers.ReadOnlyField()
    savings_amount = serializers.ReadOnlyField()
    savings_percentage = serializers.ReadOnlyField()
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ProductBundle
        fields = [
            'id', 'name', 'description', 'bundle_price',
            'is_active', 'bundle_items', 'total_individual_price',
            'savings_amount', 'savings_percentage', 'item_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'total_individual_price', 'savings_amount',
            'savings_percentage', 'created_at', 'updated_at'
        ]
    
    def get_item_count(self, obj):
        return obj.bundle_items.count()

class ProductStatsSerializer(serializers.Serializer):
    """Serializer for product statistics"""
    total_products = serializers.IntegerField()
    active_products = serializers.IntegerField()
    low_stock_products = serializers.IntegerField()
    out_of_stock_products = serializers.IntegerField()
    products_by_category = serializers.DictField()
    products_by_type = serializers.DictField()
    products_by_status = serializers.DictField()
    total_inventory_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    average_product_price = serializers.DecimalField(max_digits=15, decimal_places=2)
    top_products = serializers.ListField()
    monthly_trend = serializers.ListField()

class ProductSearchSerializer(serializers.Serializer):
    """Serializer for product search results"""
    products = ProductListSerializer(many=True)
    total_count = serializers.IntegerField()
    categories = ProductCategoryListSerializer(many=True)
    filters = serializers.DictField()
    sort_options = serializers.ListField()