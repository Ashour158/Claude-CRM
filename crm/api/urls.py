# crm/api/urls.py
# URL configuration for CRM API stubs

from django.urls import path, include
from . import stub_endpoints

app_name = 'crm_api'

urlpatterns = [
    # Timeline (from activities)
    path('activities/', include('crm.activities.api.urls')),
    
    # Stub endpoints
    path('meta/saved-views/', stub_endpoints.saved_views, name='saved-views'),
    path('leads/bulk/', stub_endpoints.bulk_actions, name='bulk-actions-leads'),
    path('search/', stub_endpoints.global_search, name='global-search'),
    path('deals/board/', stub_endpoints.kanban_board, name='kanban-board'),
    path('settings/summary/', stub_endpoints.settings_summary, name='settings-summary'),
]
