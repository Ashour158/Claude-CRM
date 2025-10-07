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
    
    # API URLs - Core
    path('api/core/', include('core.urls')),
    path('api/auth/', include('core.urls')),  # Alias for frontend compatibility
    
    # API URLs - CRM
    path('api/crm/', include('crm.urls')),
    
    # API URLs - Activities
    path('api/activities/', include('activities.urls')),
    
    # API URLs - Deals
    path('api/deals/', include('deals.urls')),
    
    # API URLs - Products
    path('api/products/', include('products.urls')),
    
    # API URLs - Territories
    path('api/territories/', include('territories.urls')),
    
    # API URLs - Sales (placeholder)
    # path('api/sales/', include('sales.urls')),
    
    # API URLs - Vendors (placeholder)
    # path('api/vendors/', include('vendors.urls')),
    
    # API URLs - Analytics
    path('api/analytics/', include('analytics.urls')),
    
    # API URLs - Marketing (placeholder)
    # path('api/marketing/', include('marketing.urls')),
    
    # API URLs - System Config (placeholder)
    # path('api/system-config/', include('system_config.urls')),
    
    # API URLs - Integrations
    path('api/integrations/', include('integrations.urls')),
    
    # API URLs - Master Data (placeholder)
    # path('api/master-data/', include('master_data.urls')),
    
    # API URLs - Workflow
    path('api/workflow/', include('workflow.urls')),
    
    # API URLs - Sharing
    path('api/sharing/', include('sharing.urls')),
    
    # API URLs - Enterprise Features
    path('api/data-import/', include('data_import.urls')),
    path('api/api-versioning/', include('api_versioning.urls')),
    path('api/marketplace/', include('marketplace.urls')),
    path('api/audit/', include('audit.urls')),
    
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
