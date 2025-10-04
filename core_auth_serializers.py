# core/serializers/auth.py
# Serializers for authentication and user management

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from core.models import User, Company, UserCompanyAccess

# ========================================
# USER SERIALIZERS
# ========================================

class UserSerializer(serializers.ModelSerializer):
    """Serializer for user data"""
    
    full_name = serializers.ReadOnlyField()
    companies_count = serializers.SerializerMethodField()
    primary_company = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'full_name',
            'phone', 'mobile', 'avatar_url', 'title', 'department',
            'email_verified', 'two_factor_enabled',
            'last_login_at', 'is_active', 'is_superadmin',
            'companies_count', 'primary_company',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'email_verified', 'last_login_at',
            'is_superadmin', 'created_at', 'updated_at'
        ]
    
    def get_companies_count(self, obj):
        return obj.company_access.filter(is_active=True).count()
    
    def get_primary_company(self, obj):
        primary = obj.get_primary_company()
        if primary:
            return {
                'id': str(primary.id),
                'name': primary.name,
                'code': primary.code
            }
        return None

class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )
    
    class Meta:
        model = User
        fields = [
            'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone', 'title'
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                "password": "Password fields didn't match."
            })
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone=validated_data.get('phone', ''),
            title=validated_data.get('title', '')
        )
        return user

class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    
    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(
                request=self.context.get('request'),
                username=email,
                password=password
            )
            
            if not user:
                raise serializers.ValidationError(
                    'Unable to log in with provided credentials.',
                    code='authorization'
                )
            
            if not user.is_active:
                raise serializers.ValidationError(
                    'User account is disabled.',
                    code='authorization'
                )
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError(
                'Must include "email" and "password".',
                code='authorization'
            )

class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change"""
    
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password": "Password fields didn't match."
            })
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request"""
    
    email = serializers.EmailField(required=True)
    
    def validate_email(self, value):
        try:
            User.objects.get(email=value)
        except User.DoesNotExist:
            # Don't reveal if email exists or not for security
            pass
        return value

class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation"""
    
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                "new_password": "Password fields didn't match."
            })
        return attrs

# ========================================
# COMPANY SERIALIZERS
# ========================================

class CompanySerializer(serializers.ModelSerializer):
    """Serializer for company data"""
    
    users_count = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(
        source='created_by.full_name',
        read_only=True
    )
    
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'legal_name', 'code', 'tax_id',
            'email', 'phone', 'website',
            'address_line1', 'address_line2', 'city', 'state',
            'postal_code', 'country',
            'currency', 'timezone', 'date_format', 'fiscal_year_start_month',
            'logo_url', 'primary_color',
            'is_active', 'subscription_plan', 'subscription_expires_at',
            'users_count', 'created_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_users_count(self, obj):
        return obj.user_access.filter(is_active=True).count()

class CompanyListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for company list"""
    
    class Meta:
        model = Company
        fields = ['id', 'name', 'code', 'logo_url', 'is_active']

# ========================================
# USER COMPANY ACCESS SERIALIZERS
# ========================================

class UserCompanyAccessSerializer(serializers.ModelSerializer):
    """Serializer for user company access"""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    company_name = serializers.CharField(source='company.name', read_only=True)
    granted_by_name = serializers.CharField(
        source='granted_by.full_name',
        read_only=True
    )
    
    class Meta:
        model = UserCompanyAccess
        fields = [
            'id', 'user', 'user_email', 'user_name',
            'company', 'company_name',
            'role', 'can_create', 'can_read', 'can_update',
            'can_delete', 'can_export',
            'is_primary', 'is_active',
            'granted_by', 'granted_by_name', 'granted_at', 'revoked_at'
        ]
        read_only_fields = ['id', 'granted_at']

class AddUserToCompanySerializer(serializers.Serializer):
    """Serializer for adding user to company"""
    
    email = serializers.EmailField(required=True)
    role = serializers.ChoiceField(
        choices=UserCompanyAccess.ROLE_CHOICES,
        required=True
    )
    is_primary = serializers.BooleanField(default=False)
    can_create = serializers.BooleanField(default=True)
    can_read = serializers.BooleanField(default=True)
    can_update = serializers.BooleanField(default=True)
    can_delete = serializers.BooleanField(default=False)
    can_export = serializers.BooleanField(default=False)
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            self.context['user'] = user
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")

class SwitchCompanySerializer(serializers.Serializer):
    """Serializer for switching active company"""
    
    company_id = serializers.UUIDField(required=True)
    
    def validate_company_id(self, value):
        user = self.context['request'].user
        
        # Check if user has access to this company
        if not user.has_company_access(Company.objects.get(id=value)):
            raise serializers.ValidationError(
                "You don't have access to this company."
            )
        
        return value

# ========================================
# RESPONSE SERIALIZERS
# ========================================

class AuthTokenSerializer(serializers.Serializer):
    """Serializer for authentication token response"""
    
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    token_type = serializers.CharField(default='Bearer')
    expires_in = serializers.IntegerField()
    user = UserSerializer()

class MessageSerializer(serializers.Serializer):
    """Generic message response serializer"""
    
    message = serializers.CharField()