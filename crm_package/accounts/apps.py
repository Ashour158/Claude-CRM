"""
Django app configuration for accounts module.
"""

from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'crm_package.accounts'
    verbose_name = 'CRM Accounts'
