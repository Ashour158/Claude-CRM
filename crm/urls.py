# crm/urls.py
# CRM URL Configuration

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from crm.views.accounts import AccountViewSet
from crm.views.contacts import ContactViewSet
from crm.views.leads import LeadViewSet

# Create router and register viewsets
router = DefaultRouter()
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'contacts', ContactViewSet, basename='contact')
router.register(r'leads', LeadViewSet, basename='lead')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
]
