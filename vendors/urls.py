# vendors/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from vendors.views import (
    VendorViewSet, VendorContactViewSet, VendorProductViewSet,
    PurchaseOrderViewSet, VendorInvoiceViewSet, VendorPaymentViewSet
)

router = DefaultRouter()
router.register(r'vendors', VendorViewSet, basename='vendor')
router.register(r'vendor-contacts', VendorContactViewSet, basename='vendor-contact')
router.register(r'vendor-products', VendorProductViewSet, basename='vendor-product')
router.register(r'purchase-orders', PurchaseOrderViewSet, basename='purchase-order')
router.register(r'vendor-invoices', VendorInvoiceViewSet, basename='vendor-invoice')
router.register(r'vendor-payments', VendorPaymentViewSet, basename='vendor-payment')

urlpatterns = [
    path('', include(router.urls)),
]
