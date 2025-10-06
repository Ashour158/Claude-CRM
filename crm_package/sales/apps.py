"""
Django app configuration for sales module.
"""

from django.apps import AppConfig


class SalesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crm_package.sales'
    verbose_name = 'CRM Sales'
