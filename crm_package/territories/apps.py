"""
Django app configuration for territories module.
"""

from django.apps import AppConfig


class TerritoriesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crm_package.territories'
    verbose_name = 'CRM Territories'
