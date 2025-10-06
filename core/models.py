# core/models.py
# Core authentication and multi-tenant models

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
import uuid

class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication"""
    
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model with email-based authentication"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    email_verified = models.BooleanField(default=False)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    objects = UserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    class Meta:
        db_table = 'core_user'
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def get_short_name(self):
        return self.first_name

class Company(models.Model):
    """Company model for multi-tenancy"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    domain = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core_company'
        verbose_name_plural = 'Companies'
    
    def __str__(self):
        return self.name

class CompanyIsolatedModel(models.Model):
    """Abstract base model for company-isolated data"""
    
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='%(class)s_set')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
    
    def save(self, *args, **kwargs):
        if not self.company_id:
            # Set company from request if available
            from django.contrib.auth import get_user_model
            User = get_user_model()
            if hasattr(self, '_request') and hasattr(self._request, 'user'):
                if self._request.user.is_authenticated:
                    # Get company from user's company access
                    company_access = UserCompanyAccess.objects.filter(user=self._request.user).first()
                    if company_access:
                        self.company = company_access.company
        super().save(*args, **kwargs)

class UserCompanyAccess(models.Model):
    """User access to companies"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='company_access')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='user_access')
    role = models.CharField(max_length=50, default='user')
    is_active = models.BooleanField(default=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'core_user_company_access'
        unique_together = ('user', 'company')
    
    def __str__(self):
        return f"{self.user.email} - {self.company.name}"

class UserSession(models.Model):
    """User session tracking"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'core_user_session'
    
    def __str__(self):
        return f"{self.user.email} - {self.session_key}"
    
    @property
    def is_valid(self):
        """Check if session is still valid"""
        return timezone.now() < self.expires_at

class AuditLog(models.Model):
    """Audit log for tracking important actions"""
    
    ACTION_CHOICES = [
        ('create', 'Create'),
        ('update', 'Update'),
        ('delete', 'Delete'),
        ('login', 'Login'),
        ('logout', 'Logout'),
        ('view', 'View'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    company = models.ForeignKey(Company, on_delete=models.SET_NULL, null=True, blank=True, related_name='audit_logs')
    object_type = models.CharField(max_length=100, blank=True)
    object_id = models.CharField(max_length=100, blank=True)
    details = models.JSONField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'core_audit_log'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.action} - {self.user.email if self.user else 'System'}"

# Import Phase 4+ permission and security models
from core.permissions_models import (
    Role, RoleFieldPermission, GDPRRegistry, 
    DataRetentionPolicy, MaskingAuditLog
)

__all__ = [
    'User', 'Company', 'CompanyIsolatedModel', 'UserCompanyAccess',
    'UserSession', 'AuditLog', 'Role', 'RoleFieldPermission',
    'GDPRRegistry', 'DataRetentionPolicy', 'MaskingAuditLog'
]

