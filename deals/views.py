# deals/views.py
# Deals Views

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Deal
from .serializers import DealSerializer

class DealViewSet(viewsets.ModelViewSet):
    queryset = Deal.objects.all()
    serializer_class = DealSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    filterset_fields = ['stage', 'status', 'owner']
    ordering_fields = ['amount', 'expected_close_date', 'created_at']
    ordering = ['-created_at']

    @action(detail=True, methods=['post'])
    def change_stage(self, request, pk=None):
        deal = self.get_object()
        new_stage = request.data.get('stage')
        if new_stage:
            deal.stage = new_stage
            deal.save()
            return Response({'message': 'Stage updated'})
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
        # Kanban view data
        deals = self.get_queryset()
        serializer = self.get_serializer(deals, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def forecast(self, request):
        # Sales forecast data
        return Response({'forecast': []})  # Placeholder