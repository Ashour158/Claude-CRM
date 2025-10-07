# audit/apps.py
# Audit App Configuration

from django.apps import AppConfig

class AuditConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'audit'
    verbose_name = 'Audit & Compliance'
    
    def ready(self):
        """App ready hook"""
        # Import signal handlers if needed
        pass
