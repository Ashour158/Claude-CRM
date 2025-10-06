# sharing/models.py
# Sharing enforcement models

from django.db import models
from django.contrib.auth import get_user_model
from core.models import Company
import uuid

User = get_user_model()


class SharingRule(models.Model):
    """
    Predicate-based sharing rules for automatic record access.
    Rules are aggregated with OR semantics.
    """
    
    ACCESS_LEVEL_CHOICES = [
        ('read_only', 'Read Only'),
        ('read_write', 'Read/Write'),
    ]
    
    OBJECT_TYPE_CHOICES = [
        ('lead', 'Lead'),
        ('deal', 'Deal'),
        ('account', 'Account'),
        ('contact', 'Contact'),
        ('activity', 'Activity'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='sharing_rules',
        help_text="Company this rule belongs to"
    )
    
    # Rule identification
    name = models.CharField(max_length=255, help_text="Human-readable rule name")
    description = models.TextField(blank=True, help_text="Rule description")
    
    # Rule configuration
    object_type = models.CharField(
        max_length=50,
        choices=OBJECT_TYPE_CHOICES,
        db_index=True,
        help_text="Type of object this rule applies to"
    )
    predicate = models.JSONField(
        help_text="JSON predicate defining rule conditions. Format: {'field': 'status', 'operator': 'eq', 'value': 'qualified'}"
    )
    access_level = models.CharField(
        max_length=20,
        choices=ACCESS_LEVEL_CHOICES,
        default='read_only',
        help_text="Access level granted by this rule"
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether this rule is currently active"
    )
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_sharing_rules'
    )
    
    class Meta:
        db_table = 'sharing_rule'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['company', 'object_type', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.object_type})"


class RecordShare(models.Model):
    """
    Explicit record-level sharing.
    Grants specific users access to specific records.
    """
    
    ACCESS_LEVEL_CHOICES = [
        ('read_only', 'Read Only'),
        ('read_write', 'Read/Write'),
    ]
    
    OBJECT_TYPE_CHOICES = [
        ('lead', 'Lead'),
        ('deal', 'Deal'),
        ('account', 'Account'),
        ('contact', 'Contact'),
        ('activity', 'Activity'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='record_shares',
        help_text="Company this share belongs to"
    )
    
    # Share configuration
    object_type = models.CharField(
        max_length=50,
        choices=OBJECT_TYPE_CHOICES,
        db_index=True,
        help_text="Type of object being shared"
    )
    object_id = models.UUIDField(
        db_index=True,
        help_text="ID of the specific record being shared"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='record_shares',
        help_text="User being granted access"
    )
    access_level = models.CharField(
        max_length=20,
        choices=ACCESS_LEVEL_CHOICES,
        default='read_only',
        help_text="Access level granted"
    )
    
    # Optional reason
    reason = models.TextField(blank=True, help_text="Reason for sharing")
    
    # Audit fields
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_record_shares'
    )
    
    class Meta:
        db_table = 'record_share'
        ordering = ['-created_at']
        unique_together = ('company', 'object_type', 'object_id', 'user')
        indexes = [
            models.Index(fields=['company', 'object_type', 'object_id']),
            models.Index(fields=['company', 'user']),
        ]
    
    def __str__(self):
        return f"{self.object_type}:{self.object_id} -> {self.user.email} ({self.access_level})"
