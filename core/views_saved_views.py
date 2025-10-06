# core/views_saved_views.py
# Views for Saved Views CRUD

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from core.models_saved_views import SavedListView
from core.serializers_saved_views import (
    SavedListViewSerializer,
    SavedListViewCreateSerializer,
    SavedListViewUpdateSerializer
)
from core.permissions import ActionPermission


class SavedListViewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing saved list views.
    
    Supports:
    - list: List all views for a user (private + global for their company)
    - retrieve: Get a specific view
    - create: Create a new view
    - update/partial_update: Update a view
    - destroy: Delete a view
    - apply: Apply a view to get filtered results
    """
    
    permission_classes = [IsAuthenticated, ActionPermission]
    object_type = 'savedlistview'
    
    def get_queryset(self):
        """
        Get views that the user can access.
        - All global views for their company
        - Their own private views
        """
        user = self.request.user
        company = getattr(self.request, 'company', None)
        
        if not company:
            return SavedListView.objects.none()
        
        # Filter by company and (global or owned by user)
        queryset = SavedListView.objects.filter(
            Q(company=company) &
            (Q(is_private=False) | Q(owner=user))
        )
        
        # Filter by entity_type if provided
        entity_type = self.request.query_params.get('entity_type')
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)
        
        return queryset.order_by('entity_type', 'name')
    
    def get_serializer_class(self):
        """Get appropriate serializer based on action."""
        if self.action == 'create':
            return SavedListViewCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return SavedListViewUpdateSerializer
        return SavedListViewSerializer
    
    def perform_create(self, serializer):
        """
        Create a saved view.
        Set company from request and owner if private.
        """
        company = getattr(self.request, 'company', None)
        
        extra_fields = {'company': company}
        
        # Set owner if private
        if serializer.validated_data.get('is_private', True):
            extra_fields['owner'] = self.request.user
        
        serializer.save(**extra_fields)
    
    def perform_update(self, serializer):
        """
        Update a saved view.
        Ensure user can only update their own private views or global views if admin.
        """
        instance = self.get_object()
        
        # Check ownership for private views
        if instance.is_private and instance.owner != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only update your own private views")
        
        # Check admin role for global views
        if not instance.is_private:
            from core.models import UserCompanyAccess
            try:
                access = UserCompanyAccess.objects.get(
                    user=self.request.user,
                    company=instance.company,
                    is_active=True
                )
                if access.role not in ['admin', 'manager']:
                    from rest_framework.exceptions import PermissionDenied
                    raise PermissionDenied("Only admins and managers can update global views")
            except UserCompanyAccess.DoesNotExist:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("No access to this company")
        
        serializer.save()
    
    def perform_destroy(self, instance):
        """
        Delete a saved view.
        Ensure user can only delete their own private views or global views if admin.
        """
        # Check ownership for private views
        if instance.is_private and instance.owner != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only delete your own private views")
        
        # Check admin role for global views
        if not instance.is_private:
            from core.models import UserCompanyAccess
            try:
                access = UserCompanyAccess.objects.get(
                    user=self.request.user,
                    company=instance.company,
                    is_active=True
                )
                if access.role != 'admin':
                    from rest_framework.exceptions import PermissionDenied
                    raise PermissionDenied("Only admins can delete global views")
            except UserCompanyAccess.DoesNotExist:
                from rest_framework.exceptions import PermissionDenied
                raise PermissionDenied("No access to this company")
        
        instance.delete()
    
    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """
        Apply a saved view to get filtered and sorted results.
        This is a placeholder that returns the view definition.
        The actual filtering should be done in the entity-specific endpoints.
        """
        view = self.get_object()
        
        return Response({
            'view_id': view.id,
            'name': view.name,
            'entity_type': view.entity_type,
            'definition': view.definition,
            'message': 'Apply these filters and sort in the entity list endpoint'
        })
    
    @action(detail=False, methods=['get'])
    def defaults(self, request):
        """
        Get default views for each entity type.
        """
        company = getattr(request, 'company', None)
        if not company:
            return Response({'error': 'No company context'}, status=status.HTTP_400_BAD_REQUEST)
        
        defaults = SavedListView.objects.filter(
            company=company,
            is_default=True
        ).order_by('entity_type')
        
        serializer = self.get_serializer(defaults, many=True)
        return Response(serializer.data)
