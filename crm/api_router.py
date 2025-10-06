# crm/api_router.py
# Phase 2 API Router - Aggregates all v1 API endpoints
from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import viewsets from apps
from crm.views import AccountViewSet, ContactViewSet, LeadViewSet
from activities.views import ActivityViewSet, TaskViewSet, EventViewSet
from deals.views import DealViewSet

# Import Phase 2 API views
from crm.api_views import (
    activities_timeline,
    lead_convert,
    saved_views,
    leads_bulk,
    global_search,
    deals_board,
    settings_summary
)

# Create router and register viewsets
router = DefaultRouter()

# CRM viewsets
router.register(r'accounts', AccountViewSet, basename='account')
router.register(r'contacts', ContactViewSet, basename='contact')
router.register(r'leads', LeadViewSet, basename='lead')

# Activities viewsets
router.register(r'activities', ActivityViewSet, basename='activity')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'events', EventViewSet, basename='event')

# Deals viewsets
router.register(r'deals', DealViewSet, basename='deal')

# API v1 URL patterns
urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Phase 2 custom endpoints
    path('activities/timeline/', activities_timeline, name='activities-timeline'),
    path('leads/convert/<uuid:id>/', lead_convert, name='lead-convert'),
    path('leads/bulk/', leads_bulk, name='leads-bulk'),
    path('meta/saved-views/', saved_views, name='saved-views'),
    path('search/', global_search, name='global-search'),
    path('deals/board/', deals_board, name='deals-board'),
    path('settings/summary/', settings_summary, name='settings-summary'),
]
