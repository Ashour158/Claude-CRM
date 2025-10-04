# deals/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Sum, Count, Avg
from django.utils import timezone
from datetime import datetime, timedelta

from deals.models import PipelineStage, Deal, DealProduct, DealActivity, DealForecast
from deals.serializers import (
    PipelineStageSerializer, PipelineStageListSerializer,
    DealSerializer, DealListSerializer, DealCreateSerializer, DealUpdateSerializer,
    DealProductSerializer, DealActivitySerializer, DealForecastSerializer,
    DealPipelineSerializer, DealStatsSerializer
)
from core.permissions import IsCompanyMember
from core.cache import cache_api_response

class PipelineStageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for PipelineStage CRUD operations
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = ['is_closed', 'is_won', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['sequence', 'name', 'probability']
    ordering = ['sequence']
    
    def get_queryset(self):
        return PipelineStage.objects.filter(
            company=self.request.active_company
        ).prefetch_related('deals')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PipelineStageListSerializer
        return PipelineStageSerializer
    
    @action(detail=False, methods=['post'])
    def reorder(self, request):
        """Reorder pipeline stages"""
        stage_ids = request.data.get('stage_ids', [])
        
        for index, stage_id in enumerate(stage_ids):
            PipelineStage.objects.filter(
                id=stage_id,
                company=request.active_company
            ).update(sequence=index + 1)
        
        return Response({'message': 'Pipeline stages reordered successfully'})
    
    @action(detail=False, methods=['get'])
    def pipeline(self, request):
        """Get pipeline with deals for kanban view"""
        stages = self.get_queryset().filter(is_active=True)
        serializer = DealPipelineSerializer(stages, many=True)
        return Response(serializer.data)

class DealViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Deal CRUD operations
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = [
        'status', 'stage', 'owner', 'territory', 'priority',
        'source', 'is_active'
    ]
    search_fields = [
        'name', 'description', 'account__name', 'contact__first_name',
        'contact__last_name', 'next_step', 'notes'
    ]
    ordering_fields = [
        'name', 'amount', 'expected_close_date', 'created_at',
        'updated_at', 'probability'
    ]
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Deal.objects.filter(
            company=self.request.active_company
        ).select_related(
            'account', 'contact', 'stage', 'owner', 'territory', 'created_by'
        ).prefetch_related(
            'products__product', 'activities', 'tags'
        )
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        # Filter by expected close date
        close_start = self.request.query_params.get('close_start_date')
        close_end = self.request.query_params.get('close_end_date')
        
        if close_start:
            queryset = queryset.filter(expected_close_date__gte=close_start)
        if close_end:
            queryset = queryset.filter(expected_close_date__lte=close_end)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return DealListSerializer
        elif self.action == 'create':
            return DealCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return DealUpdateSerializer
        return DealSerializer
    
    @action(detail=True, methods=['post'])
    def change_stage(self, request, pk=None):
        """Change deal stage"""
        deal = self.get_object()
        new_stage_id = request.data.get('stage_id')
        
        if not new_stage_id:
            return Response(
                {'error': 'stage_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            new_stage = PipelineStage.objects.get(
                id=new_stage_id,
                company=request.active_company
            )
            deal.stage = new_stage
            deal.probability = new_stage.probability
            deal.save()
            
            # Log activity
            DealActivity.objects.create(
                deal=deal,
                activity_type='other',
                subject=f'Stage changed to {new_stage.name}',
                description=f'Deal stage changed from {deal.stage.name if deal.stage else "None"} to {new_stage.name}',
                activity_date=timezone.now(),
                company=request.active_company,
                created_by=request.user
            )
            
            return Response({'message': 'Stage changed successfully'})
        except PipelineStage.DoesNotExist:
            return Response(
                {'error': 'Invalid stage'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def mark_won(self, request, pk=None):
        """Mark deal as won"""
        deal = self.get_object()
        deal.status = 'won'
        deal.actual_close_date = timezone.now().date()
        deal.save()
        
        # Log activity
        DealActivity.objects.create(
            deal=deal,
            activity_type='other',
            subject='Deal Won',
            description='Deal marked as won',
            activity_date=timezone.now(),
            company=request.active_company,
            created_by=request.user
        )
        
        return Response({'message': 'Deal marked as won'})
    
    @action(detail=True, methods=['post'])
    def mark_lost(self, request, pk=None):
        """Mark deal as lost"""
        deal = self.get_object()
        deal.status = 'lost'
        deal.actual_close_date = timezone.now().date()
        deal.save()
        
        # Log activity
        DealActivity.objects.create(
            deal=deal,
            activity_type='other',
            subject='Deal Lost',
            description='Deal marked as lost',
            activity_date=timezone.now(),
            company=request.active_company,
            created_by=request.user
        )
        
        return Response({'message': 'Deal marked as lost'})
    
    @action(detail=True, methods=['get'])
    def activities(self, request, pk=None):
        """Get deal activities"""
        deal = self.get_object()
        activities = deal.activities.all().order_by('-activity_date')
        serializer = DealActivitySerializer(activities, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def log_activity(self, request, pk=None):
        """Log activity for deal"""
        deal = self.get_object()
        serializer = DealActivitySerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(
                deal=deal,
                company=request.active_company,
                created_by=request.user
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """Get deal products"""
        deal = self.get_object()
        products = deal.products.all()
        serializer = DealProductSerializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_product(self, request, pk=None):
        """Add product to deal"""
        deal = self.get_object()
        serializer = DealProductSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(deal=deal, company=request.active_company)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def pipeline(self, request):
        """Get pipeline kanban view"""
        stages = PipelineStage.objects.filter(
            company=request.active_company,
            is_active=True
        ).order_by('sequence')
        serializer = DealPipelineSerializer(stages, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def forecast(self, request):
        """Get sales forecast"""
        # Get deals by expected close date
        deals = self.get_queryset().filter(
            status='open',
            expected_close_date__isnull=False
        )
        
        # Group by month
        monthly_forecast = {}
        for deal in deals:
            month_key = deal.expected_close_date.strftime('%Y-%m')
            if month_key not in monthly_forecast:
                monthly_forecast[month_key] = {
                    'month': month_key,
                    'deals': 0,
                    'total_value': 0,
                    'weighted_value': 0
                }
            
            monthly_forecast[month_key]['deals'] += 1
            monthly_forecast[month_key]['total_value'] += float(deal.amount or 0)
            monthly_forecast[month_key]['weighted_value'] += float(deal.expected_revenue or 0)
        
        return Response(list(monthly_forecast.values()))
    
    @action(detail=False, methods=['get'])
    @cache_api_response(timeout=300)  # Cache for 5 minutes
    def stats(self, request):
        """Get deal statistics"""
        queryset = self.get_queryset()
        
        # Basic counts
        total_deals = queryset.count()
        open_deals = queryset.filter(status='open').count()
        won_deals = queryset.filter(status='won').count()
        lost_deals = queryset.filter(status='lost').count()
        
        # Financial metrics
        total_value = queryset.aggregate(
            total=Sum('amount')
        )['total'] or 0
        
        weighted_value = queryset.aggregate(
            total=Sum('expected_revenue')
        )['total'] or 0
        
        average_deal_size = queryset.aggregate(
            avg=Avg('amount')
        )['avg'] or 0
        
        # Win rate
        closed_deals = won_deals + lost_deals
        win_rate = (won_deals / closed_deals * 100) if closed_deals > 0 else 0
        
        # Average sales cycle (days from creation to close)
        won_deals_with_dates = queryset.filter(
            status='won',
            actual_close_date__isnull=False
        )
        sales_cycles = []
        for deal in won_deals_with_dates:
            cycle_days = (deal.actual_close_date - deal.created_at.date()).days
            sales_cycles.append(cycle_days)
        
        average_sales_cycle = sum(sales_cycles) / len(sales_cycles) if sales_cycles else 0
        
        # Deals by stage
        deals_by_stage = {}
        for stage in PipelineStage.objects.filter(company=request.active_company):
            count = queryset.filter(stage=stage).count()
            deals_by_stage[stage.name] = count
        
        # Deals by owner
        deals_by_owner = {}
        for deal in queryset.select_related('owner'):
            if deal.owner:
                owner_name = deal.owner.full_name
                deals_by_owner[owner_name] = deals_by_owner.get(owner_name, 0) + 1
        
        # Deals by source
        deals_by_source = {}
        for deal in queryset:
            if deal.source:
                deals_by_source[deal.source] = deals_by_source.get(deal.source, 0) + 1
        
        # Monthly trend (last 12 months)
        monthly_trend = []
        for i in range(12):
            month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            
            month_deals = queryset.filter(
                created_at__date__range=[month_start.date(), month_end.date()]
            )
            
            monthly_trend.append({
                'month': month_start.strftime('%Y-%m'),
                'deals': month_deals.count(),
                'value': float(month_deals.aggregate(total=Sum('amount'))['total'] or 0)
            })
        
        monthly_trend.reverse()
        
        # Quarterly forecast
        quarterly_forecast = []
        for i in range(4):
            quarter_start = timezone.now().replace(day=1) + timedelta(days=30*i*3)
            quarter_end = quarter_start + timedelta(days=90)
            
            quarter_deals = queryset.filter(
                expected_close_date__range=[quarter_start.date(), quarter_end.date()],
                status='open'
            )
            
            quarterly_forecast.append({
                'quarter': f'Q{i+1}',
                'deals': quarter_deals.count(),
                'value': float(quarter_deals.aggregate(total=Sum('expected_revenue'))['total'] or 0)
            })
        
        stats_data = {
            'total_deals': total_deals,
            'open_deals': open_deals,
            'won_deals': won_deals,
            'lost_deals': lost_deals,
            'total_value': float(total_value),
            'weighted_value': float(weighted_value),
            'average_deal_size': float(average_deal_size),
            'win_rate': round(win_rate, 2),
            'average_sales_cycle': int(average_sales_cycle),
            'deals_by_stage': deals_by_stage,
            'deals_by_owner': deals_by_owner,
            'deals_by_source': deals_by_source,
            'monthly_trend': monthly_trend,
            'quarterly_forecast': quarterly_forecast
        }
        
        serializer = DealStatsSerializer(stats_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def bulk_update(self, request):
        """Bulk update deals"""
        deal_ids = request.data.get('deal_ids', [])
        updates = request.data.get('updates', {})
        
        if not deal_ids:
            return Response(
                {'error': 'deal_ids is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        deals = Deal.objects.filter(
            id__in=deal_ids,
            company=request.active_company
        )
        
        updated_count = deals.update(**updates)
        
        return Response({
            'message': f'{updated_count} deals updated successfully'
        })
    
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """Export deals to CSV"""
        import csv
        from django.http import HttpResponse
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="deals.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Name', 'Account', 'Contact', 'Stage', 'Status', 'Amount',
            'Currency', 'Probability', 'Expected Close Date', 'Owner',
            'Priority', 'Source', 'Created At'
        ])
        
        for deal in self.get_queryset():
            writer.writerow([
                deal.name,
                deal.account.name if deal.account else '',
                deal.contact.full_name if deal.contact else '',
                deal.stage.name if deal.stage else '',
                deal.status,
                deal.amount,
                deal.currency,
                deal.probability,
                deal.expected_close_date,
                deal.owner.full_name if deal.owner else '',
                deal.priority,
                deal.source,
                deal.created_at.strftime('%Y-%m-%d')
            ])
        
        return response

class DealProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for DealProduct CRUD operations
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]
    
    def get_queryset(self):
        return DealProduct.objects.filter(
            deal__company=self.request.active_company
        ).select_related('deal', 'product')
    
    def get_serializer_class(self):
        return DealProductSerializer

class DealActivityViewSet(viewsets.ModelViewSet):
    """
    ViewSet for DealActivity CRUD operations
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    
    filterset_fields = ['activity_type', 'deal']
    ordering_fields = ['activity_date', 'created_at']
    ordering = ['-activity_date']
    
    def get_queryset(self):
        return DealActivity.objects.filter(
            deal__company=self.request.active_company
        ).select_related('deal', 'created_by').prefetch_related('participants')
    
    def get_serializer_class(self):
        return DealActivitySerializer

class DealForecastViewSet(viewsets.ModelViewSet):
    """
    ViewSet for DealForecast CRUD operations
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]
    
    def get_queryset(self):
        return DealForecast.objects.filter(
            deal__company=self.request.active_company
        ).select_related('deal')
    
    def get_serializer_class(self):
        return DealForecastSerializer