# sales/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta

from sales.models import (
    Quote, QuoteItem, SalesOrder, SalesOrderItem,
    Invoice, InvoiceItem, Payment
)
from sales.serializers import (
    QuoteSerializer, QuoteListSerializer, QuoteItemSerializer,
    SalesOrderSerializer, SalesOrderListSerializer, SalesOrderItemSerializer,
    InvoiceSerializer, InvoiceListSerializer, InvoiceItemSerializer,
    PaymentSerializer, SalesStatsSerializer, SalesPipelineSerializer
)
from core.permissions import IsCompanyMember
from core.cache import cache_api_response

class QuoteViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Quote CRUD operations
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = [
        'status', 'account', 'contact', 'owner', 'is_active'
    ]
    search_fields = [
        'quote_number', 'title', 'description', 'notes'
    ]
    ordering_fields = [
        'quote_number', 'total_amount', 'valid_until', 'created_at'
    ]
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Quote.objects.filter(
            company=self.request.active_company
        ).select_related(
            'account', 'contact', 'deal', 'owner', 'created_by'
        ).prefetch_related('items__product')
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return QuoteListSerializer
        return QuoteSerializer
    
    @action(detail=True, methods=['post'])
    def send_quote(self, request, pk=None):
        """Send quote to customer"""
        quote = self.get_object()
        quote.status = 'sent'
        quote.sent_date = timezone.now()
        quote.save()
        
        return Response({'message': 'Quote sent successfully'})
    
    @action(detail=True, methods=['post'])
    def mark_viewed(self, request, pk=None):
        """Mark quote as viewed"""
        quote = self.get_object()
        quote.status = 'viewed'
        quote.viewed_date = timezone.now()
        quote.save()
        
        return Response({'message': 'Quote marked as viewed'})
    
    @action(detail=True, methods=['post'])
    def accept_quote(self, request, pk=None):
        """Accept quote"""
        quote = self.get_object()
        quote.status = 'accepted'
        quote.accepted_date = timezone.now()
        quote.save()
        
        return Response({'message': 'Quote accepted successfully'})
    
    @action(detail=True, methods=['post'])
    def reject_quote(self, request, pk=None):
        """Reject quote"""
        quote = self.get_object()
        quote.status = 'rejected'
        quote.save()
        
        return Response({'message': 'Quote rejected'})
    
    @action(detail=True, methods=['post'])
    def convert_to_order(self, request, pk=None):
        """Convert quote to sales order"""
        quote = self.get_object()
        
        if quote.status != 'accepted':
            return Response(
                {'error': 'Only accepted quotes can be converted to orders'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create sales order
        order = SalesOrder.objects.create(
            account=quote.account,
            contact=quote.contact,
            deal=quote.deal,
            title=f"Order from {quote.quote_number}",
            description=quote.description,
            order_date=timezone.now().date(),
            subtotal=quote.subtotal,
            tax_rate=quote.tax_rate,
            tax_amount=quote.tax_amount,
            discount_percentage=quote.discount_percentage,
            discount_amount=quote.discount_amount,
            total_amount=quote.total_amount,
            currency=quote.currency,
            owner=quote.owner,
            terms_conditions=quote.terms_conditions,
            notes=quote.notes,
            company=request.active_company,
            created_by=request.user
        )
        
        # Copy quote items to order items
        for quote_item in quote.items.all():
            SalesOrderItem.objects.create(
                order=order,
                product=quote_item.product,
                description=quote_item.description,
                quantity=quote_item.quantity,
                unit_price=quote_item.unit_price,
                discount_percentage=quote_item.discount_percentage,
                discount_amount=quote_item.discount_amount,
                total_price=quote_item.total_price,
                company=request.active_company
            )
        
        # Update quote status
        quote.status = 'converted'
        quote.save()
        
        return Response({
            'message': 'Quote converted to sales order successfully',
            'order_id': order.id,
            'order_number': order.order_number
        })
    
    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """Get quote items"""
        quote = self.get_object()
        items = quote.items.all()
        serializer = QuoteItemSerializer(items, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """Add item to quote"""
        quote = self.get_object()
        serializer = QuoteItemSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(quote=quote, company=request.active_company)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def expired(self, request):
        """Get expired quotes"""
        queryset = self.get_queryset().filter(
            status__in=['sent', 'viewed'],
            valid_until__lt=timezone.now().date()
        )
        serializer = QuoteListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def expiring_soon(self, request):
        """Get quotes expiring within 7 days"""
        from datetime import timedelta
        soon = timezone.now().date() + timedelta(days=7)
        queryset = self.get_queryset().filter(
            status__in=['sent', 'viewed'],
            valid_until__lte=soon,
            valid_until__gte=timezone.now().date()
        )
        serializer = QuoteListSerializer(queryset, many=True)
        return Response(serializer.data)

class SalesOrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for SalesOrder CRUD operations
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = [
        'status', 'account', 'contact', 'owner', 'is_active'
    ]
    search_fields = [
        'order_number', 'title', 'description', 'tracking_number', 'notes'
    ]
    ordering_fields = [
        'order_number', 'total_amount', 'order_date', 'created_at'
    ]
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = SalesOrder.objects.filter(
            company=self.request.active_company
        ).select_related(
            'account', 'contact', 'quote', 'deal', 'owner', 'created_by'
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
            return SalesOrderListSerializer
        return SalesOrderSerializer
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirm order"""
        order = self.get_object()
        order.status = 'confirmed'
        order.save()
        
        return Response({'message': 'Order confirmed successfully'})
    
    @action(detail=True, methods=['post'])
    def ship(self, request, pk=None):
        """Mark order as shipped"""
        order = self.get_object()
        tracking_number = request.data.get('tracking_number', '')
        shipping_method = request.data.get('shipping_method', '')
        
        order.status = 'shipped'
        order.tracking_number = tracking_number
        order.shipping_method = shipping_method
        order.save()
        
        return Response({'message': 'Order marked as shipped'})
    
    @action(detail=True, methods=['post'])
    def deliver(self, request, pk=None):
        """Mark order as delivered"""
        order = self.get_object()
        order.status = 'delivered'
        order.actual_delivery_date = timezone.now().date()
        order.save()
        
        return Response({'message': 'Order marked as delivered'})
    
    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """Get order items"""
        order = self.get_object()
        items = order.items.all()
        serializer = SalesOrderItemSerializer(items, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """Add item to order"""
        order = self.get_object()
        serializer = SalesOrderItemSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(order=order, company=request.active_company)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def create_invoice(self, request, pk=None):
        """Create invoice from order"""
        order = self.get_object()
        
        if order.status not in ['confirmed', 'processing', 'shipped', 'delivered']:
            return Response(
                {'error': 'Only confirmed or processed orders can be invoiced'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create invoice
        invoice = Invoice.objects.create(
            account=order.account,
            contact=order.contact,
            deal=order.deal,
            sales_order=order,
            title=f"Invoice for {order.order_number}",
            description=order.description,
            invoice_date=timezone.now().date(),
            due_date=timezone.now().date() + timedelta(days=30),  # 30 days payment terms
            subtotal=order.subtotal,
            tax_rate=order.tax_rate,
            tax_amount=order.tax_amount,
            discount_percentage=order.discount_percentage,
            discount_amount=order.discount_amount,
            total_amount=order.total_amount,
            currency=order.currency,
            owner=order.owner,
            terms_conditions=order.terms_conditions,
            notes=order.notes,
            company=request.active_company,
            created_by=request.user
        )
        
        # Copy order items to invoice items
        for order_item in order.items.all():
            InvoiceItem.objects.create(
                invoice=invoice,
                product=order_item.product,
                description=order_item.description,
                quantity=order_item.quantity,
                unit_price=order_item.unit_price,
                discount_percentage=order_item.discount_percentage,
                discount_amount=order_item.discount_amount,
                total_price=order_item.total_price,
                company=request.active_company
            )
        
        return Response({
            'message': 'Invoice created successfully',
            'invoice_id': invoice.id,
            'invoice_number': invoice.invoice_number
        })

class InvoiceViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Invoice CRUD operations
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = [
        'status', 'account', 'contact', 'owner', 'is_active'
    ]
    search_fields = [
        'invoice_number', 'title', 'description', 'notes'
    ]
    ordering_fields = [
        'invoice_number', 'total_amount', 'invoice_date', 'due_date', 'created_at'
    ]
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Invoice.objects.filter(
            company=self.request.active_company
        ).select_related(
            'account', 'contact', 'sales_order', 'deal', 'owner', 'created_by'
        ).prefetch_related('items__product', 'payments')
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(invoice_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(invoice_date__lte=end_date)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return InvoiceListSerializer
        return InvoiceSerializer
    
    @action(detail=True, methods=['post'])
    def send_invoice(self, request, pk=None):
        """Send invoice to customer"""
        invoice = self.get_object()
        invoice.status = 'sent'
        invoice.sent_date = timezone.now()
        invoice.save()
        
        return Response({'message': 'Invoice sent successfully'})
    
    @action(detail=True, methods=['post'])
    def mark_viewed(self, request, pk=None):
        """Mark invoice as viewed"""
        invoice = self.get_object()
        invoice.status = 'viewed'
        invoice.viewed_date = timezone.now()
        invoice.save()
        
        return Response({'message': 'Invoice marked as viewed'})
    
    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        """Mark invoice as paid"""
        invoice = self.get_object()
        invoice.status = 'paid'
        invoice.paid_date = timezone.now()
        invoice.paid_amount = invoice.total_amount
        invoice.balance_amount = 0
        invoice.save()
        
        return Response({'message': 'Invoice marked as paid'})
    
    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """Get invoice items"""
        invoice = self.get_object()
        items = invoice.items.all()
        serializer = InvoiceItemSerializer(items, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """Add item to invoice"""
        invoice = self.get_object()
        serializer = InvoiceItemSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(invoice=invoice, company=request.active_company)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def payments(self, request, pk=None):
        """Get invoice payments"""
        invoice = self.get_object()
        payments = invoice.payments.all().order_by('-payment_date')
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_payment(self, request, pk=None):
        """Add payment to invoice"""
        invoice = self.get_object()
        serializer = PaymentSerializer(data=request.data)
        
        if serializer.is_valid():
            payment = serializer.save(
                invoice=invoice,
                account=invoice.account,
                company=request.active_company
            )
            
            # Update invoice paid amount
            invoice.paid_amount += payment.amount
            invoice.balance_amount = invoice.total_amount - invoice.paid_amount
            
            if invoice.balance_amount <= 0:
                invoice.status = 'paid'
                invoice.paid_date = timezone.now()
            
            invoice.save()
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def overdue(self, request):
        """Get overdue invoices"""
        queryset = self.get_queryset().filter(
            status__in=['sent', 'viewed'],
            due_date__lt=timezone.now().date()
        )
        serializer = InvoiceListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def due_soon(self, request):
        """Get invoices due within 7 days"""
        from datetime import timedelta
        soon = timezone.now().date() + timedelta(days=7)
        queryset = self.get_queryset().filter(
            status__in=['sent', 'viewed'],
            due_date__lte=soon,
            due_date__gte=timezone.now().date()
        )
        serializer = InvoiceListSerializer(queryset, many=True)
        return Response(serializer.data)

class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Payment CRUD operations
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = [
        'status', 'payment_method', 'invoice', 'account', 'is_active'
    ]
    search_fields = [
        'payment_number', 'reference_number', 'notes'
    ]
    ordering_fields = [
        'payment_number', 'amount', 'payment_date', 'created_at'
    ]
    ordering = ['-payment_date']
    
    def get_queryset(self):
        return Payment.objects.filter(
            company=self.request.active_company
        ).select_related('invoice', 'account', 'created_by')
    
    def get_serializer_class(self):
        return PaymentSerializer
    
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
        
        # Update invoice
        invoice = payment.invoice
        invoice.paid_amount += payment.amount
        invoice.balance_amount = invoice.total_amount - invoice.paid_amount
        
        if invoice.balance_amount <= 0:
            invoice.status = 'paid'
            invoice.paid_date = timezone.now()
        
        invoice.save()
        
        return Response({'message': 'Payment completed successfully'})
    
    @action(detail=True, methods=['post'])
    def refund_payment(self, request, pk=None):
        """Refund payment"""
        payment = self.get_object()
        payment.status = 'refunded'
        payment.save()
        
        # Update invoice
        invoice = payment.invoice
        invoice.paid_amount -= payment.amount
        invoice.balance_amount = invoice.total_amount - invoice.paid_amount
        invoice.status = 'sent'  # Reset to sent status
        invoice.save()
        
        return Response({'message': 'Payment refunded successfully'})

class SalesStatsViewSet(viewsets.ViewSet):
    """
    ViewSet for sales statistics
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]
    
    @action(detail=False, methods=['get'])
    @cache_api_response(timeout=300)
    def stats(self, request):
        """Get comprehensive sales statistics"""
        company = request.active_company
        
        # Basic counts
        total_quotes = Quote.objects.filter(company=company).count()
        total_orders = SalesOrder.objects.filter(company=company).count()
        total_invoices = Invoice.objects.filter(company=company).count()
        total_payments = Payment.objects.filter(company=company).count()
        
        # Financial metrics
        total_revenue = Payment.objects.filter(
            company=company,
            status='completed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        outstanding_amount = Invoice.objects.filter(
            company=company,
            status__in=['sent', 'viewed']
        ).aggregate(total=Sum('balance_amount'))['total'] or 0
        
        # Status breakdowns
        quotes_by_status = {}
        for status_choice, _ in Quote.QUOTE_STATUS_CHOICES:
            count = Quote.objects.filter(company=company, status=status_choice).count()
            quotes_by_status[status_choice] = count
        
        orders_by_status = {}
        for status_choice, _ in SalesOrder.ORDER_STATUS_CHOICES:
            count = SalesOrder.objects.filter(company=company, status=status_choice).count()
            orders_by_status[status_choice] = count
        
        invoices_by_status = {}
        for status_choice, _ in Invoice.INVOICE_STATUS_CHOICES:
            count = Invoice.objects.filter(company=company, status=status_choice).count()
            invoices_by_status[status_choice] = count
        
        payments_by_method = {}
        for method_choice, _ in Payment.PAYMENT_METHODS:
            count = Payment.objects.filter(company=company, payment_method=method_choice).count()
            payments_by_method[method_choice] = count
        
        # Monthly revenue trend
        monthly_revenue = []
        for i in range(12):
            month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            
            month_payments = Payment.objects.filter(
                company=company,
                status='completed',
                payment_date__date__range=[month_start.date(), month_end.date()]
            )
            
            monthly_revenue.append({
                'month': month_start.strftime('%Y-%m'),
                'revenue': float(month_payments.aggregate(total=Sum('amount'))['total'] or 0)
            })
        
        monthly_revenue.reverse()
        
        # Top customers by revenue
        top_customers = []
        customer_revenue = Payment.objects.filter(
            company=company,
            status='completed'
        ).values('account__name').annotate(
            total_revenue=Sum('amount')
        ).order_by('-total_revenue')[:10]
        
        for customer in customer_revenue:
            top_customers.append({
                'account_name': customer['account__name'],
                'total_revenue': float(customer['total_revenue'])
            })
        
        # Conversion rate (quotes to orders)
        accepted_quotes = Quote.objects.filter(company=company, status='accepted').count()
        conversion_rate = (accepted_quotes / total_quotes * 100) if total_quotes > 0 else 0
        
        stats_data = {
            'total_quotes': total_quotes,
            'total_orders': total_orders,
            'total_invoices': total_invoices,
            'total_payments': total_payments,
            'total_revenue': float(total_revenue),
            'outstanding_amount': float(outstanding_amount),
            'quotes_by_status': quotes_by_status,
            'orders_by_status': orders_by_status,
            'invoices_by_status': invoices_by_status,
            'payments_by_method': payments_by_method,
            'monthly_revenue': monthly_revenue,
            'top_customers': top_customers,
            'conversion_rate': round(conversion_rate, 2)
        }
        
        serializer = SalesStatsSerializer(stats_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def pipeline(self, request):
        """Get sales pipeline data"""
        company = request.active_company
        
        # Get recent quotes, orders, and invoices
        quotes = Quote.objects.filter(
            company=company,
            status__in=['sent', 'viewed', 'accepted']
        ).order_by('-created_at')[:20]
        
        orders = SalesOrder.objects.filter(
            company=company,
            status__in=['pending', 'confirmed', 'processing']
        ).order_by('-created_at')[:20]
        
        invoices = Invoice.objects.filter(
            company=company,
            status__in=['sent', 'viewed']
        ).order_by('-created_at')[:20]
        
        # Calculate total pipeline value
        total_pipeline_value = (
            quotes.aggregate(total=Sum('total_amount'))['total'] or 0 +
            orders.aggregate(total=Sum('total_amount'))['total'] or 0 +
            invoices.aggregate(total=Sum('total_amount'))['total'] or 0
        )
        
        # Conversion funnel
        conversion_funnel = {
            'quotes': quotes.count(),
            'accepted_quotes': quotes.filter(status='accepted').count(),
            'orders': orders.count(),
            'invoices': invoices.count(),
            'paid_invoices': Invoice.objects.filter(company=company, status='paid').count()
        }
        
        pipeline_data = {
            'quotes': QuoteListSerializer(quotes, many=True).data,
            'orders': SalesOrderListSerializer(orders, many=True).data,
            'invoices': InvoiceListSerializer(invoices, many=True).data,
            'total_pipeline_value': float(total_pipeline_value),
            'conversion_funnel': conversion_funnel
        }
        
        serializer = SalesPipelineSerializer(pipeline_data)
        return Response(serializer.data)
