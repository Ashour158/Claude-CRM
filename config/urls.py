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
    
    # API URLs
    path('api/auth/', include('core.urls')),
    path('api/crm/', include('crm.urls')),
    path('api/territories/', include('territories.urls')),
    path('api/activities/', include('activities.urls')),
    path('api/deals/', include('deals.urls')),
    path('api/products/', include('products.urls')),
    path('api/sales/', include('sales.urls')),
    path('api/vendors/', include('vendors.urls')),
    path('api/analytics/', include('analytics.urls')),
    path('api/marketing/', include('marketing.urls')),
    path('api/system-config/', include('system_config.urls')),
    path('api/integrations/', include('integrations.urls')),
    path('api/master-data/', include('master_data.urls')),
    path('api/workflow/', include('workflow.urls')),
    
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
