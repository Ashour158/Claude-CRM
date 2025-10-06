# core/admin.py
# Django Admin Configuration for Core Models

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User, Company, UserCompanyAccess, UserSession


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """Company admin interface"""
    list_display = ['name', 'code', 'email', 'phone', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at', 'updated_at']
    search_fields = ['name', 'code', 'email', 'phone']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom user admin interface"""
    list_display = ['email', 'first_name', 'last_name', 'is_active', 'is_staff', 'last_login']
    list_filter = ['is_active', 'is_staff', 'is_superuser', 'last_login', 'date_joined', 'email_verified']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['email']
    readonly_fields = ['date_joined', 'last_login']
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('email', 'first_name', 'last_name', 'phone', 'avatar')
        }),
        ('Authentication', {
            'fields': ('password', 'email_verified')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Timestamps', {
            'fields': ('date_joined', 'last_login'),
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


@admin.register(UserCompanyAccess)
class UserCompanyAccessAdmin(admin.ModelAdmin):
    """User company access admin interface"""
    list_display = ['user', 'company', 'role', 'is_primary', 'is_active', 'created_at']
    list_filter = ['role', 'is_primary', 'is_active', 'created_at']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'company__name']
    readonly_fields = ['created_at']


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """User session admin interface"""
    list_display = ['user', 'session_key', 'created_at', 'expires_at', 'ip_address']
    list_filter = ['created_at', 'expires_at']
    search_fields = ['user__email', 'session_key', 'ip_address']
    readonly_fields = ['session_key', 'created_at']
    
    def has_add_permission(self, request):
        """Disable adding sessions manually"""
        return False
