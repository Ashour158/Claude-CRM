# vendors/serializers.py
from rest_framework import serializers
from vendors.models import (
    Vendor, VendorContact, VendorProduct, PurchaseOrder,
    PurchaseOrderItem, VendorInvoice, VendorPayment
)
from products.serializers import ProductListSerializer
from core.serializers import UserBasicSerializer

class VendorContactSerializer(serializers.ModelSerializer):
    """Serializer for VendorContact"""
    
    class Meta:
        model = VendorContact
        fields = [
            'id', 'contact_type', 'name', 'title', 'email',
            'phone', 'mobile', 'department', 'is_primary',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

class VendorProductSerializer(serializers.ModelSerializer):
    """Serializer for VendorProduct"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    product_detail = ProductListSerializer(source='product', read_only=True)
    
    class Meta:
        model = VendorProduct
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'product_detail',
            'vendor_sku', 'vendor_price', 'currency', 'minimum_order_quantity',
            'lead_time_days', 'is_preferred', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class VendorListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for vendor lists"""
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    contact_count = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Vendor
        fields = [
            'id', 'name', 'vendor_code', 'vendor_type', 'status',
            'primary_contact_name', 'primary_contact_email', 'primary_contact_phone',
            'city', 'country', 'currency', 'rating', 'owner', 'owner_name',
            'contact_count', 'product_count', 'created_at'
        ]
    
    def get_contact_count(self, obj):
        return obj.contacts.count()
    
    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()

class VendorSerializer(serializers.ModelSerializer):
    """Full serializer for Vendor"""
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    owner_detail = UserBasicSerializer(source='owner', read_only=True)
    contacts = VendorContactSerializer(many=True, read_only=True)
    products = VendorProductSerializer(many=True, read_only=True)
    contact_count = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    order_count = serializers.SerializerMethodField()
    total_spent = serializers.SerializerMethodField()
    
    class Meta:
        model = Vendor
        fields = [
            'id', 'name', 'vendor_code', 'vendor_type', 'status',
            'primary_contact_name', 'primary_contact_email', 'primary_contact_phone',
            'business_registration_number', 'tax_id', 'website',
            'billing_address', 'shipping_address', 'city', 'state',
            'postal_code', 'country', 'currency', 'payment_terms', 'credit_limit',
            'rating', 'on_time_delivery_rate', 'quality_rating',
            'owner', 'owner_name', 'owner_detail', 'description', 'notes',
            'tags', 'metadata', 'is_active',
            'contacts', 'products', 'contact_count', 'product_count',
            'order_count', 'total_spent',
            'created_at', 'updated_at', 'created_by_name'
        ]
        read_only_fields = [
            'id', 'vendor_code', 'created_at', 'updated_at'
        ]
    
    def get_contact_count(self, obj):
        return obj.contacts.count()
    
    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()
    
    def get_order_count(self, obj):
        return obj.purchase_orders.count()
    
    def get_total_spent(self, obj):
        from django.db.models import Sum
        total = obj.purchase_orders.filter(status='received').aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        return float(total)
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['company'] = request.active_company
        validated_data['created_by'] = request.user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        request = self.context.get('request')
        validated_data['updated_by'] = request.user
        return super().update(instance, validated_data)

class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    """Serializer for PurchaseOrderItem"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    product_detail = ProductListSerializer(source='product', read_only=True)
    is_fully_received = serializers.ReadOnlyField()
    remaining_quantity = serializers.ReadOnlyField()
    
    class Meta:
        model = PurchaseOrderItem
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'product_detail',
            'vendor_product', 'description', 'quantity', 'unit_price',
            'discount_percentage', 'discount_amount', 'total_price',
            'received_quantity', 'is_fully_received', 'remaining_quantity',
            'created_at'
        ]
        read_only_fields = [
            'id', 'discount_amount', 'total_price', 'is_fully_received',
            'remaining_quantity', 'created_at'
        ]

class PurchaseOrderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for purchase order lists"""
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'order_number', 'title', 'vendor', 'vendor_name',
            'status', 'total_amount', 'currency', 'order_date',
            'expected_delivery_date', 'actual_delivery_date',
            'owner', 'owner_name', 'item_count', 'created_at'
        ]
    
    def get_item_count(self, obj):
        return obj.items.count()

