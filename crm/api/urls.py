# crm/api/urls.py
"""
URL configuration for CRM API endpoints
"""
from django.urls import path
from . import views

app_name = 'crm_api'

urlpatterns = [
    # Timeline endpoint
    path('activities/timeline/', views.timeline_list, name='timeline-list'),
    
    # Lead conversion endpoint
    path('leads/convert/', views.convert_lead, name='lead-convert'),
]
