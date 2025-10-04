# sales/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from sales.views import (
    QuoteViewSet, SalesOrderViewSet, InvoiceViewSet,
    PaymentViewSet, SalesStatsViewSet
)

router = DefaultRouter()
router.register(r'quotes', QuoteViewSet, basename='quote')
router.register(r'orders', SalesOrderViewSet, basename='sales-order')
router.register(r'invoices', InvoiceViewSet, basename='invoice')
router.register(r'payments', PaymentViewSet, basename='payment')
router.register(r'stats', SalesStatsViewSet, basename='sales-stats')

urlpatterns = [
    path('', include(router.urls)),
]
