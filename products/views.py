# products/views.py
# Products Views

from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from .models import Product, ProductCategory, PriceList
from .serializers import ProductSerializer, ProductCategorySerializer, PriceListSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description', 'sku']
    filterset_fields = ['category', 'is_active']
    ordering_fields = ['name', 'price', 'created_at']
    ordering = ['name']

    @action(detail=False, methods=['post'])
    def import_csv(self, request):
        return Response({'message': 'Import functionality not implemented yet'})

    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        return Response({'message': 'Export functionality not implemented yet'})

class ProductCategoryViewSet(viewsets.ModelViewSet):
    queryset = ProductCategory.objects.all()
    serializer_class = ProductCategorySerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

class PriceListViewSet(viewsets.ModelViewSet):
    queryset = PriceList.objects.all()
    serializer_class = PriceListSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name', 'description']
    filterset_fields = ['is_active']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        price_list = self.get_object()
        items = price_list.items.all()
        return Response({'items': []})  # Placeholder