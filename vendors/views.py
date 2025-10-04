# vendors/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta

from vendors.models import (
    Vendor, VendorContact, VendorProduct, PurchaseOrder,
    PurchaseOrderItem, VendorInvoice, VendorPayment
)
from vendors.serializers import (
    VendorSerializer, VendorListSerializer, VendorContactSerializer,
    VendorProductSerializer, PurchaseOrderSerializer, PurchaseOrderListSerializer,
    PurchaseOrderItemSerializer, VendorInvoiceSerializer, VendorPaymentSerializer,
    VendorStatsSerializer, VendorPerformanceSerializer
)
from core.permissions import IsCompanyMember
from core.cache import cache_api_response

class VendorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Vendor CRUD operations
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = [
        'vendor_type', 'status', 'owner', 'is_active', 'country', 'currency'
    ]
    search_fields = [
        'name', 'vendor_code', 'primary_contact_name', 'primary_contact_email',
        'business_registration_number', 'tax_id', 'description'
    ]
    ordering_fields = [
        'name', 'vendor_code', 'rating', 'created_at'
    ]
    ordering = ['name']
    
    def get_queryset(self):
        return Vendor.objects.filter(
            company=self.request.active_company
        ).select_related(
            'owner', 'created_by'
        ).prefetch_related(
            'contacts', 'products__product', 'tags'
        )
    
    def get_serializer_class(self):
        if self.action == 'list':
            return VendorListSerializer
        return VendorSerializer
    
    @action(detail=True, methods=['get'])
    def contacts(self, request, pk=None):
        """Get vendor contacts"""
        vendor = self.get_object()
        contacts = vendor.contacts.all()
        serializer = VendorContactSerializer(contacts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_contact(self, request, pk=None):
        """Add contact to vendor"""
        vendor = self.get_object()
        serializer = VendorContactSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(vendor=vendor, company=request.active_company)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """Get vendor products"""
        vendor = self.get_object()
        products = vendor.products.filter(is_active=True)
        serializer = VendorProductSerializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_product(self, request, pk=None):
        """Add product to vendor"""
        vendor = self.get_object()
        serializer = VendorProductSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(vendor=vendor, company=request.active_company)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def orders(self, request, pk=None):
        """Get vendor purchase orders"""
        vendor = self.get_object()
        orders = vendor.purchase_orders.all().order_by('-created_at')
        serializer = PurchaseOrderListSerializer(orders, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        """Get vendor performance metrics"""
        vendor = self.get_object()
        
        # Calculate performance metrics
        total_orders = vendor.purchase_orders.count()
        total_spent = vendor.purchase_orders.filter(status='received').aggregate(
            total=Sum('total_amount')
        )['total'] or 0
        
        # Calculate average delivery time
        completed_orders = vendor.purchase_orders.filter(
            status='received',
            actual_delivery_date__isnull=False,
            order_date__isnull=False
        )
        delivery_times = []
        for order in completed_orders:
            if order.order_date and order.actual_delivery_date:
                time_diff = order.actual_delivery_date - order.order_date
                delivery_times.append(time_diff.days)
        
        average_delivery_time = sum(delivery_times) / len(delivery_times) if delivery_times else 0
        
        # Calculate on-time delivery rate
        on_time_orders = 0
        for order in completed_orders:
            if order.expected_delivery_date and order.actual_delivery_date:
                if order.actual_delivery_date <= order.expected_delivery_date:
                    on_time_orders += 1
        
        on_time_delivery_rate = (on_time_orders / len(completed_orders) * 100) if completed_orders else 0
        
        # Get last order date
        last_order = vendor.purchase_orders.order_by('-order_date').first()
        last_order_date = last_order.order_date if last_order else None
        
        # Count pending orders and overdue invoices
        pending_orders = vendor.purchase_orders.filter(
            status__in=['sent', 'acknowledged', 'confirmed']
        ).count()
        
        overdue_invoices = VendorInvoice.objects.filter(
            vendor=vendor,
            status__in=['received', 'verified', 'approved'],
            due_date__lt=timezone.now().date()
        ).count()
        
        performance_data = {
            'vendor': VendorListSerializer(vendor).data,
            'total_orders': total_orders,
            'total_spent': float(total_spent),
            'average_delivery_time': int(average_delivery_time),
            'on_time_delivery_rate': round(on_time_delivery_rate, 2),
            'quality_rating': float(vendor.quality_rating or 0),
            'last_order_date': last_order_date,
            'pending_orders': pending_orders,
            'overdue_invoices': overdue_invoices
        }
        
        serializer = VendorPerformanceSerializer(performance_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    @cache_api_response(timeout=300)
    def stats(self, request):
        """Get vendor statistics"""
        queryset = self.get_queryset()
        
        # Basic counts
        total_vendors = queryset.count()
        active_vendors = queryset.filter(status='active').count()
        
        # Vendors by type
        vendors_by_type = {}
        for vendor_type, _ in Vendor.VENDOR_TYPES:
            count = queryset.filter(vendor_type=vendor_type).count()
            vendors_by_type[vendor_type] = count
        
        # Vendors by status
        vendors_by_status = {}
        for status_choice, _ in Vendor.STATUS_CHOICES:
            count = queryset.filter(status=status_choice).count()
            vendors_by_status[status_choice] = count
        
        # Purchase order statistics
        total_purchase_orders = PurchaseOrder.objects.filter(company=request.active_company).count()
        total_purchase_amount = PurchaseOrder.objects.filter(
            company=request.active_company,
            status='received'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        average_order_value = PurchaseOrder.objects.filter(
            company=request.active_company,
            status='received'
        ).aggregate(avg=Avg('total_amount'))['avg'] or 0
        
        # Top vendors by spending
        top_vendors = []
        vendor_spending = PurchaseOrder.objects.filter(
            company=request.active_company,
            status='received'
        ).values('vendor__name').annotate(
            total_spent=Sum('total_amount')
        ).order_by('-total_spent')[:10]
        
        for vendor in vendor_spending:
            top_vendors.append({
                'vendor_name': vendor['vendor__name'],
                'total_spent': float(vendor['total_spent'])
            })
        
        # Monthly spending trend
        monthly_spending = []
        for i in range(12):
            month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            
            month_orders = PurchaseOrder.objects.filter(
                company=request.active_company,
                status='received',
                order_date__range=[month_start.date(), month_end.date()]
            )
            
            monthly_spending.append({
                'month': month_start.strftime('%Y-%m'),
                'spending': float(month_orders.aggregate(total=Sum('total_amount'))['total'] or 0)
            })
        
        monthly_spending.reverse()
        
        # Overdue invoices and pending orders
        overdue_invoices = VendorInvoice.objects.filter(
            company=request.active_company,
            status__in=['received', 'verified', 'approved'],
            due_date__lt=timezone.now().date()
        ).count()
        
        pending_orders = PurchaseOrder.objects.filter(
            company=request.active_company,
            status__in=['sent', 'acknowledged', 'confirmed']
        ).count()
        
        stats_data = {
            'total_vendors': total_vendors,
            'active_vendors': active_vendors,
            'vendors_by_type': vendors_by_type,
            'vendors_by_status': vendors_by_status,
            'total_purchase_orders': total_purchase_orders,
            'total_purchase_amount': float(total_purchase_amount),
            'average_order_value': float(average_order_value),
            'top_vendors': top_vendors,
            'monthly_spending': monthly_spending,
            'overdue_invoices': overdue_invoices,
            'pending_orders': pending_orders
        }
        
        serializer = VendorStatsSerializer(stats_data)
        return Response(serializer.data)

class VendorContactViewSet(viewsets.ModelViewSet):
    """
    ViewSet for VendorContact CRUD operations
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = ['contact_type', 'is_primary', 'vendor']
    search_fields = ['name', 'title', 'email', 'phone', 'department']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        return VendorContact.objects.filter(
            vendor__company=self.request.active_company
        ).select_related('vendor')
    
    def get_serializer_class(self):
        return VendorContactSerializer

class VendorProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for VendorProduct CRUD operations
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = ['vendor', 'product', 'is_preferred', 'is_active']
    search_fields = ['vendor_sku', 'product__name', 'product__sku']
    ordering_fields = ['vendor_price', 'lead_time_days', 'created_at']
    ordering = ['product__name']
    
    def get_queryset(self):
        return VendorProduct.objects.filter(
            vendor__company=self.request.active_company
        ).select_related('vendor', 'product')
    
    def get_serializer_class(self):
        return VendorProductSerializer

class PurchaseOrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for PurchaseOrder CRUD operations
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = [
        'status', 'vendor', 'owner', 'is_active'
    ]
    search_fields = [
        'order_number', 'title', 'description', 'tracking_number', 'notes'
    ]
    ordering_fields = [
        'order_number', 'total_amount', 'order_date', 'created_at'
    ]
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = PurchaseOrder.objects.filter(
            company=self.request.active_company
        ).select_related(
            'vendor', 'vendor_contact', 'owner', 'created_by'
        ).prefetch_related('items__product')
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(order_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(order_date__lte=end_date)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PurchaseOrderListSerializer
        return PurchaseOrderSerializer
    
    @action(detail=True, methods=['post'])
    def send_order(self, request, pk=None):
        """Send purchase order to vendor"""
        order = self.get_object()
        order.status = 'sent'
        order.save()
        
        return Response({'message': 'Purchase order sent successfully'})
    
    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge purchase order"""
        order = self.get_object()
        order.status = 'acknowledged'
        order.save()
        
        return Response({'message': 'Purchase order acknowledged'})
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm purchase order"""
        order = self.get_object()
        order.status = 'confirmed'
        order.save()
        
        return Response({'message': 'Purchase order confirmed'})
    
    @action(detail=True, methods=['post'])
    def receive(self, request, pk=None):
        """Mark order as received"""
        order = self.get_object()
        order.status = 'received'
        order.actual_delivery_date = timezone.now().date()
        order.save()
        
        return Response({'message': 'Purchase order marked as received'})
    
    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """Get order items"""
        order = self.get_object()
        items = order.items.all()
        serializer = PurchaseOrderItemSerializer(items, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """Add item to order"""
        order = self.get_object()
        serializer = PurchaseOrderItemSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(order=order, company=request.active_company)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def receive_item(self, request, pk=None):
        """Receive items for an order"""
        order = self.get_object()
        item_id = request.data.get('item_id')
        received_quantity = request.data.get('received_quantity', 0)
        
        if not item_id:
            return Response(
                {'error': 'item_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            item = order.items.get(id=item_id)
            item.received_quantity += received_quantity
            item.save()
            
            # Check if all items are received
            all_received = all(item.is_fully_received for item in order.items.all())
            if all_received:
                order.status = 'received'
                order.actual_delivery_date = timezone.now().date()
                order.save()
            
            return Response({'message': 'Items received successfully'})
        except PurchaseOrderItem.DoesNotExist:
            return Response(
                {'error': 'Item not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def pending(self, request):
        """Get pending purchase orders"""
        queryset = self.get_queryset().filter(
            status__in=['sent', 'acknowledged', 'confirmed']
        )
        serializer = PurchaseOrderListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue purchase orders"""
        queryset = self.get_queryset().filter(
            status__in=['sent', 'acknowledged', 'confirmed'],
            expected_delivery_date__lt=timezone.now().date()
        )
        serializer = PurchaseOrderListSerializer(queryset, many=True)
        return Response(serializer.data)

class VendorInvoiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for VendorInvoice CRUD operations
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = [
        'status', 'vendor', 'owner', 'is_active'
    ]
    search_fields = [
        'invoice_number', 'title', 'description', 'notes'
    ]
    ordering_fields = [
        'invoice_number', 'total_amount', 'invoice_date', 'due_date', 'created_at'
    ]
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = VendorInvoice.objects.filter(
            company=self.request.active_company
        ).select_related(
            'vendor', 'purchase_order', 'owner', 'created_by'
        )
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(invoice_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(invoice_date__lte=end_date)
        
        return queryset
    
    def get_serializer_class(self):
        return VendorInvoiceSerializer
    
    @action(detail=True, methods=['post'])
    def receive_invoice(self, request, pk=None):
        """Mark invoice as received"""
        invoice = self.get_object()
        invoice.status = 'received'
        invoice.received_date = timezone.now()
        invoice.save()
        
        return Response({'message': 'Invoice marked as received'})
    
    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        """Verify invoice"""
        invoice = self.get_object()
        invoice.status = 'verified'
        invoice.save()
        
        return Response({'message': 'Invoice verified'})
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve invoice for payment"""
        invoice = self.get_object()
        invoice.status = 'approved'
        invoice.save()
        
        return Response({'message': 'Invoice approved for payment'})
    
    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """Mark invoice as paid"""
        invoice = self.get_object()
        invoice.status = 'paid'
        invoice.paid_date = timezone.now()
        invoice.save()
        
        return Response({'message': 'Invoice marked as paid'})
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue invoices"""
        queryset = self.get_queryset().filter(
            status__in=['received', 'verified', 'approved'],
            due_date__lt=timezone.now().date()
        )
        serializer = VendorInvoiceSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def due_soon(self, request):
        """Get invoices due within 7 days"""
        from datetime import timedelta
        soon = timezone.now().date() + timedelta(days=7)
        queryset = self.get_queryset().filter(
            status__in=['received', 'verified', 'approved'],
            due_date__lte=soon,
            due_date__gte=timezone.now().date()
        )
        serializer = VendorInvoiceSerializer(queryset, many=True)
        return Response(serializer.data)

class VendorPaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for VendorPayment CRUD operations
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = [
        'status', 'payment_method', 'vendor', 'is_active'
    ]
    search_fields = [
        'payment_number', 'reference_number', 'notes'
    ]
    ordering_fields = [
        'payment_number', 'amount', 'payment_date', 'created_at'
    ]
    ordering = ['-payment_date']
    
    def get_queryset(self):
        return VendorPayment.objects.filter(
            company=self.request.active_company
        ).select_related('vendor', 'invoice', 'created_by')
    
    def get_serializer_class(self):
        return VendorPaymentSerializer
    
    @action(detail=True, methods=['post'])
    def process_payment(self, request, pk=None):
        """Process payment"""
        payment = self.get_object()
        payment.status = 'processing'
        payment.save()
        
        return Response({'message': 'Payment is being processed'})
    
    @action(detail=True, methods=['post'])
    def complete_payment(self, request, pk=None):
        """Mark payment as completed"""
        payment = self.get_object()
        payment.status = 'completed'
        payment.save()
        
        # Update invoice status
        invoice = payment.invoice
        invoice.status = 'paid'
        invoice.paid_date = timezone.now()
        invoice.save()
        
        return Response({'message': 'Payment completed successfully'})
    
    @action(detail=True, methods=['post'])
    def cancel_payment(self, request, pk=None):
        """Cancel payment"""
        payment = self.get_object()
        payment.status = 'cancelled'
        payment.save()
        
        return Response({'message': 'Payment cancelled'})
