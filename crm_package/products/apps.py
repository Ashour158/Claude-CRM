"""
Django app configuration for products module.
"""

from django.apps import AppConfig


class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crm_package.products'
    verbose_name = 'CRM Products'
