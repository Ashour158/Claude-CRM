# vendors/urls.py
# Vendors URL patterns

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'vendors', views.VendorViewSet)
router.register(r'vendor-contacts', views.VendorContactViewSet)
router.register(r'purchase-orders', views.PurchaseOrderViewSet)
router.register(r'purchase-order-items', views.PurchaseOrderItemViewSet)
router.register(r'vendor-performance', views.VendorPerformanceViewSet)

urlpatterns = [
    path('', include(router.urls)),
]