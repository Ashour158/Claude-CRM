# compliance/views.py
# API views for compliance features

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q

from .models import (
    CompliancePolicy, PolicyAuditLog, DataResidency,
    DataSubjectRequest, SecretVault, SecretAccessLog,
    AccessReview, StaleAccess, RetentionPolicy, RetentionLog
)
from .serializers import (
    CompliancePolicySerializer, PolicyAuditLogSerializer, DataResidencySerializer,
    DataSubjectRequestSerializer, SecretVaultSerializer, SecretVaultDetailSerializer,
    SecretAccessLogSerializer, AccessReviewSerializer, StaleAccessSerializer,
    RetentionPolicySerializer, RetentionLogSerializer
)


class CompliancePolicyViewSet(viewsets.ModelViewSet):
    """ViewSet for compliance policies"""
    
    serializer_class = CompliancePolicySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['policy_type', 'status', 'is_enforced']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'name', 'version']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return CompliancePolicy.objects.all()
        
        # Get user's companies
        from core.models import UserCompanyAccess
        user_companies = UserCompanyAccess.objects.filter(
            user=user, is_active=True
        ).values_list('company_id', flat=True)
        
        return CompliancePolicy.objects.filter(company_id__in=user_companies)
    
    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        """Validate policy configuration"""
        policy = self.get_object()
        
        # Validate policy configuration
        from .policy_validator import PolicyValidator
        validator = PolicyValidator()
        is_valid, errors = validator.validate(policy.policy_config)
        
        # Log validation
        PolicyAuditLog.objects.create(
            policy=policy,
            company=policy.company,
            action='validated',
            action_details={'valid': is_valid, 'errors': errors},
            performed_by=request.user,
            ip_address=self.get_client_ip(request)
        )
        
        return Response({
            'valid': is_valid,
            'errors': errors
        })
    
    @action(detail=True, methods=['post'])
    def dry_run(self, request, pk=None):
        """Perform dry-run impact analysis"""
        policy = self.get_object()
        
        # Analyze impact without applying
        from .policy_engine import PolicyEngine
        engine = PolicyEngine()
        impact = engine.analyze_impact(policy)
        
        # Log dry-run
        PolicyAuditLog.objects.create(
            policy=policy,
            company=policy.company,
            action='validated',
            action_details={'dry_run': True, 'impact': impact},
            entities_affected=impact.get('entities', []),
            records_affected=impact.get('total_records', 0),
            performed_by=request.user,
            ip_address=self.get_client_ip(request)
        )
        
        return Response(impact)
    
    @action(detail=True, methods=['post'])
    def apply(self, request, pk=None):
        """Apply policy"""
        policy = self.get_object()
        
        if policy.status == 'active' and policy.is_enforced:
            return Response(
                {'error': 'Policy is already active and enforced'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Apply policy
        from .policy_engine import PolicyEngine
        engine = PolicyEngine()
        result = engine.apply_policy(policy)
        
        # Update policy
        policy.status = 'active'
        policy.is_enforced = True
        policy.applied_at = timezone.now()
        policy.applied_by = request.user
        policy.save()
        
        # Log application
        PolicyAuditLog.objects.create(
            policy=policy,
            company=policy.company,
            action='applied',
            action_details=result,
            entities_affected=result.get('entities', []),
            records_affected=result.get('total_records', 0),
            performed_by=request.user,
            ip_address=self.get_client_ip(request)
        )
        
        return Response(result)
    
    @action(detail=True, methods=['post'])
    def rollback(self, request, pk=None):
        """Rollback policy to previous version"""
        policy = self.get_object()
        
        if not policy.previous_version_id:
            return Response(
                {'error': 'No previous version to rollback to'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Rollback logic
        from .policy_engine import PolicyEngine
        engine = PolicyEngine()
        result = engine.rollback_policy(policy)
        
        # Update policy
        policy.status = 'inactive'
        policy.is_enforced = False
        policy.save()
        
        # Log rollback
        PolicyAuditLog.objects.create(
            policy=policy,
            company=policy.company,
            action='rollback',
            action_details=result,
            performed_by=request.user,
            ip_address=self.get_client_ip(request)
        )
        
        return Response(result)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class PolicyAuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for policy audit logs (read-only)"""
    
    serializer_class = PolicyAuditLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['policy', 'action', 'performed_by']
    ordering_fields = ['created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return PolicyAuditLog.objects.all()
        
        from core.models import UserCompanyAccess
        user_companies = UserCompanyAccess.objects.filter(
            user=user, is_active=True
        ).values_list('company_id', flat=True)
        
        return PolicyAuditLog.objects.filter(company_id__in=user_companies)


class DataResidencyViewSet(viewsets.ModelViewSet):
    """ViewSet for data residency configuration"""
    
    serializer_class = DataResidencySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return DataResidency.objects.all()
        
        from core.models import UserCompanyAccess
        user_companies = UserCompanyAccess.objects.filter(
            user=user, is_active=True
        ).values_list('company_id', flat=True)
        
        return DataResidency.objects.filter(company_id__in=user_companies)


class DataSubjectRequestViewSet(viewsets.ModelViewSet):
    """ViewSet for data subject requests"""
    
    serializer_class = DataSubjectRequestSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['request_type', 'status']
    search_fields = ['subject_email', 'subject_name', 'request_id']
    ordering_fields = ['created_at', 'due_date']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return DataSubjectRequest.objects.all()
        
        from core.models import UserCompanyAccess
        user_companies = UserCompanyAccess.objects.filter(
            user=user, is_active=True
        ).values_list('company_id', flat=True)
        
        return DataSubjectRequest.objects.filter(company_id__in=user_companies)
    
    @action(detail=True, methods=['post'])
    def process(self, request, pk=None):
        """Process DSR request"""
        dsr = self.get_object()
        
        if dsr.status == 'completed':
            return Response(
                {'error': 'Request already completed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process request
        from .dsr_processor import DSRProcessor
        processor = DSRProcessor()
        result = processor.process_request(dsr, request.user)
        
        # Update DSR
        dsr.status = 'completed'
        dsr.processed_at = timezone.now()
        dsr.processed_by = request.user
        dsr.audit_data = result.get('audit_data', {})
        dsr.save()
        
        return Response(result)
    
    @action(detail=True, methods=['post'])
    def rollback(self, request, pk=None):
        """Rollback DSR processing"""
        dsr = self.get_object()
        
        if not dsr.can_rollback:
            return Response(
                {'error': 'Rollback not available for this request'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Rollback logic
        from .dsr_processor import DSRProcessor
        processor = DSRProcessor()
        result = processor.rollback_request(dsr)
        
        # Update DSR
        dsr.status = 'pending'
        dsr.save()
        
        return Response(result)


class SecretVaultViewSet(viewsets.ModelViewSet):
    """ViewSet for secret vault"""
    
    permission_classes = [IsAuthenticated]
    filterset_fields = ['secret_type', 'is_active', 'rotation_enabled']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'last_rotated']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return SecretVaultDetailSerializer
        return SecretVaultSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return SecretVault.objects.all()
        
        from core.models import UserCompanyAccess
        user_companies = UserCompanyAccess.objects.filter(
            user=user, is_active=True
        ).values_list('company_id', flat=True)
        
        return SecretVault.objects.filter(company_id__in=user_companies)
    
    @action(detail=True, methods=['post'])
    def rotate(self, request, pk=None):
        """Rotate secret"""
        secret = self.get_object()
        
        new_value = request.data.get('new_value')
        if not new_value:
            return Response(
                {'error': 'new_value is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Encrypt and update secret
        from .encryption import SecretEncryption
        encryption = SecretEncryption()
        encrypted_value = encryption.encrypt(new_value, secret.kms_key_id)
        
        secret.secret_value = encrypted_value
        secret.last_rotated = timezone.now()
        
        # Calculate next rotation
        if secret.rotation_enabled:
            from datetime import timedelta
            secret.next_rotation = timezone.now() + timedelta(days=secret.rotation_days)
        
        secret.save()
        
        # Log access
        SecretAccessLog.objects.create(
            secret=secret,
            company=secret.company,
            accessed_by=request.user,
            service_name='secret_rotation',
            ip_address=self.get_client_ip(request),
            success=True
        )
        
        return Response({'message': 'Secret rotated successfully'})
    
    @action(detail=True, methods=['get'])
    def reveal(self, request, pk=None):
        """Reveal decrypted secret (restricted)"""
        secret = self.get_object()
        
        # Decrypt secret
        from .encryption import SecretEncryption
        encryption = SecretEncryption()
        
        try:
            decrypted_value = encryption.decrypt(secret.secret_value, secret.kms_key_id)
            
            # Log access
            SecretAccessLog.objects.create(
                secret=secret,
                company=secret.company,
                accessed_by=request.user,
                service_name='api_reveal',
                ip_address=self.get_client_ip(request),
                success=True
            )
            
            return Response({'value': decrypted_value})
        except Exception as e:
            # Log failure
            SecretAccessLog.objects.create(
                secret=secret,
                company=secret.company,
                accessed_by=request.user,
                service_name='api_reveal',
                ip_address=self.get_client_ip(request),
                success=False,
                failure_reason=str(e)
            )
            
            return Response(
                {'error': 'Failed to decrypt secret'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class SecretAccessLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for secret access logs (read-only)"""
    
    serializer_class = SecretAccessLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['secret', 'accessed_by', 'success']
    ordering_fields = ['created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return SecretAccessLog.objects.all()
        
        from core.models import UserCompanyAccess
        user_companies = UserCompanyAccess.objects.filter(
            user=user, is_active=True
        ).values_list('company_id', flat=True)
        
        return SecretAccessLog.objects.filter(company_id__in=user_companies)


class AccessReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for access reviews"""
    
    serializer_class = AccessReviewSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status']
    ordering_fields = ['created_at', 'review_period_start']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return AccessReview.objects.all()
        
        from core.models import UserCompanyAccess
        user_companies = UserCompanyAccess.objects.filter(
            user=user, is_active=True
        ).values_list('company_id', flat=True)
        
        return AccessReview.objects.filter(company_id__in=user_companies)
    
    @action(detail=False, methods=['post'])
    def start_review(self, request):
        """Start a new access review"""
        from .access_review import AccessReviewEngine
        
        # Get user's company
        from core.models import UserCompanyAccess
        user_access = UserCompanyAccess.objects.filter(
            user=request.user, is_active=True
        ).first()
        
        if not user_access:
            return Response(
                {'error': 'No active company access found'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create and run review
        engine = AccessReviewEngine()
        review = engine.create_review(user_access.company)
        engine.run_review(review)
        
        serializer = self.get_serializer(review)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class StaleAccessViewSet(viewsets.ModelViewSet):
    """ViewSet for stale access records"""
    
    serializer_class = StaleAccessSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['access_review', 'user', 'is_resolved', 'resolution']
    ordering_fields = ['days_inactive', 'created_at']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return StaleAccess.objects.all()
        
        from core.models import UserCompanyAccess
        user_companies = UserCompanyAccess.objects.filter(
            user=user, is_active=True
        ).values_list('company_id', flat=True)
        
        return StaleAccess.objects.filter(company_id__in=user_companies)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve stale access"""
        stale = self.get_object()
        resolution = request.data.get('resolution', 'pending')
        
        if resolution not in ['revoked', 'retained', 'pending']:
            return Response(
                {'error': 'Invalid resolution value'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        stale.resolution = resolution
        stale.is_resolved = resolution != 'pending'
        stale.resolved_at = timezone.now() if stale.is_resolved else None
        stale.resolved_by = request.user if stale.is_resolved else None
        stale.save()
        
        serializer = self.get_serializer(stale)
        return Response(serializer.data)


class RetentionPolicyViewSet(viewsets.ModelViewSet):
    """ViewSet for retention policies"""
    
    serializer_class = RetentionPolicySerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['entity_type', 'is_active', 'deletion_method']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'retention_days']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return RetentionPolicy.objects.all()
        
        from core.models import UserCompanyAccess
        user_companies = UserCompanyAccess.objects.filter(
            user=user, is_active=True
        ).values_list('company_id', flat=True)
        
        return RetentionPolicy.objects.filter(company_id__in=user_companies)
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Execute retention policy"""
        policy = self.get_object()
        
        # Execute policy
        from .retention_engine import RetentionEngine
        engine = RetentionEngine()
        result = engine.execute_policy(policy)
        
        return Response(result)


class RetentionLogViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for retention logs (read-only)"""
    
    serializer_class = RetentionLogSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['policy']
    ordering_fields = ['execution_started']
    
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser:
            return RetentionLog.objects.all()
        
        from core.models import UserCompanyAccess
        user_companies = UserCompanyAccess.objects.filter(
            user=user, is_active=True
        ).values_list('company_id', flat=True)
        
        return RetentionLog.objects.filter(company_id__in=user_companies)
