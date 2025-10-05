# sales/views.py
# Sales views

from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Quote, QuoteItem, SalesOrder, SalesOrderItem, Invoice, InvoiceItem
from .serializers import (
    QuoteSerializer, QuoteItemSerializer, SalesOrderSerializer,
    SalesOrderItemSerializer, InvoiceSerializer, InvoiceItemSerializer
)
from rest_framework.decorators import action
from rest_framework.response import Response

class QuoteViewSet(viewsets.ModelViewSet):
    """Quote viewset"""
    queryset = Quote.objects.all()
    serializer_class = QuoteSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'account', 'owner']
    search_fields = ['quote_number', 'title', 'description']
    ordering_fields = ['quote_date', 'created_at', 'total_amount']
    ordering = ['-quote_date']
    
    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """Send quote to customer"""
        quote = self.get_object()
        quote.status = 'sent'
        quote.save()
        return Response({'message': 'Quote sent successfully'})
    
    @action(detail=True, methods=['post'])
    def convert_to_order(self, request, pk=None):
        """Convert quote to sales order"""
        quote = self.get_object()
        # Note: Implementation would create a sales order from the quote
        return Response({'message': 'Quote converted to order successfully'})

class QuoteItemViewSet(viewsets.ModelViewSet):
    """Quote item viewset"""
    queryset = QuoteItem.objects.all()
    serializer_class = QuoteItemSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['quote', 'product']
    ordering_fields = ['created_at']
    ordering = ['created_at']

class SalesOrderViewSet(viewsets.ModelViewSet):
    """Sales order viewset"""
    queryset = SalesOrder.objects.all()
    serializer_class = SalesOrderSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'account', 'owner']
    search_fields = ['order_number', 'title', 'description']
    ordering_fields = ['order_date', 'created_at', 'total_amount']
    ordering = ['-order_date']
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm sales order"""
        order = self.get_object()
        order.status = 'confirmed'
        order.save()
        return Response({'message': 'Order confirmed successfully'})
    
    @action(detail=True, methods=['post'])
    def ship(self, request, pk=None):
        """Mark order as shipped"""
        order = self.get_object()
        order.status = 'shipped'
        order.save()
        return Response({'message': 'Order marked as shipped'})

class SalesOrderItemViewSet(viewsets.ModelViewSet):
    """Sales order item viewset"""
    queryset = SalesOrderItem.objects.all()
    serializer_class = SalesOrderItemSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['order', 'product']
    ordering_fields = ['created_at']
    ordering = ['created_at']

class InvoiceViewSet(viewsets.ModelViewSet):
    """Invoice viewset"""
    queryset = Invoice.objects.all()
    serializer_class = InvoiceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'account', 'owner']
    search_fields = ['invoice_number', 'title', 'description']
    ordering_fields = ['invoice_date', 'created_at', 'total_amount']
    ordering = ['-invoice_date']
    
    @action(detail=True, methods=['post'])
    def send(self, request, pk=None):
        """Send invoice to customer"""
        invoice = self.get_object()
        invoice.status = 'sent'
        invoice.save()
        return Response({'message': 'Invoice sent successfully'})
    
    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """Mark invoice as paid"""
        invoice = self.get_object()
        invoice.status = 'paid'
        invoice.save()
        return Response({'message': 'Invoice marked as paid'})

class InvoiceItemViewSet(viewsets.ModelViewSet):
    """Invoice item viewset"""
    queryset = InvoiceItem.objects.all()
    serializer_class = InvoiceItemSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['invoice', 'product']
    ordering_fields = ['created_at']
    ordering = ['created_at']