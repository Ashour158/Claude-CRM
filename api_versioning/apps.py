# api_versioning/apps.py
# API Versioning App Configuration

from django.apps import AppConfig

class ApiVersioningConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'api_versioning'
    verbose_name = 'API Versioning & Management'
    
    def ready(self):
        """App ready hook"""
        # Import signal handlers if needed
        pass
