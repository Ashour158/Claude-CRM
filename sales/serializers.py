# sales/serializers.py
from rest_framework import serializers
from sales.models import (
    Quote, QuoteItem, SalesOrder, SalesOrderItem,
    Invoice, InvoiceItem, Payment
)
from crm.serializers import AccountSerializer, ContactSerializer
from deals.serializers import DealListSerializer
from products.serializers import ProductListSerializer
from core.serializers import UserBasicSerializer

class QuoteItemSerializer(serializers.ModelSerializer):
    """Serializer for QuoteItem"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    product_detail = ProductListSerializer(source='product', read_only=True)
    
    class Meta:
        model = QuoteItem
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'product_detail',
            'description', 'quantity', 'unit_price', 'discount_percentage',
            'discount_amount', 'total_price', 'created_at'
        ]
        read_only_fields = ['id', 'discount_amount', 'total_price', 'created_at']

class QuoteListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for quote lists"""
    account_name = serializers.CharField(source='account.name', read_only=True)
    contact_name = serializers.CharField(source='contact.full_name', read_only=True)
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    is_expired = serializers.ReadOnlyField()
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Quote
        fields = [
            'id', 'quote_number', 'title', 'account', 'account_name',
            'contact', 'contact_name', 'status', 'total_amount', 'currency',
            'valid_until', 'owner', 'owner_name', 'is_expired', 'item_count',
            'created_at'
        ]
    
    def get_item_count(self, obj):
        return obj.items.count()

