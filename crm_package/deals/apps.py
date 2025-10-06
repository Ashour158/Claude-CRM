"""
Django app configuration for deals module.
"""

from django.apps import AppConfig


class DealsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crm_package.deals'
    verbose_name = 'CRM Deals'
