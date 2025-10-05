# products/urls.py
# Products URL patterns

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'products', views.ProductViewSet)
router.register(r'categories', views.ProductCategoryViewSet)
router.register(r'price-lists', views.PriceListViewSet)

urlpatterns = [
    path('', include(router.urls)),
]