class PurchaseOrderSerializer(serializers.ModelSerializer):
    """Full serializer for PurchaseOrder"""
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    vendor_detail = VendorListSerializer(source='vendor', read_only=True)
    vendor_contact_name = serializers.CharField(source='vendor_contact.name', read_only=True)
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    owner_detail = UserBasicSerializer(source='owner', read_only=True)
    items = PurchaseOrderItemSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PurchaseOrder
        fields = [
            'id', 'order_number', 'title', 'description',
            'vendor', 'vendor_name', 'vendor_detail',
            'vendor_contact', 'vendor_contact_name',
            'status', 'order_date', 'expected_delivery_date', 'actual_delivery_date',
            'subtotal', 'tax_rate', 'tax_amount',
            'discount_percentage', 'discount_amount', 'total_amount', 'currency',
            'owner', 'owner_name', 'owner_detail',
            'shipping_address', 'shipping_method', 'tracking_number',
            'terms_conditions', 'notes', 'metadata', 'is_active',
            'items', 'item_count',
            'created_at', 'updated_at', 'created_by_name'
        ]
        read_only_fields = [
            'id', 'order_number', 'created_at', 'updated_at'
        ]
    
    def get_item_count(self, obj):
        return obj.items.count()
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['company'] = request.active_company
        validated_data['created_by'] = request.user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        request = self.context.get('request')
        validated_data['updated_by'] = request.user
        return super().update(instance, validated_data)

class VendorInvoiceSerializer(serializers.ModelSerializer):
    """Serializer for VendorInvoice"""
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    purchase_order_number = serializers.CharField(source='purchase_order.order_number', read_only=True)
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = VendorInvoice
        fields = [
            'id', 'invoice_number', 'title', 'description',
            'vendor', 'vendor_name', 'purchase_order', 'purchase_order_number',
            'status', 'invoice_date', 'due_date', 'received_date', 'paid_date',
            'subtotal', 'tax_rate', 'tax_amount',
            'discount_percentage', 'discount_amount', 'total_amount', 'currency',
            'owner', 'owner_name', 'notes', 'metadata', 'is_active',
            'is_overdue', 'created_at', 'updated_at', 'created_by_name'
        ]
        read_only_fields = [
            'id', 'is_overdue', 'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['company'] = request.active_company
        validated_data['created_by'] = request.user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        request = self.context.get('request')
        validated_data['updated_by'] = request.user
        return super().update(instance, validated_data)

class VendorPaymentSerializer(serializers.ModelSerializer):
    """Serializer for VendorPayment"""
    vendor_name = serializers.CharField(source='vendor.name', read_only=True)
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    
    class Meta:
        model = VendorPayment
        fields = [
            'id', 'payment_number', 'amount', 'currency',
            'vendor', 'vendor_name', 'invoice', 'invoice_number',
            'payment_method', 'status', 'payment_date', 'reference_number',
            'notes', 'metadata', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'payment_number', 'created_at']
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['company'] = request.active_company
        validated_data['created_by'] = request.user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        request = self.context.get('request')
        validated_data['updated_by'] = request.user
        return super().update(instance, validated_data)

class VendorStatsSerializer(serializers.Serializer):
    """Serializer for vendor statistics"""
    total_vendors = serializers.IntegerField()
    active_vendors = serializers.IntegerField()
    vendors_by_type = serializers.DictField()
    vendors_by_status = serializers.DictField()
    total_purchase_orders = serializers.IntegerField()
    total_purchase_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    average_order_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    top_vendors = serializers.ListField()
    monthly_spending = serializers.ListField()
    overdue_invoices = serializers.IntegerField()
    pending_orders = serializers.IntegerField()

class VendorPerformanceSerializer(serializers.Serializer):
    """Serializer for vendor performance metrics"""
    vendor = VendorListSerializer()
    total_orders = serializers.IntegerField()
    total_spent = serializers.DecimalField(max_digits=15, decimal_places=2)
    average_delivery_time = serializers.IntegerField()
    on_time_delivery_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    quality_rating = serializers.DecimalField(max_digits=3, decimal_places=2)
    last_order_date = serializers.DateTimeField()
    pending_orders = serializers.IntegerField()
    overdue_invoices = serializers.IntegerField()
