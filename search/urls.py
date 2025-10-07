# search/urls.py
# Search and Knowledge Layer URLs

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'search'

router = DefaultRouter()
router.register(r'query-expansion', views.QueryExpansionViewSet, basename='query-expansion')
router.register(r'metrics', views.SearchMetricViewSet, basename='metrics')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Advanced search endpoint
    path('advanced/', views.advanced_search, name='advanced_search'),
    
    # Relationship graph endpoints
    path('graph/', views.relationship_graph, name='relationship_graph'),
    path('graph/rebuild/', views.rebuild_graph, name='rebuild_graph'),
    
    # Interaction tracking
    path('track/', views.track_interaction, name='track_interaction'),
]
