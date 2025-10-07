# marketplace/admin.py
# Admin configuration for marketplace module

from django.contrib import admin
from .models import Plugin, PluginInstallation, PluginExecution, PluginReview

@admin.register(Plugin)
class PluginAdmin(admin.ModelAdmin):
    list_display = ['name', 'version', 'plugin_type', 'status', 'is_featured', 'is_verified', 
                   'install_count', 'rating_average', 'developer_name']
    list_filter = ['plugin_type', 'status', 'is_featured', 'is_verified', 'pricing_model']
    search_fields = ['name', 'description', 'plugin_id', 'developer_name']
    readonly_fields = ['install_count', 'active_installs', 'rating_average', 'rating_count', 
                       'download_count', 'created_at', 'updated_at', 'published_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('plugin_id', 'name', 'description', 'tagline', 'plugin_type', 'version')
        }),
        ('Manifest & Requirements', {
            'fields': ('manifest', 'min_system_version', 'dependencies', 'required_permissions')
        }),
        ('Installation', {
            'fields': ('install_script', 'uninstall_script', 'configuration_schema', 'default_configuration'),
            'classes': ('collapse',)
        }),
        ('Media', {
            'fields': ('icon_url', 'screenshots', 'video_url')
        }),
        ('Developer', {
            'fields': ('developer_name', 'developer_email', 'developer_website', 'support_url', 'documentation_url')
        }),
        ('Pricing', {
            'fields': ('is_free', 'price', 'pricing_model', 'trial_days')
        }),
        ('Status & Verification', {
            'fields': ('status', 'is_featured', 'is_verified', 'reviewed_by', 'review_notes')
        }),
        ('Statistics', {
            'fields': ('install_count', 'active_installs', 'rating_average', 'rating_count', 'download_count'),
            'classes': ('collapse',)
        }),
    )

@admin.register(PluginInstallation)
class PluginInstallationAdmin(admin.ModelAdmin):
    list_display = ['plugin', 'company', 'installed_version', 'status', 'is_enabled', 
                   'installed_at', 'installed_by']
    list_filter = ['status', 'is_enabled', 'installed_at']
    search_fields = ['plugin__name', 'company__name']
    readonly_fields = ['installation_id', 'installed_at', 'last_updated', 'last_activated', 
                       'last_deactivated', 'error_count', 'last_error', 'execution_count', 'last_execution']

@admin.register(PluginExecution)
class PluginExecutionAdmin(admin.ModelAdmin):
    list_display = ['installation', 'trigger_type', 'status', 'started_at', 'completed_at', 'duration_ms']
    list_filter = ['status', 'trigger_type', 'started_at']
    search_fields = ['installation__plugin__name', 'execution_id']
    readonly_fields = ['execution_id', 'started_at', 'completed_at', 'duration_ms']

@admin.register(PluginReview)
class PluginReviewAdmin(admin.ModelAdmin):
    list_display = ['plugin', 'reviewer', 'rating', 'is_verified_purchase', 'helpful_count', 'created_at']
    list_filter = ['rating', 'is_verified_purchase', 'created_at']
    search_fields = ['plugin__name', 'reviewer__email', 'title', 'review_text']
    readonly_fields = ['helpful_count', 'not_helpful_count', 'created_at', 'updated_at']
