# territories/views.py
# Territory Management Views

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Count, Sum
from django.shortcuts import get_object_or_404

from territories.models import Territory, TerritoryRule, TerritoryAssignment
from territories.serializers import (
    TerritorySerializer, TerritoryListSerializer, TerritoryCreateSerializer,
    TerritoryUpdateSerializer, TerritoryStatsSerializer,
    TerritoryRuleSerializer, TerritoryRuleCreateSerializer,
    TerritoryRuleUpdateSerializer
)
from core.permissions import IsCompanyMember


class TerritoryViewSet(viewsets.ModelViewSet):
    """
    Territory management with hierarchical structure
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'code', 'description']
    ordering_fields = ['name', 'code', 'created_at']
    ordering = ['name']
    filterset_fields = ['type', 'manager', 'is_active']
    
    def get_queryset(self):
        """Filter territories by active company"""
        return Territory.objects.filter(
            company=self.request.active_company
        ).select_related('manager', 'parent').prefetch_related('children')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'list':
            return TerritoryListSerializer
        elif self.action == 'create':
            return TerritoryCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return TerritoryUpdateSerializer
        elif self.action == 'stats':
            return TerritoryStatsSerializer
        return TerritorySerializer
    
    def perform_create(self, serializer):
        """Set company and created_by from request context"""
        serializer.save(
            company=self.request.active_company,
            created_by=self.request.user
        )
    
    def perform_update(self, serializer):
        """Set updated_by from request context"""
        serializer.save(updated_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        """Get child territories"""
        territory = self.get_object()
        children = territory.children.all()
        serializer = TerritoryListSerializer(children, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def users(self, request, pk=None):
        """Get users assigned to this territory"""
        territory = self.get_object()
        users = territory.get_all_users()
        from core.serializers.auth import UserSerializer
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def accounts(self, request, pk=None):
        """Get accounts in this territory"""
        territory = self.get_object()
        accounts = territory.accounts.all()
        from crm.serializers.accounts import AccountListSerializer
        serializer = AccountListSerializer(accounts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def leads(self, request, pk=None):
        """Get leads in this territory"""
        territory = self.get_object()
        leads = territory.leads.all()
        from crm.serializers.leads import LeadListSerializer
        serializer = LeadListSerializer(leads, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def deals(self, request, pk=None):
        """Get deals in this territory"""
        territory = self.get_object()
        deals = territory.deals.all()
        from deals.serializers import DealListSerializer
        serializer = DealListSerializer(deals, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get territory statistics"""
        territories = self.get_queryset()
        
        stats = {
            'total_territories': territories.count(),
            'active_territories': territories.filter(is_active=True).count(),
            'territories_by_type': {},
            'total_users': 0,
            'total_accounts': 0,
            'total_leads': 0,
            'total_deals': 0,
            'total_deal_value': 0,
        }
        
        # Territory type breakdown
        for territory_type, _ in Territory.TYPE_CHOICES:
            count = territories.filter(type=territory_type).count()
            stats['territories_by_type'][territory_type] = count
        
        # Aggregate data
        for territory in territories:
            users = territory.get_all_users()
            stats['total_users'] += users.count()
            stats['total_accounts'] += territory.accounts.count()
            stats['total_leads'] += territory.leads.count()
            stats['total_deals'] += territory.deals.count()
            stats['total_deal_value'] += territory.deals.aggregate(
                total=Sum('amount')
            )['total'] or 0
        
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def assign_user(self, request, pk=None):
        """Assign user to territory"""
        territory = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from core.models import UserCompanyAccess
            user_access = UserCompanyAccess.objects.get(
                user_id=user_id,
                company=self.request.active_company
            )
            user_access.territory = territory
            user_access.save()
            
            return Response({'message': 'User assigned to territory'})
        except UserCompanyAccess.DoesNotExist:
            return Response(
                {'error': 'User not found in company'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def remove_user(self, request, pk=None):
        """Remove user from territory"""
        territory = self.get_object()
        user_id = request.data.get('user_id')
        
        if not user_id:
            return Response(
                {'error': 'user_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from core.models import UserCompanyAccess
            user_access = UserCompanyAccess.objects.get(
                user_id=user_id,
                company=self.request.active_company
            )
            user_access.territory = None
            user_access.save()
            
            return Response({'message': 'User removed from territory'})
        except UserCompanyAccess.DoesNotExist:
            return Response(
                {'error': 'User not found in company'},
                status=status.HTTP_404_NOT_FOUND
            )


class TerritoryRuleViewSet(viewsets.ModelViewSet):
    """
    Territory assignment rules
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'priority', 'created_at']
    ordering = ['-priority', 'name']
    filterset_fields = ['territory', 'is_active']
    
    def get_queryset(self):
        """Filter rules by active company"""
        return TerritoryRule.objects.filter(
            company=self.request.active_company
        ).select_related('territory')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return TerritoryRuleCreateSerializer
        elif self.action == 'update' or self.action == 'partial_update':
            return TerritoryRuleUpdateSerializer
        return TerritoryRuleSerializer
    
    def perform_create(self, serializer):
        """Set company and created_by from request context"""
        serializer.save(
            company=self.request.active_company,
            created_by=self.request.user
        )
    
    def perform_update(self, serializer):
        """Set updated_by from request context"""
        serializer.save(updated_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def test_rule(self, request, pk=None):
        """Test rule against sample data"""
        rule = self.get_object()
        test_data = request.data.get('test_data', {})
        
        try:
            result = rule.evaluate_conditions(test_data)
            return Response({
                'rule_id': rule.id,
                'rule_name': rule.name,
                'matches': result,
                'test_data': test_data
            })
        except Exception as e:
            return Response(
                {'error': f'Rule evaluation failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def apply_rule(self, request, pk=None):
        """Apply rule to existing entities"""
        rule = self.get_object()
        entity_type = request.data.get('entity_type')
        entity_ids = request.data.get('entity_ids', [])
        
        if not entity_type or not entity_ids:
            return Response(
                {'error': 'entity_type and entity_ids are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            applied_count = 0
            for entity_id in entity_ids:
                # Get entity based on type
                if entity_type == 'lead':
                    from crm.models import Lead
                    entity = Lead.objects.get(id=entity_id, company=self.request.active_company)
                elif entity_type == 'account':
                    from crm.models import Account
                    entity = Account.objects.get(id=entity_id, company=self.request.active_company)
                else:
                    continue
                
                # Apply rule
                rule.apply_rule(entity, entity_type)
                applied_count += 1
            
            return Response({
                'message': f'Rule applied to {applied_count} entities',
                'applied_count': applied_count
            })
        except Exception as e:
            return Response(
                {'error': f'Rule application failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
