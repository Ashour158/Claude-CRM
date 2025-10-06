# config/urls.py
# Main URL Configuration

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API v1 - Consolidated router
    path('api/v1/', include('crm.api_router')),
    
    # API URLs - Core
    path('api/core/', include('core.urls')),
    path('api/auth/', include('core.urls')),  # Alias for frontend compatibility
    
    # Health Check
    path('health/', TemplateView.as_view(template_name='health.html')),
    
    # API Documentation (if using drf-yasg)
    # path('api/docs/', include('drf_yasg.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Django Debug Toolbar
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns

# Admin site customization
admin.site.site_header = "CRM System Administration"
admin.site.site_title = "CRM Admin"
admin.site.index_title = "Welcome to CRM Administration"
