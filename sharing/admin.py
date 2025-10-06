# sharing/admin.py
# Django admin for sharing models

from django.contrib import admin
from .models import SharingRule, RecordShare


@admin.register(SharingRule)
class SharingRuleAdmin(admin.ModelAdmin):
    """Admin interface for SharingRule"""
    
    list_display = ['name', 'company', 'object_type', 'access_level', 'is_active', 'created_at']
    list_filter = ['object_type', 'access_level', 'is_active', 'company']
    search_fields = ['name', 'description']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'company', 'name', 'description')
        }),
        ('Rule Configuration', {
            'fields': ('object_type', 'predicate', 'access_level', 'is_active')
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(RecordShare)
class RecordShareAdmin(admin.ModelAdmin):
    """Admin interface for RecordShare"""
    
    list_display = ['object_type', 'object_id', 'user', 'company', 'access_level', 'created_at']
    list_filter = ['object_type', 'access_level', 'company']
    search_fields = ['object_id', 'user__email', 'reason']
    readonly_fields = ['id', 'created_at']
    
    fieldsets = (
        ('Share Configuration', {
            'fields': ('id', 'company', 'object_type', 'object_id', 'user', 'access_level')
        }),
        ('Additional Information', {
            'fields': ('reason',)
        }),
        ('Audit Information', {
            'fields': ('created_by', 'created_at')
        }),
    )
