# sharing/views.py
# Views for sharing administration

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import SharingRule, RecordShare
from .serializers import SharingRuleSerializer, RecordShareSerializer


class SharingRuleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing sharing rules.
    
    Provides CRUD operations for SharingRule model.
    Rules are automatically scoped to the user's active company.
    """
    
    serializer_class = SharingRuleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['object_type', 'is_active', 'access_level']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter rules by active company"""
        if not hasattr(self.request, 'active_company'):
            return SharingRule.objects.none()
        
        return SharingRule.objects.filter(
            company=self.request.active_company
        ).select_related('created_by')
    
    def perform_create(self, serializer):
        """Set company and created_by on creation"""
        serializer.save(
            company=self.request.active_company,
            created_by=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a sharing rule"""
        rule = self.get_object()
        rule.is_active = True
        rule.save()
        return Response({'status': 'Rule activated'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate a sharing rule"""
        rule = self.get_object()
        rule.is_active = False
        rule.save()
        return Response({'status': 'Rule deactivated'})


class RecordShareViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing explicit record shares.
    
    Provides CRUD operations for RecordShare model.
    Shares are automatically scoped to the user's active company.
    """
    
    serializer_class = RecordShareSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['object_type', 'object_id', 'user', 'access_level']
    search_fields = ['reason']
    ordering_fields = ['created_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Filter shares by active company"""
        if not hasattr(self.request, 'active_company'):
            return RecordShare.objects.none()
        
        return RecordShare.objects.filter(
            company=self.request.active_company
        ).select_related('user', 'created_by')
    
    def perform_create(self, serializer):
        """Set company and created_by on creation"""
        serializer.save(
            company=self.request.active_company,
            created_by=self.request.user
        )
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """
        Bulk create record shares.
        
        Expected payload:
        {
            "shares": [
                {
                    "object_type": "lead",
                    "object_id": "uuid",
                    "user": "user_id",
                    "access_level": "read_only",
                    "reason": "optional"
                },
                ...
            ]
        }
        """
        shares_data = request.data.get('shares', [])
        
        if not shares_data:
            return Response(
                {'error': 'No shares provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_shares = []
        errors = []
        
        for share_data in shares_data:
            share_data['company'] = self.request.active_company.id
            serializer = self.get_serializer(data=share_data)
            
            if serializer.is_valid():
                self.perform_create(serializer)
                created_shares.append(serializer.data)
            else:
                errors.append({
                    'data': share_data,
                    'errors': serializer.errors
                })
        
        return Response({
            'created': len(created_shares),
            'shares': created_shares,
            'errors': errors
        }, status=status.HTTP_201_CREATED if created_shares else status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['delete'])
    def bulk_delete(self, request):
        """
        Bulk delete record shares.
        
        Expected payload:
        {
            "share_ids": ["uuid1", "uuid2", ...]
        }
        """
        share_ids = request.data.get('share_ids', [])
        
        if not share_ids:
            return Response(
                {'error': 'No share IDs provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        deleted_count = self.get_queryset().filter(id__in=share_ids).delete()[0]
        
        return Response({
            'deleted': deleted_count
        }, status=status.HTTP_200_OK)
