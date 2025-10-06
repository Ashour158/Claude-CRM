# core/admin.py
# Django Admin Configuration for Core Models

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from .models import User, Company, UserCompanyAccess, UserSession, SavedListView, CustomFieldValue, TimelineEvent


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """Company admin interface"""
    list_display = [
        'name', 'code', 'email', 'phone', 'is_active', 
        'users_count', 'created_at'
    ]
    list_filter = ['is_active', 'created_at', 'updated_at']
    search_fields = ['name', 'code', 'email', 'phone']
    readonly_fields = ['code', 'created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'description', 'website')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'address_line1', 'address_line2', 
                      'city', 'state', 'postal_code', 'country')
        }),
        ('Settings', {
            'fields': ('timezone', 'currency', 'date_format', 'time_format')
        }),
        ('Branding', {
            'fields': ('logo_url', 'primary_color', 'secondary_color')
        }),
        ('Subscription', {
            'fields': ('subscription_plan', 'subscription_status', 'trial_ends_at')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def users_count(self, obj):
        """Display number of users in company"""
        count = obj.users.count()
        if count > 0:
            url = reverse('admin:core_user_changelist') + f'?company__id__exact={obj.id}'
            return format_html('<a href="{}">{} users</a>', url, count)
        return '0 users'
    users_count.short_description = 'Users'


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom user admin interface"""
    list_display = [
        'email', 'first_name', 'last_name', 'is_active', 
        'is_staff', 'companies_count', 'last_login'
    ]
    list_filter = [
        'is_active', 'is_staff', 'is_superuser', 'last_login', 
        'date_joined', 'email_verified'
    ]
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['email']
    readonly_fields = ['date_joined', 'last_login', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('email', 'first_name', 'last_name', 'phone', 'avatar_url')
        }),
        ('Authentication', {
            'fields': ('password', 'email_verified', 'verification_token', 
                      'password_reset_token', 'password_reset_expires_at')
        }),
        ('Two-Factor Authentication', {
            'fields': ('two_factor_enabled', 'two_factor_secret'),
            'classes': ('collapse',)
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Session Information', {
            'fields': ('last_login', 'last_login_ip', 'last_login_user_agent'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    add_fieldsets = (
        ('Personal Information', {
            'fields': ('email', 'first_name', 'last_name', 'phone')
        }),
        ('Authentication', {
            'fields': ('password1', 'password2')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser')
        })
    )
    
    def companies_count(self, obj):
        """Display number of companies user belongs to"""
        count = obj.companies.count()
        if count > 0:
            url = reverse('admin:core_usercompanyaccess_changelist') + f'?user__id__exact={obj.id}'
            return format_html('<a href="{}">{} companies</a>', url, count)
        return '0 companies'
    companies_count.short_description = 'Companies'


@admin.register(UserCompanyAccess)
class UserCompanyAccessAdmin(admin.ModelAdmin):
    """User company access admin interface"""
    list_display = [
        'user', 'company', 'role', 'is_primary', 'is_active', 'created_at'
    ]
    list_filter = ['role', 'is_primary', 'is_active', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'company__name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Access Information', {
            'fields': ('user', 'company', 'role', 'is_primary', 'is_active')
        }),
        ('Permissions', {
            'fields': ('permissions',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """User session admin interface"""
    list_display = [
        'user', 'session_key', 'is_valid', 'created_at', 'expires_at', 'ip_address'
    ]
    list_filter = ['is_valid', 'created_at', 'expires_at']
    search_fields = ['user__email', 'session_key', 'ip_address']
    readonly_fields = ['session_key', 'access_token', 'refresh_token', 'created_at']
    
    fieldsets = (
        ('Session Information', {
            'fields': ('user', 'session_key', 'is_valid')
        }),
        ('Tokens', {
            'fields': ('access_token', 'refresh_token', 'expires_at'),
            'classes': ('collapse',)
        }),
        ('Device Information', {
            'fields': ('ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def has_add_permission(self, request):
        """Disable adding sessions manually"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable changing sessions manually"""
        return False


@admin.register(SavedListView)
class SavedListViewAdmin(admin.ModelAdmin):
    """Saved list view admin interface"""
    list_display = [
        'name', 'entity_type', 'organization', 'owner', 'is_private', 
        'is_active', 'created_at'
    ]
    list_filter = ['entity_type', 'is_private', 'is_active', 'created_at']
    search_fields = ['name', 'organization__name', 'owner__email']
    readonly_fields = ['created_at', 'updated_at', 'deleted_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'entity_type', 'organization', 'owner')
        }),
        ('View Definition', {
            'fields': ('definition',)
        }),
        ('Settings', {
            'fields': ('is_private', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(CustomFieldValue)
class CustomFieldValueAdmin(admin.ModelAdmin):
    """Custom field value admin interface"""
    list_display = [
        'custom_field_name', 'entity_type', 'entity_id', 'company', 'created_at'
    ]
    list_filter = ['entity_type', 'custom_field_name', 'created_at']
    search_fields = ['custom_field_name', 'value_text', 'value_select']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Field Information', {
            'fields': ('custom_field_id', 'custom_field_name', 'company')
        }),
        ('Entity Reference', {
            'fields': ('entity_type', 'entity_id')
        }),
        ('Values', {
            'fields': ('value_text', 'value_number', 'value_date', 
                      'value_datetime', 'value_boolean', 'value_select')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(TimelineEvent)
class TimelineEventAdmin(admin.ModelAdmin):
    """Timeline event admin interface"""
    list_display = [
        'event_type', 'title', 'entity_type', 'entity_id', 'user', 
        'company', 'created_at'
    ]
    list_filter = ['event_type', 'entity_type', 'created_at']
    search_fields = ['title', 'description', 'user__email']
    readonly_fields = ['created_at']
    
    fieldsets = (
        ('Event Information', {
            'fields': ('event_type', 'title', 'description', 'company')
        }),
        ('Entity Reference', {
            'fields': ('entity_type', 'entity_id')
        }),
        ('Actor', {
            'fields': ('user',)
        }),
        ('Additional Data', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
        ('Timestamp', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def has_add_permission(self, request):
        """Disable adding timeline events manually"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable changing timeline events manually"""
        return False
