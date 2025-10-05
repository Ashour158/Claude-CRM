# sales/urls.py
# Sales URL patterns

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'quotes', views.QuoteViewSet)
router.register(r'quote-items', views.QuoteItemViewSet)
router.register(r'sales-orders', views.SalesOrderViewSet)
router.register(r'sales-order-items', views.SalesOrderItemViewSet)
router.register(r'invoices', views.InvoiceViewSet)
router.register(r'invoice-items', views.InvoiceItemViewSet)

urlpatterns = [
    path('', include(router.urls)),
]