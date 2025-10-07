# data_import/apps.py
# Data Import App Configuration

from django.apps import AppConfig

class DataImportConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'data_import'
    verbose_name = 'Data Import & Deduplication'
    
    def ready(self):
        """App ready hook"""
        # Import signal handlers if needed
        pass
