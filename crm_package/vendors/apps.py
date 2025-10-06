"""
Django app configuration for vendors module.
"""

from django.apps import AppConfig


class VendorsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crm_package.vendors'
    verbose_name = 'CRM Vendors'
