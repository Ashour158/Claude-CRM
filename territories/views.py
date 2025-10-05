# territories/views.py
# Territories Views

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Territory
from .serializers import TerritorySerializer

class TerritoryViewSet(viewsets.ModelViewSet):
    queryset = Territory.objects.all()
    serializer_class = TerritorySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    filterset_fields = ['is_active']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
        territory = self.get_object()
        children = territory.children.all()
        serializer = self.get_serializer(children, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def assign_accounts(self, request, pk=None):
        territory = self.get_object()
        account_ids = request.data.get('account_ids', [])
        # Territory assignment logic
        return Response({'message': 'Accounts assigned to territory'})

    @action(detail=True, methods=['post'])
    def assign_leads(self, request, pk=None):
        territory = self.get_object()
        lead_ids = request.data.get('lead_ids', [])
        # Territory assignment logic
        return Response({'message': 'Leads assigned to territory'})