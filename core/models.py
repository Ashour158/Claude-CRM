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


# ========================================
# SAVED VIEWS MODEL
# ========================================

class SavedListView(models.Model):
    """Saved list views for entities with filters, columns, and sorting."""
    
    ENTITY_TYPE_CHOICES = [
        ('account', 'Account'),
        ('contact', 'Contact'),
        ('lead', 'Lead'),
        ('deal', 'Deal'),
        ('activity', 'Activity'),
        ('product', 'Product'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='saved_views')
    owner = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='saved_views',
        help_text="Owner of the view. Null means shared/public view."
    )
    entity_type = models.CharField(
        max_length=50,
        choices=ENTITY_TYPE_CHOICES,
        db_index=True,
        help_text="Type of entity this view is for"
    )
    name = models.CharField(max_length=255, help_text="Name of the saved view")
    definition = models.JSONField(
        help_text="View definition including filters, columns, and sort"
    )
    is_private = models.BooleanField(
        default=True,
        help_text="Whether this view is private to the owner"
    )
    
    # Soft Delete
    is_active = models.BooleanField(default=True, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core_saved_list_view'
        ordering = ['entity_type', 'name']
        unique_together = [('organization', 'entity_type', 'name', 'owner')]
        indexes = [
            models.Index(fields=['entity_type']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        owner_str = f" - {self.owner.email}" if self.owner else " (Shared)"
        return f"{self.name} ({self.entity_type}){owner_str}"
    
    def soft_delete(self):
        """Soft delete the saved view."""
        self.is_active = False
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_active', 'deleted_at'])


# ========================================
# CUSTOM FIELD VALUE MODEL (Relational Layer)
# ========================================

class CustomFieldValue(models.Model):
    """Relational storage for custom field values (dual-write with JSON)."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='custom_field_values')
    
    # Custom field reference
    custom_field_id = models.UUIDField(help_text="Reference to CustomField")
    custom_field_name = models.CharField(max_length=255, db_index=True)
    
    # Entity reference (generic)
    entity_type = models.CharField(max_length=50, db_index=True)
    entity_id = models.UUIDField(db_index=True)
    
    # Typed value columns
    value_text = models.TextField(null=True, blank=True)
    value_number = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    value_date = models.DateField(null=True, blank=True)
    value_datetime = models.DateTimeField(null=True, blank=True)
    value_boolean = models.BooleanField(null=True, blank=True)
    value_select = models.CharField(max_length=255, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'core_custom_field_value'
        unique_together = [('company', 'custom_field_id', 'entity_type', 'entity_id')]
        indexes = [
            models.Index(fields=['entity_type', 'entity_id']),
            models.Index(fields=['custom_field_name']),
        ]
    
    def __str__(self):
        return f"{self.custom_field_name} for {self.entity_type}:{self.entity_id}"


# ========================================
# TIMELINE EVENT MODEL
# ========================================

class TimelineEvent(models.Model):
    """Timeline events for tracking entity history."""
    
    EVENT_TYPE_CHOICES = [
        ('create', 'Created'),
        ('update', 'Updated'),
        ('delete', 'Deleted'),
        ('stage_change', 'Stage Changed'),
        ('status_change', 'Status Changed'),
        ('assignment', 'Assigned'),
        ('note', 'Note Added'),
        ('call', 'Call Logged'),
        ('email', 'Email Sent'),
        ('meeting', 'Meeting Scheduled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='timeline_events')
    
    # Event details
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES, db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Entity reference (generic)
    entity_type = models.CharField(max_length=50, db_index=True)
    entity_id = models.UUIDField(db_index=True)
    
    # Actor
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='timeline_events')
    
    # Additional data
    metadata = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'core_timeline_event'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['entity_type', 'entity_id', '-created_at']),
            models.Index(fields=['event_type']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.title}"
