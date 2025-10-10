# core/serializers.py
# Core serializers

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Company, UserCompanyAccess, AuditLog, Permission, Role, UserRole,
    UserActivity, UserPreference, UserInvitation
)

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """User serializer"""
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'full_name', 'phone', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined']
    
    def get_full_name(self, obj):
        return obj.get_full_name()

class CompanySerializer(serializers.ModelSerializer):
    """Company serializer"""
    
    class Meta:
        model = Company
        fields = ['id', 'name', 'code', 'domain', 'email', 'phone', 'is_active']
        read_only_fields = ['id']

class PermissionSerializer(serializers.ModelSerializer):
    """Permission serializer"""
    
    class Meta:
        model = Permission
        fields = ['id', 'name', 'codename', 'description', 'module', 'created_at']
        read_only_fields = ['id', 'created_at']

class RoleSerializer(serializers.ModelSerializer):
    """Role serializer"""
    permissions = PermissionSerializer(many=True, read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    permissions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'permissions', 'permissions_count', 'company', 'company_name', 'is_system_role', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_permissions_count(self, obj):
        return obj.permissions.count()

class UserRoleSerializer(serializers.ModelSerializer):
    """User role serializer"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)
    assigned_by_email = serializers.EmailField(source='assigned_by.email', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = UserRole
        fields = ['id', 'user', 'user_email', 'role', 'role_name', 'assigned_by', 'assigned_by_email', 
                  'assigned_at', 'expires_at', 'is_active', 'is_expired']
        read_only_fields = ['id', 'assigned_at']

class UserActivitySerializer(serializers.ModelSerializer):
    """User activity serializer"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = UserActivity
        fields = ['id', 'user', 'user_email', 'activity_type', 'module', 'description', 
                  'ip_address', 'user_agent', 'metadata', 'created_at']
        read_only_fields = ['id', 'created_at']

class UserPreferenceSerializer(serializers.ModelSerializer):
    """User preference serializer"""
    
    class Meta:
        model = UserPreference
        fields = ['id', 'user', 'theme', 'language', 'timezone', 'date_format', 'time_format',
                  'notifications_enabled', 'email_notifications', 'desktop_notifications', 
                  'custom_settings', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class UserInvitationSerializer(serializers.ModelSerializer):
    """User invitation serializer"""
    company_name = serializers.CharField(source='company.name', read_only=True)
    invited_by_email = serializers.EmailField(source='invited_by.email', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = UserInvitation
        fields = ['id', 'email', 'company', 'company_name', 'invited_by', 'invited_by_email',
                  'role', 'role_name', 'token', 'status', 'message', 'created_at', 'expires_at',
                  'accepted_at', 'is_expired']
        read_only_fields = ['id', 'token', 'created_at', 'accepted_at']

class UserCompanyAccessSerializer(serializers.ModelSerializer):
    """User company access serializer"""
    user = UserSerializer(read_only=True)
    company = CompanySerializer(read_only=True)
    
    class Meta:
        model = UserCompanyAccess
        fields = ['id', 'user', 'company', 'role', 'is_active', 'is_primary']
        read_only_fields = ['id']

class AuditLogSerializer(serializers.ModelSerializer):
    """Audit log serializer"""
    user = UserSerializer(read_only=True)
    company = CompanySerializer(read_only=True)
    
    class Meta:
        model = AuditLog
        fields = ['id', 'action', 'user', 'company', 'object_type', 'object_id', 'details', 'ip_address', 'created_at']
        read_only_fields = ['id', 'created_at']

# Additional serializers for enhanced functionality
class UserDetailSerializer(UserSerializer):
    """Extended user serializer with additional details"""
    roles = UserRoleSerializer(source='user_roles', many=True, read_only=True)
    companies = serializers.SerializerMethodField()
    preferences = UserPreferenceSerializer(read_only=True)
    last_activity = serializers.SerializerMethodField()
    
    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['roles', 'companies', 'preferences', 'last_activity', 'avatar']
    
    def get_companies(self, obj):
        accesses = obj.company_access.filter(is_active=True)
        return UserCompanyAccessSerializer(accesses, many=True).data
    
    def get_last_activity(self, obj):
        activity = obj.activities.first()
        if activity:
            return UserActivitySerializer(activity).data
        return None

class BulkUserActionSerializer(serializers.Serializer):
    """Serializer for bulk user actions"""
    user_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True
    )
    action = serializers.ChoiceField(
        choices=['activate', 'deactivate', 'delete'],
        required=True
    )

class UserStatsSerializer(serializers.Serializer):
    """Serializer for user statistics"""
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    inactive_users = serializers.IntegerField()
    pending_invitations = serializers.IntegerField()
    users_by_role = serializers.DictField()
    recent_activities = UserActivitySerializer(many=True)