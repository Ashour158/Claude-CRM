# core/serializers.py
# Core serializers

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Company, UserCompanyAccess, AuditLog

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """User serializer"""
    
    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'is_active', 'date_joined']
        read_only_fields = ['id', 'date_joined']

class CompanySerializer(serializers.ModelSerializer):
    """Company serializer"""
    
    class Meta:
        model = Company
        fields = ['id', 'name', 'code', 'domain', 'email', 'phone', 'is_active']
        read_only_fields = ['id']

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