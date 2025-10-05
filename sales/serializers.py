# sales/serializers.py
# Sales serializers

from rest_framework import serializers
from .models import Quote, QuoteItem, SalesOrder, SalesOrderItem, Invoice, InvoiceItem
from core.serializers import UserSerializer
from crm.serializers import AccountSerializer, ContactSerializer
from products.serializers import ProductSerializer

class QuoteSerializer(serializers.ModelSerializer):
    """Quote serializer"""
    account = AccountSerializer(read_only=True)
    contact = ContactSerializer(read_only=True)
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = Quote
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class QuoteItemSerializer(serializers.ModelSerializer):
    """Quote item serializer"""
    product = ProductSerializer(read_only=True)
    
    class Meta:
        model = QuoteItem
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class SalesOrderSerializer(serializers.ModelSerializer):
    """Sales order serializer"""
    account = AccountSerializer(read_only=True)
    contact = ContactSerializer(read_only=True)
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = SalesOrder
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class SalesOrderItemSerializer(serializers.ModelSerializer):
    """Sales order item serializer"""
    product = ProductSerializer(read_only=True)
    
    class Meta:
        model = SalesOrderItem
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class InvoiceSerializer(serializers.ModelSerializer):
    """Invoice serializer"""
    account = AccountSerializer(read_only=True)
    contact = ContactSerializer(read_only=True)
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = Invoice
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class InvoiceItemSerializer(serializers.ModelSerializer):
    """Invoice item serializer"""
    product = ProductSerializer(read_only=True)
    
    class Meta:
        model = InvoiceItem
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']