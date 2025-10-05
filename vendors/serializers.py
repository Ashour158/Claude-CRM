# vendors/serializers.py
# Vendors serializers

from rest_framework import serializers
from .models import Vendor, VendorContact, PurchaseOrder, PurchaseOrderItem, VendorPerformance
from core.serializers import UserSerializer

class VendorSerializer(serializers.ModelSerializer):
    """Vendor serializer"""
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = Vendor
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class VendorContactSerializer(serializers.ModelSerializer):
    """Vendor contact serializer"""
    
    class Meta:
        model = VendorContact
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class PurchaseOrderSerializer(serializers.ModelSerializer):
    """Purchase order serializer"""
    vendor = VendorSerializer(read_only=True)
    vendor_contact = VendorContactSerializer(read_only=True)
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = PurchaseOrder
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    """Purchase order item serializer"""
    
    class Meta:
        model = PurchaseOrderItem
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class VendorPerformanceSerializer(serializers.ModelSerializer):
    """Vendor performance serializer"""
    
    class Meta:
        model = VendorPerformance
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']