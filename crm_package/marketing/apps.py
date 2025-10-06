"""
Django app configuration for marketing module.
"""

from django.apps import AppConfig


class MarketingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crm_package.marketing'
    verbose_name = 'CRM Marketing'
