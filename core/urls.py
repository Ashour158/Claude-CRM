# core/urls.py
# Core URL patterns

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views_saved_views import SavedListViewViewSet
from .search.views import GlobalSearchView, SearchSuggestionsView

router = DefaultRouter()
router.register(r'companies', views.CompanyViewSet)
router.register(r'user-company-access', views.UserCompanyAccessViewSet)
router.register(r'audit-logs', views.AuditLogViewSet)
router.register(r'saved-views', SavedListViewViewSet, basename='saved-views')

urlpatterns = [
    path('', include(router.urls)),
    path('health/', views.health_check, name='health_check'),
    path('profile/', views.user_profile, name='user_profile'),
    path('status/', views.system_status, name='system_status'),
    path('search/', GlobalSearchView.as_view(), name='global_search'),
    path('search/suggestions/', SearchSuggestionsView.as_view(), name='search_suggestions'),
]