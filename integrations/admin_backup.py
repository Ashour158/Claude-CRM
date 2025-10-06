# integrations/admin.py
from django.contrib import admin
from .models import (
    APICredential, Webhook, WebhookLog,
    DataSync, DataSyncLog
)

@admin.register(APICredential)
class APICredentialAdmin(admin.ModelAdmin):
    list_display = ['name', 'service_name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'company']
    search_fields = ['name', 'service_name']
    ordering = ['-created_at']

@admin.register(Webhook)
class WebhookAdmin(admin.ModelAdmin):
    list_display = ['name', 'url', 'event_type', 'is_active', 'created_at']
    list_filter = ['event_type', 'is_active', 'created_at', 'company']
    search_fields = ['name', 'url']
    ordering = ['-created_at']

@admin.register(WebhookLog)
class WebhookLogAdmin(admin.ModelAdmin):
    list_display = ['webhook', 'status_code', 'created_at']
    list_filter = ['status_code', 'created_at', 'webhook__company']
    search_fields = ['webhook__name', 'response_body']
    ordering = ['-created_at']
    raw_id_fields = ['webhook']

@admin.register(DataSync)
class DataSyncAdmin(admin.ModelAdmin):
    list_display = ['name', 'source_system', 'target_system', 'sync_type', 'is_active', 'last_sync_at']
    list_filter = ['sync_type', 'is_active', 'last_sync_at', 'company']
    search_fields = ['name', 'source_system', 'target_system']
    ordering = ['-last_sync_at']

@admin.register(DataSyncLog)
class DataSyncLogAdmin(admin.ModelAdmin):
    list_display = ['data_sync', 'status', 'records_processed', 'records_success', 'records_failed', 'started_at']
    list_filter = ['status', 'started_at', 'data_sync__company']
    search_fields = ['data_sync__name']
    ordering = ['-started_at']
    raw_id_fields = ['data_sync']
