# vendors/views.py
# Vendors views

from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Vendor, VendorContact, PurchaseOrder, PurchaseOrderItem, VendorPerformance
from .serializers import (
    VendorSerializer, VendorContactSerializer, PurchaseOrderSerializer,
    PurchaseOrderItemSerializer, VendorPerformanceSerializer
)
from rest_framework.decorators import action
from rest_framework.response import Response

class VendorViewSet(viewsets.ModelViewSet):
    """Vendor viewset"""
    queryset = Vendor.objects.all()
    serializer_class = VendorSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['vendor_type', 'status', 'is_approved', 'is_preferred']
    search_fields = ['name', 'email', 'phone']
    ordering_fields = ['name', 'created_at', 'rating']
    ordering = ['name']
    
    @action(detail=True, methods=['get'])
    def contacts(self, request, pk=None):
        """Get vendor contacts"""
        vendor = self.get_object()
        contacts = vendor.contacts.all()
        serializer = VendorContactSerializer(contacts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        """Get vendor performance"""
        vendor = self.get_object()
        performance = vendor.performance_records.all()
        serializer = VendorPerformanceSerializer(performance, many=True)
        return Response(serializer.data)

class VendorContactViewSet(viewsets.ModelViewSet):
    """Vendor contact viewset"""
    queryset = VendorContact.objects.all()
    serializer_class = VendorContactSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['vendor', 'is_primary', 'is_active']
    search_fields = ['name', 'email', 'phone']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

class PurchaseOrderViewSet(viewsets.ModelViewSet):
    """Purchase order viewset"""
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'vendor', 'owner']
    search_fields = ['po_number', 'title', 'description']
    ordering_fields = ['order_date', 'created_at', 'total_amount']
    ordering = ['-order_date']
    
    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """Send purchase order to vendor"""
        po = self.get_object()
        po.status = 'sent'
        po.save()
        return Response({'message': 'Purchase order sent successfully'})
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge purchase order"""
        po = self.get_object()
        po.status = 'acknowledged'
        po.save()
        return Response({'message': 'Purchase order acknowledged'})
    
    @action(detail=True, methods=['post'])
    def receive(self, request, pk=None):
        """Mark purchase order as received"""
        po = self.get_object()
        po.status = 'received'
        po.save()
        return Response({'message': 'Purchase order marked as received'})

class PurchaseOrderItemViewSet(viewsets.ModelViewSet):
    """Purchase order item viewset"""
    queryset = PurchaseOrderItem.objects.all()
    serializer_class = PurchaseOrderItemSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['purchase_order']
    ordering_fields = ['created_at']
    ordering = ['created_at']

class VendorPerformanceViewSet(viewsets.ModelViewSet):
    """Vendor performance viewset"""
    queryset = VendorPerformance.objects.all()
    serializer_class = VendorPerformanceSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['vendor']
    ordering_fields = ['period_end', 'overall_score']
    ordering = ['-period_end']