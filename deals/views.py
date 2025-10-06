# deals/views.py
# Deals Views

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db import transaction
from django.db.models import Prefetch
from .models import Deal, Pipeline, PipelineStage
from .serializers import DealSerializer
from core.permissions import ActionPermission


class DealViewSet(viewsets.ModelViewSet):
    queryset = Deal.objects.all()
    serializer_class = DealSerializer
    permission_classes = [IsAuthenticated, ActionPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    filterset_fields = ['stage', 'status', 'owner']
    ordering_fields = ['amount', 'expected_close_date', 'created_at']
    ordering = ['-created_at']
    object_type = 'deal'

    def get_queryset(self):
        """Filter by company."""
        queryset = super().get_queryset()
        company = getattr(self.request, 'company', None)
        if company:
            queryset = queryset.filter(company=company)
        return queryset

    @action(detail=True, methods=['post'])
    def change_stage(self, request, pk=None):
        deal = self.get_object()
        new_stage = request.data.get('stage')
        if new_stage:
            deal.stage = new_stage
            deal.save()
            
            # Create timeline event
            self._create_stage_change_event(deal, new_stage)
            
            return Response({'message': 'Stage updated', 'stage': new_stage})
        return Response({'error': 'Stage required'}, status=400)

    @action(detail=True, methods=['post'])
    def mark_won(self, request, pk=None):
        deal = self.get_object()
        deal.status = 'won'
        deal.save()
        return Response({'message': 'Deal marked as won'})

    @action(detail=True, methods=['post'])
    def mark_lost(self, request, pk=None):
        deal = self.get_object()
        deal.status = 'lost'
        deal.save()
        return Response({'message': 'Deal marked as lost'})

    @action(detail=True, methods=['get'])
    def activities(self, request, pk=None):
        deal = self.get_object()
        activities = deal.activities.all()
        return Response({'activities': []})  # Placeholder

    @action(detail=False, methods=['get'])
    def pipeline(self, request):
        # Legacy: Kanban view data
        deals = self.get_queryset()
        serializer = self.get_serializer(deals, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def board(self, request):
        """
        Get deals organized by pipeline stages for kanban board view.
        Returns stages with minimal hydrated deal cards.
        """
        company = getattr(request, 'company', None)
        if not company:
            return Response(
                {'error': 'No company context'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get pipeline (default or specified)
        pipeline_id = request.query_params.get('pipeline_id')
        
        if pipeline_id:
            try:
                pipeline = Pipeline.objects.get(id=pipeline_id, company=company)
            except Pipeline.DoesNotExist:
                return Response(
                    {'error': 'Pipeline not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Get default pipeline
            pipeline = Pipeline.objects.filter(
                company=company,
                is_default=True,
                is_active=True
            ).first()
            
            if not pipeline:
                # Get any active pipeline
                pipeline = Pipeline.objects.filter(
                    company=company,
                    is_active=True
                ).first()
        
        if not pipeline:
            return Response({
                'pipeline': None,
                'stages': [],
                'message': 'No pipeline configured'
            })
        
        # Get stages with deals
        stages = PipelineStage.objects.filter(
            pipeline=pipeline,
            is_active=True
        ).prefetch_related(
            Prefetch(
                'pipeline_stages_set',  # Reverse relation name
                queryset=Deal.objects.filter(
                    company=company,
                    status='open'
                ).select_related('account', 'owner'),
                to_attr='deals'
            )
        ).order_by('sequence')
        
        # Build response
        stage_data = []
        for stage in stages:
            # Get deals for this stage (matching stage name for now)
            stage_deals = Deal.objects.filter(
                company=company,
                stage=stage.name.lower().replace(' ', '_'),
                status='open'
            ).select_related('account', 'owner')[:20]  # Limit for performance
            
            deals_data = []
            for deal in stage_deals:
                deals_data.append({
                    'id': deal.id,
                    'name': deal.name,
                    'amount': str(deal.amount) if deal.amount else None,
                    'account': deal.account.name if deal.account else None,
                    'owner': deal.owner.get_full_name() if deal.owner else None,
                    'expected_close_date': deal.expected_close_date,
                })
            
            stage_data.append({
                'id': stage.id,
                'name': stage.name,
                'sequence': stage.sequence,
                'probability': stage.probability,
                'wip_limit': stage.wip_limit,
                'deal_count': len(deals_data),
                'deals': deals_data,
            })
        
        return Response({
            'pipeline': {
                'id': pipeline.id,
                'name': pipeline.name,
            },
            'stages': stage_data
        })

    @action(detail=False, methods=['post'])
    def move(self, request):
        """
        Move a deal to a different stage with position control.
        
        Request body:
        {
            "deal_id": <id>,
            "to_stage_id": <id>,
            "position": <int>  # Optional
        }
        """
        deal_id = request.data.get('deal_id')
        to_stage_id = request.data.get('to_stage_id')
        position = request.data.get('position', 0)
        
        if not deal_id or not to_stage_id:
            return Response(
                {'error': 'deal_id and to_stage_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        company = getattr(request, 'company', None)
        
        try:
            with transaction.atomic():
                # Get deal with lock
                deal = Deal.objects.select_for_update().get(
                    id=deal_id,
                    company=company
                )
                
                # Get target stage
                stage = PipelineStage.objects.get(
                    id=to_stage_id,
                    company=company
                )
                
                old_stage = deal.stage
                
                # Check WIP limit if configured
                if stage.wip_limit:
                    current_count = Deal.objects.filter(
                        company=company,
                        stage=stage.name.lower().replace(' ', '_'),
                        status='open'
                    ).count()
                    
                    if current_count >= stage.wip_limit:
                        return Response({
                            'warning': f'Stage WIP limit ({stage.wip_limit}) reached',
                            'current_count': current_count,
                            'can_proceed': False
                        }, status=status.HTTP_200_OK)
                
                # Update deal stage
                deal.stage = stage.name.lower().replace(' ', '_')
                deal.probability = stage.probability
                
                # Update status if closed stage
                if stage.is_closed:
                    deal.status = 'won' if stage.is_won else 'lost'
                
                deal.save()
                
                # Create timeline event
                self._create_stage_change_event(deal, deal.stage, old_stage)
        
        except Deal.DoesNotExist:
            return Response(
                {'error': 'Deal not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except PipelineStage.DoesNotExist:
            return Response(
                {'error': 'Stage not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({
            'message': 'Deal moved successfully',
            'deal_id': deal.id,
            'new_stage': deal.stage,
            'new_probability': deal.probability,
        })

    @action(detail=False, methods=['get'])
    def forecast(self, request):
        # Sales forecast data
        return Response({'forecast': []})  # Placeholder
    
    def _create_stage_change_event(self, deal, new_stage, old_stage=None):
        """
        Create a timeline event for stage change.
        This is a placeholder for future timeline integration.
        """
        # TODO: Integrate with timeline/activity system
        pass
