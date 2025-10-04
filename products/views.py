# products/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Sum, Count, Avg, F
from django.utils import timezone
from datetime import datetime, timedelta

from products.models import (
    ProductCategory, Product, ProductVariant, PriceList,
    PriceListItem, InventoryTransaction, ProductReview,
    ProductBundle, BundleItem
)
from products.serializers import (
    ProductCategorySerializer, ProductCategoryListSerializer,
    ProductSerializer, ProductListSerializer, ProductVariantSerializer,
    PriceListSerializer, PriceListItemSerializer,
    InventoryTransactionSerializer, ProductReviewSerializer,
    ProductBundleSerializer, BundleItemSerializer,
    ProductStatsSerializer, ProductSearchSerializer
)
from core.permissions import IsCompanyMember
from core.cache import cache_api_response

class ProductCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ProductCategory CRUD operations
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = ['parent', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        return ProductCategory.objects.filter(
            company=self.request.active_company
        ).prefetch_related('children', 'products')
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProductCategoryListSerializer
        return ProductCategorySerializer
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """Get category tree structure"""
        categories = self.get_queryset().filter(parent__isnull=True)
        serializer = ProductCategorySerializer(categories, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """Get products in this category"""
        category = self.get_object()
        products = category.products.filter(is_active=True)
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)

class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Product CRUD operations
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = [
        'category', 'product_type', 'status', 'owner',
        'is_featured', 'is_digital', 'is_active'
    ]
    search_fields = [
        'name', 'sku', 'description', 'short_description',
        'meta_title', 'meta_description'
    ]
    ordering_fields = [
        'name', 'sku', 'base_price', 'stock_quantity',
        'created_at', 'updated_at'
    ]
    ordering = ['-created_at']
    
    def get_queryset(self):
        queryset = Product.objects.filter(
            company=self.request.active_company
        ).select_related(
            'category', 'owner', 'created_by'
        ).prefetch_related(
            'variants', 'reviews', 'tags'
        )
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        
        if min_price:
            queryset = queryset.filter(base_price__gte=min_price)
        if max_price:
            queryset = queryset.filter(base_price__lte=max_price)
        
        # Filter by stock status
        stock_status = self.request.query_params.get('stock_status')
        if stock_status == 'in_stock':
            queryset = queryset.filter(stock_quantity__gt=0)
        elif stock_status == 'low_stock':
            queryset = queryset.filter(
                stock_quantity__lte=F('min_stock_level'),
                stock_quantity__gt=0
            )
        elif stock_status == 'out_of_stock':
            queryset = queryset.filter(stock_quantity=0)
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return ProductListSerializer
        return ProductSerializer
    
    @action(detail=True, methods=['post'])
    def adjust_stock(self, request, pk=None):
        """Adjust product stock quantity"""
        product = self.get_object()
        quantity = request.data.get('quantity', 0)
        transaction_type = request.data.get('transaction_type', 'adjustment')
        reference = request.data.get('reference', '')
        notes = request.data.get('notes', '')
        
        if not product.track_inventory:
            return Response(
                {'error': 'Inventory tracking is disabled for this product'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create inventory transaction
        InventoryTransaction.objects.create(
            product=product,
            transaction_type=transaction_type,
            quantity=quantity,
            reference=reference,
            notes=notes,
            company=request.active_company,
            created_by=request.user
        )
        
        # Update stock quantity
        product.stock_quantity += quantity
        product.save()
        
        return Response({'message': 'Stock adjusted successfully'})
    
    @action(detail=True, methods=['get'])
    def inventory_history(self, request, pk=None):
        """Get product inventory transaction history"""
        product = self.get_object()
        transactions = product.inventory_transactions.all().order_by('-created_at')
        serializer = InventoryTransactionSerializer(transactions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        """Get product reviews"""
        product = self.get_object()
        reviews = product.reviews.filter(is_approved=True).order_by('-created_at')
        serializer = ProductReviewSerializer(reviews, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_review(self, request, pk=None):
        """Add product review"""
        product = self.get_object()
        serializer = ProductReviewSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(
                product=product,
                company=request.active_company
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def variants(self, request, pk=None):
        """Get product variants"""
        product = self.get_object()
        variants = product.variants.all()
        serializer = ProductVariantSerializer(variants, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_variant(self, request, pk=None):
        """Add product variant"""
        product = self.get_object()
        serializer = ProductVariantSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(
                product=product,
                company=request.active_company
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def search(self, request):
        """Advanced product search"""
        query = request.query_params.get('q', '')
        category = request.query_params.get('category')
        product_type = request.query_params.get('product_type')
        min_price = request.query_params.get('min_price')
        max_price = request.query_params.get('max_price')
        in_stock_only = request.query_params.get('in_stock_only', 'false').lower() == 'true'
        featured_only = request.query_params.get('featured_only', 'false').lower() == 'true'
        
        queryset = self.get_queryset()
        
        # Apply filters
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(sku__icontains=query) |
                Q(description__icontains=query) |
                Q(short_description__icontains=query)
            )
        
        if category:
            queryset = queryset.filter(category_id=category)
        
        if product_type:
            queryset = queryset.filter(product_type=product_type)
        
        if min_price:
            queryset = queryset.filter(base_price__gte=min_price)
        
        if max_price:
            queryset = queryset.filter(base_price__lte=max_price)
        
        if in_stock_only:
            queryset = queryset.filter(stock_quantity__gt=0)
        
        if featured_only:
            queryset = queryset.filter(is_featured=True)
        
        # Get categories for filters
        categories = ProductCategory.objects.filter(
            company=request.active_company,
            is_active=True
        )
        
        # Prepare response
        products = queryset[:50]  # Limit results
        serializer = ProductListSerializer(products, many=True)
        
        response_data = {
            'products': serializer.data,
            'total_count': queryset.count(),
            'categories': ProductCategoryListSerializer(categories, many=True).data,
            'filters': {
                'query': query,
                'category': category,
                'product_type': product_type,
                'min_price': min_price,
                'max_price': max_price,
                'in_stock_only': in_stock_only,
                'featured_only': featured_only
            },
            'sort_options': [
                {'value': 'name', 'label': 'Name'},
                {'value': 'base_price', 'label': 'Price'},
                {'value': 'stock_quantity', 'label': 'Stock'},
                {'value': 'created_at', 'label': 'Newest'},
            ]
        }
        
        serializer = ProductSearchSerializer(response_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """Get low stock products"""
        queryset = self.get_queryset().filter(
            track_inventory=True,
            stock_quantity__lte=F('min_stock_level'),
            stock_quantity__gt=0
        )
        serializer = ProductListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def out_of_stock(self, request):
        """Get out of stock products"""
        queryset = self.get_queryset().filter(
            track_inventory=True,
            stock_quantity=0
        )
        serializer = ProductListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    @cache_api_response(timeout=300)
    def stats(self, request):
        """Get product statistics"""
        queryset = self.get_queryset()
        
        # Basic counts
        total_products = queryset.count()
        active_products = queryset.filter(status='active').count()
        low_stock_products = queryset.filter(
            track_inventory=True,
            stock_quantity__lte=F('min_stock_level'),
            stock_quantity__gt=0
        ).count()
        out_of_stock_products = queryset.filter(
            track_inventory=True,
            stock_quantity=0
        ).count()
        
        # Products by category
        products_by_category = {}
        for category in ProductCategory.objects.filter(company=request.active_company):
            count = queryset.filter(category=category).count()
            if count > 0:
                products_by_category[category.name] = count
        
        # Products by type
        products_by_type = {}
        for product_type, _ in Product.PRODUCT_TYPES:
            count = queryset.filter(product_type=product_type).count()
            products_by_type[product_type] = count
        
        # Products by status
        products_by_status = {}
        for status_choice, _ in Product.STATUS_CHOICES:
            count = queryset.filter(status=status_choice).count()
            products_by_status[status_choice] = count
        
        # Financial metrics
        total_inventory_value = queryset.aggregate(
            total=Sum(F('base_price') * F('stock_quantity'))
        )['total'] or 0
        
        average_product_price = queryset.aggregate(
            avg=Avg('base_price')
        )['avg'] or 0
        
        # Top products (by stock value)
        top_products = queryset.annotate(
            stock_value=F('base_price') * F('stock_quantity')
        ).order_by('-stock_value')[:10]
        
        top_products_data = []
        for product in top_products:
            top_products_data.append({
                'id': product.id,
                'name': product.name,
                'sku': product.sku,
                'stock_quantity': product.stock_quantity,
                'base_price': float(product.base_price),
                'stock_value': float(product.stock_value)
            })
        
        # Monthly trend (last 12 months)
        monthly_trend = []
        for i in range(12):
            month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            
            month_products = queryset.filter(
                created_at__date__range=[month_start.date(), month_end.date()]
            )
            
            monthly_trend.append({
                'month': month_start.strftime('%Y-%m'),
                'products': month_products.count(),
                'active': month_products.filter(status='active').count()
            })
        
        monthly_trend.reverse()
        
        stats_data = {
            'total_products': total_products,
            'active_products': active_products,
            'low_stock_products': low_stock_products,
            'out_of_stock_products': out_of_stock_products,
            'products_by_category': products_by_category,
            'products_by_type': products_by_type,
            'products_by_status': products_by_status,
            'total_inventory_value': float(total_inventory_value),
            'average_product_price': float(average_product_price),
            'top_products': top_products_data,
            'monthly_trend': monthly_trend
        }
        
        serializer = ProductStatsSerializer(stats_data)
        return Response(serializer.data)

class ProductVariantViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ProductVariant CRUD operations
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]
    
    def get_queryset(self):
        return ProductVariant.objects.filter(
            product__company=self.request.active_company
        ).select_related('product')
    
    def get_serializer_class(self):
        return ProductVariantSerializer

class PriceListViewSet(viewsets.ModelViewSet):
    """
    ViewSet for PriceList CRUD operations
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = ['is_default', 'is_active', 'currency']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        return PriceList.objects.filter(
            company=self.request.active_company
        ).prefetch_related('items__product')
    
    def get_serializer_class(self):
        return PriceListSerializer
    
    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """Get price list items"""
        price_list = self.get_object()
        items = price_list.items.filter(is_active=True)
        serializer = PriceListItemSerializer(items, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """Add item to price list"""
        price_list = self.get_object()
        serializer = PriceListItemSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(
                price_list=price_list,
                company=request.active_company
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PriceListItemViewSet(viewsets.ModelViewSet):
    """
    ViewSet for PriceListItem CRUD operations
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]
    
    def get_queryset(self):
        return PriceListItem.objects.filter(
            price_list__company=self.request.active_company
        ).select_related('price_list', 'product')
    
    def get_serializer_class(self):
        return PriceListItemSerializer

class InventoryTransactionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for InventoryTransaction CRUD operations
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    
    filterset_fields = ['product', 'transaction_type', 'related_quote', 'related_order']
    ordering_fields = ['created_at', 'quantity']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return InventoryTransaction.objects.filter(
            company=self.request.active_company
        ).select_related('product', 'created_by')
    
    def get_serializer_class(self):
        return InventoryTransactionSerializer

class ProductReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ProductReview CRUD operations
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    
    filterset_fields = ['product', 'rating', 'is_verified', 'is_approved']
    ordering_fields = ['created_at', 'rating']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return ProductReview.objects.filter(
            company=self.request.active_company
        ).select_related('product')
    
    def get_serializer_class(self):
        return ProductReviewSerializer

class ProductBundleViewSet(viewsets.ModelViewSet):
    """
    ViewSet for ProductBundle CRUD operations
    """
    permission_classes = [IsAuthenticated, IsCompanyMember]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    
    filterset_fields = ['is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'bundle_price', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        return ProductBundle.objects.filter(
            company=self.request.active_company
        ).prefetch_related('bundle_items__product')
    
    def get_serializer_class(self):
        return ProductBundleSerializer
    
    @action(detail=True, methods=['get'])
    def items(self, request, pk=None):
        """Get bundle items"""
        bundle = self.get_object()
        items = bundle.bundle_items.all()
        serializer = BundleItemSerializer(items, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """Add item to bundle"""
        bundle = self.get_object()
        serializer = BundleItemSerializer(data=request.data)
        
        if serializer.is_valid():
            serializer.save(
                bundle=bundle,
                company=request.active_company
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)