# compliance/apps.py
# Compliance App Configuration

from django.apps import AppConfig

class ComplianceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'compliance'
    verbose_name = 'Compliance & Governance'
    
    def ready(self):
        """App ready hook"""
        # Import signal handlers if needed
        pass