class QuoteSerializer(serializers.ModelSerializer):
    """Full serializer for Quote"""
    account_name = serializers.CharField(source='account.name', read_only=True)
    account_detail = AccountSerializer(source='account', read_only=True)
    contact_name = serializers.CharField(source='contact.full_name', read_only=True)
    contact_detail = ContactSerializer(source='contact', read_only=True)
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    owner_detail = UserBasicSerializer(source='owner', read_only=True)
    deal_detail = DealListSerializer(source='deal', read_only=True)
    is_expired = serializers.ReadOnlyField()
    items = QuoteItemSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Quote
        fields = [
            'id', 'quote_number', 'title', 'description',
            'account', 'account_name', 'account_detail',
            'contact', 'contact_name', 'contact_detail',
            'deal', 'deal_detail', 'status', 'valid_until',
            'sent_date', 'viewed_date', 'accepted_date',
            'subtotal', 'tax_rate', 'tax_amount',
            'discount_percentage', 'discount_amount', 'total_amount', 'currency',
            'owner', 'owner_name', 'owner_detail',
            'terms_conditions', 'notes', 'metadata', 'is_active',
            'items', 'item_count', 'is_expired',
            'created_at', 'updated_at', 'created_by_name'
        ]
        read_only_fields = [
            'id', 'is_expired', 'created_at', 'updated_at'
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

class SalesOrderItemSerializer(serializers.ModelSerializer):
    """Serializer for SalesOrderItem"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    product_detail = ProductListSerializer(source='product', read_only=True)
    
    class Meta:
        model = SalesOrderItem
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'product_detail',
            'description', 'quantity', 'unit_price', 'discount_percentage',
            'discount_amount', 'total_price', 'created_at'
        ]
        read_only_fields = ['id', 'discount_amount', 'total_price', 'created_at']

class SalesOrderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for sales order lists"""
    account_name = serializers.CharField(source='account.name', read_only=True)
    contact_name = serializers.CharField(source='contact.full_name', read_only=True)
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = SalesOrder
        fields = [
            'id', 'order_number', 'title', 'account', 'account_name',
            'contact', 'contact_name', 'status', 'total_amount', 'currency',
            'order_date', 'expected_delivery_date', 'actual_delivery_date',
            'owner', 'owner_name', 'item_count', 'created_at'
        ]
    
    def get_item_count(self, obj):
        return obj.items.count()

class SalesOrderSerializer(serializers.ModelSerializer):
    """Full serializer for SalesOrder"""
    account_name = serializers.CharField(source='account.name', read_only=True)
    account_detail = AccountSerializer(source='account', read_only=True)
    contact_name = serializers.CharField(source='contact.full_name', read_only=True)
    contact_detail = ContactSerializer(source='contact', read_only=True)
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    owner_detail = UserBasicSerializer(source='owner', read_only=True)
    quote_detail = QuoteListSerializer(source='quote', read_only=True)
    deal_detail = DealListSerializer(source='deal', read_only=True)
    items = SalesOrderItemSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = SalesOrder
        fields = [
            'id', 'order_number', 'title', 'description',
            'account', 'account_name', 'account_detail',
            'contact', 'contact_name', 'contact_detail',
            'quote', 'quote_detail', 'deal', 'deal_detail',
            'status', 'order_date', 'expected_delivery_date', 'actual_delivery_date',
            'subtotal', 'tax_rate', 'tax_amount',
            'discount_percentage', 'discount_amount', 'total_amount', 'currency',
            'owner', 'owner_name', 'owner_detail',
            'shipping_address', 'billing_address', 'shipping_method', 'tracking_number',
            'terms_conditions', 'notes', 'metadata', 'is_active',
            'items', 'item_count',
            'created_at', 'updated_at', 'created_by_name'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at'
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

class InvoiceItemSerializer(serializers.ModelSerializer):
    """Serializer for InvoiceItem"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    product_detail = ProductListSerializer(source='product', read_only=True)
    
    class Meta:
        model = InvoiceItem
        fields = [
            'id', 'product', 'product_name', 'product_sku', 'product_detail',
            'description', 'quantity', 'unit_price', 'discount_percentage',
            'discount_amount', 'total_price', 'created_at'
        ]
        read_only_fields = ['id', 'discount_amount', 'total_price', 'created_at']

class InvoiceListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for invoice lists"""
    account_name = serializers.CharField(source='account.name', read_only=True)
    contact_name = serializers.CharField(source='contact.full_name', read_only=True)
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    is_overdue = serializers.ReadOnlyField()
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'title', 'account', 'account_name',
            'contact', 'contact_name', 'status', 'total_amount', 'currency',
            'paid_amount', 'balance_amount', 'invoice_date', 'due_date',
            'owner', 'owner_name', 'is_overdue', 'item_count', 'created_at'
        ]
    
    def get_item_count(self, obj):
        return obj.items.count()

class InvoiceSerializer(serializers.ModelSerializer):
    """Full serializer for Invoice"""
    account_name = serializers.CharField(source='account.name', read_only=True)
    account_detail = AccountSerializer(source='account', read_only=True)
    contact_name = serializers.CharField(source='contact.full_name', read_only=True)
    contact_detail = ContactSerializer(source='contact', read_only=True)
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    owner_detail = UserBasicSerializer(source='owner', read_only=True)
    sales_order_detail = SalesOrderListSerializer(source='sales_order', read_only=True)
    deal_detail = DealListSerializer(source='deal', read_only=True)
    is_overdue = serializers.ReadOnlyField()
    items = InvoiceItemSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()
    payment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'title', 'description',
            'account', 'account_name', 'account_detail',
            'contact', 'contact_name', 'contact_detail',
            'sales_order', 'sales_order_detail', 'deal', 'deal_detail',
            'status', 'invoice_date', 'due_date', 'sent_date', 'viewed_date', 'paid_date',
            'subtotal', 'tax_rate', 'tax_amount',
            'discount_percentage', 'discount_amount', 'total_amount', 'currency',
            'paid_amount', 'balance_amount',
            'owner', 'owner_name', 'owner_detail',
            'terms_conditions', 'notes', 'metadata', 'is_active',
            'items', 'item_count', 'payment_count', 'is_overdue',
            'created_at', 'updated_at', 'created_by_name'
        ]
        read_only_fields = [
            'id', 'is_overdue', 'created_at', 'updated_at'
        ]
    
    def get_item_count(self, obj):
        return obj.items.count()
    
    def get_payment_count(self, obj):
        return obj.payments.count()
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['company'] = request.active_company
        validated_data['created_by'] = request.user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        request = self.context.get('request')
        validated_data['updated_by'] = request.user
        return super().update(instance, validated_data)

class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment"""
    invoice_number = serializers.CharField(source='invoice.invoice_number', read_only=True)
    account_name = serializers.CharField(source='account.name', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'payment_number', 'amount', 'currency',
            'invoice', 'invoice_number', 'account', 'account_name',
            'payment_method', 'status', 'payment_date', 'reference_number',
            'notes', 'metadata', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['company'] = request.active_company
        validated_data['created_by'] = request.user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        request = self.context.get('request')
        validated_data['updated_by'] = request.user
        return super().update(instance, validated_data)

class SalesStatsSerializer(serializers.Serializer):
    """Serializer for sales statistics"""
    total_quotes = serializers.IntegerField()
    total_orders = serializers.IntegerField()
    total_invoices = serializers.IntegerField()
    total_payments = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)
    outstanding_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    quotes_by_status = serializers.DictField()
    orders_by_status = serializers.DictField()
    invoices_by_status = serializers.DictField()
    payments_by_method = serializers.DictField()
    monthly_revenue = serializers.ListField()
    top_customers = serializers.ListField()
    conversion_rate = serializers.DecimalField(max_digits=5, decimal_places=2)

class SalesPipelineSerializer(serializers.Serializer):
    """Serializer for sales pipeline data"""
    quotes = QuoteListSerializer(many=True)
    orders = SalesOrderListSerializer(many=True)
    invoices = InvoiceListSerializer(many=True)
    total_pipeline_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    conversion_funnel = serializers.DictField()
