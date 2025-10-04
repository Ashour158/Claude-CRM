# products/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from products.views import (
    ProductCategoryViewSet, ProductViewSet, ProductVariantViewSet,
    PriceListViewSet, PriceListItemViewSet, InventoryTransactionViewSet,
    ProductReviewViewSet, ProductBundleViewSet
)

router = DefaultRouter()
router.register(r'categories', ProductCategoryViewSet, basename='product-category')
router.register(r'products', ProductViewSet, basename='product')
router.register(r'product-variants', ProductVariantViewSet, basename='product-variant')
router.register(r'price-lists', PriceListViewSet, basename='price-list')
router.register(r'price-list-items', PriceListItemViewSet, basename='price-list-item')
router.register(r'inventory-transactions', InventoryTransactionViewSet, basename='inventory-transaction')
router.register(r'reviews', ProductReviewViewSet, basename='product-review')
router.register(r'bundles', ProductBundleViewSet, basename='product-bundle')

urlpatterns = [
    path('', include(router.urls)),
]