# core/permissions_models.py
# Field-level permissions and security models for Phase 4+

from django.db import models
from django.contrib.auth import get_user_model
from core.models import CompanyIsolatedModel

User = get_user_model()

class Role(CompanyIsolatedModel):
    """Role definition for users"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    permissions = models.JSONField(
        default=dict,
        help_text="General permissions for this role"
    )
    
    class Meta:
        db_table = 'core_role'
        unique_together = ['company', 'name']
    
    def __str__(self):
        return self.name

class RoleFieldPermission(CompanyIsolatedModel):
    """Field-level permissions for roles"""
    
    MODE_CHOICES = [
        ('view', 'View - Full access'),
        ('mask', 'Mask - Show masked value'),
        ('hidden', 'Hidden - Field not visible'),
        ('edit', 'Edit - Can modify field'),
    ]
    
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        related_name='field_permissions'
    )
    object_type = models.CharField(
        max_length=100,
        help_text="Model name (e.g., 'lead', 'contact', 'deal')"
    )
    field_name = models.CharField(
        max_length=100,
        help_text="Field name on the model"
    )
    mode = models.CharField(
        max_length=10,
        choices=MODE_CHOICES,
        default='view',
        help_text="Permission mode for this field"
    )
    
    class Meta:
        db_table = 'core_role_field_permission'
        unique_together = ['role', 'object_type', 'field_name']
        indexes = [
            models.Index(fields=['object_type', 'field_name']),
            models.Index(fields=['role', 'object_type']),
        ]
    
    def __str__(self):
        return f"{self.role.name} - {self.object_type}.{self.field_name} ({self.mode})"

class GDPRRegistry(CompanyIsolatedModel):
    """GDPR data masking registry"""
    
    MASK_TYPES = [
        ('hash', 'Hash - One-way hash'),
        ('partial', 'Partial - Show partial data'),
        ('redact', 'Redact - Replace with [REDACTED]'),
        ('encrypt', 'Encrypt - Reversible encryption'),
        ('tokenize', 'Tokenize - Replace with token'),
    ]
    
    object_type = models.CharField(max_length=100)
    field_name = models.CharField(max_length=100)
    mask_type = models.CharField(
        max_length=20,
        choices=MASK_TYPES,
        default='redact'
    )
    mask_config = models.JSONField(
        default=dict,
        help_text="Masking configuration (e.g., how many chars to show)"
    )
    is_pii = models.BooleanField(
        default=True,
        help_text="Whether this field contains PII data"
    )
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'core_gdpr_registry'
        unique_together = ['company', 'object_type', 'field_name']
    
    def __str__(self):
        return f"{self.object_type}.{self.field_name} - {self.mask_type}"

class DataRetentionPolicy(CompanyIsolatedModel):
    """Data retention policy configuration"""
    
    object_type = models.CharField(max_length=100)
    retention_days = models.IntegerField(
        help_text="Number of days to retain data"
    )
    purge_strategy = models.CharField(
        max_length=50,
        default='soft_delete',
        help_text="Strategy for purging data (soft_delete, hard_delete, archive)"
    )
    is_active = models.BooleanField(default=True)
    last_purge_date = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'core_data_retention_policy'
        unique_together = ['company', 'object_type']
    
    def __str__(self):
        return f"{self.object_type} - {self.retention_days} days"

class MaskingAuditLog(CompanyIsolatedModel):
    """Audit log for field masking decisions"""
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='masking_audit_logs'
    )
    object_type = models.CharField(max_length=100)
    object_id = models.CharField(max_length=100)
    field_name = models.CharField(max_length=100)
    action = models.CharField(
        max_length=50,
        help_text="Action taken (masked, hidden, viewed)"
    )
    reason = models.TextField(blank=True)
    
    class Meta:
        db_table = 'core_masking_audit_log'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['object_type', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.action} on {self.object_type}.{self.field_name}"
