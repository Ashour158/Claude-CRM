# core/permissions/__init__.py
# Permission enforcement layer exports

from .base import ObjectTypePermission, ActionPermission

__all__ = ['ObjectTypePermission', 'ActionPermission']
