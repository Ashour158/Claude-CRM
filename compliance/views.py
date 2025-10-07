# compliance/views.py
# Compliance Views

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.utils import timezone

from .models import CompliancePolicy, DataRetentionRule, AccessReview, DataSubjectRequest, ComplianceViolation
from .serializers import (
    CompliancePolicySerializer, DataRetentionRuleSerializer, AccessReviewSerializer,
    DataSubjectRequestSerializer, ComplianceViolationSerializer
)

class CompliancePolicyViewSet(viewsets.ModelViewSet):
    """Compliance policy management"""
    
    queryset = CompliancePolicy.objects.all()
    serializer_class = CompliancePolicySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['policy_type', 'compliance_standard', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'priority', 'created_at']
    ordering = ['priority', '-created_at']
    
    def get_queryset(self):
        """Filter by company"""
        return self.queryset.filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        """Set company and created_by"""
        serializer.save(
            company=self.request.user.company,
            created_by=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate compliance policy"""
        policy = self.get_object()
        policy.is_active = True
        policy.save()
        
        return Response({'message': f'Policy {policy.name} activated'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """Deactivate compliance policy"""
        policy = self.get_object()
        policy.is_active = False
        policy.save()
        
        return Response({'message': f'Policy {policy.name} deactivated'})

class DataRetentionRuleViewSet(viewsets.ModelViewSet):
    """Data retention rule management"""
    
    queryset = DataRetentionRule.objects.all()
    serializer_class = DataRetentionRuleSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['policy', 'retention_type', 'is_active']
    search_fields = ['name', 'description', 'target_model']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        """Filter by company"""
        return self.queryset.filter(policy__company=self.request.user.company)
    
    @action(detail=True, methods=['post'])
    def execute(self, request, pk=None):
        """Execute retention rule"""
        rule = self.get_object()
        
        if not rule.is_active:
            return Response(
                {'error': 'Rule is not active'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update execution timestamps
        rule.last_executed = timezone.now()
        rule.next_execution = timezone.now() + rule.retention_period
        rule.save()
        
        # Execute retention logic (implement actual retention processing)
        
        return Response({'message': f'Retention rule {rule.name} executed'})

class AccessReviewViewSet(viewsets.ModelViewSet):
    """Access review management"""
    
    queryset = AccessReview.objects.all()
    serializer_class = AccessReviewSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['review_type', 'status', 'compliance_policy']
    search_fields = ['name', 'description']
    ordering_fields = ['due_date', 'created_at']
    ordering = ['-due_date']
    
    def get_queryset(self):
        """Filter by company"""
        return self.queryset.filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        """Set company and created_by"""
        serializer.save(
            company=self.request.user.company,
            created_by=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def start_review(self, request, pk=None):
        """Start access review"""
        review = self.get_object()
        
        if review.status != 'pending':
            return Response(
                {'error': 'Review is not in pending status'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        review.status = 'in_progress'
        review.save()
        
        return Response({'message': f'Access review {review.name} started'})
    
    @action(detail=True, methods=['post'])
    def complete_review(self, request, pk=None):
        """Complete access review"""
        review = self.get_object()
        
        if review.status != 'in_progress':
            return Response(
                {'error': 'Review is not in progress'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        review.status = 'completed'
        review.completion_date = timezone.now().date()
        review.progress_percentage = 100
        review.save()
        
        return Response({'message': f'Access review {review.name} completed'})

class DataSubjectRequestViewSet(viewsets.ModelViewSet):
    """Data subject request management"""
    
    queryset = DataSubjectRequest.objects.all()
    serializer_class = DataSubjectRequestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['request_type', 'status', 'priority', 'assigned_to']
    search_fields = ['subject_name', 'subject_email', 'description']
    ordering_fields = ['received_date', 'due_date', 'completed_date']
    ordering = ['-received_date']
    
    def get_queryset(self):
        """Filter by company"""
        return self.queryset.filter(company=self.request.user.company)
    
    @action(detail=True, methods=['post'])
    def assign(self, request, pk=None):
        """Assign DSR to user"""
        dsr = self.get_object()
        assigned_to_id = request.data.get('assigned_to_id')
        
        if not assigned_to_id:
            return Response(
                {'error': 'assigned_to_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            assigned_user = User.objects.get(id=assigned_to_id)
            dsr.assigned_to = assigned_user
            dsr.save()
            
            return Response({'message': f'DSR assigned to {assigned_user.get_full_name()}'})
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete DSR"""
        dsr = self.get_object()
        
        if dsr.status != 'in_progress':
            return Response(
                {'error': 'DSR is not in progress'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        dsr.status = 'completed'
        dsr.completed_date = timezone.now()
        dsr.response_date = timezone.now()
        dsr.save()
        
        return Response({'message': f'DSR {dsr.request_type} completed'})

class ComplianceViolationViewSet(viewsets.ModelViewSet):
    """Compliance violation management"""
    
    queryset = ComplianceViolation.objects.all()
    serializer_class = ComplianceViolationSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['violation_type', 'severity', 'is_resolved', 'policy']
    search_fields = ['title', 'description']
    ordering_fields = ['discovered_date', 'incident_date', 'severity']
    ordering = ['-discovered_date']
    
    def get_queryset(self):
        """Filter by company"""
        return self.queryset.filter(company=self.request.user.company)
    
    def perform_create(self, serializer):
        """Set company and reported_by"""
        serializer.save(
            company=self.request.user.company,
            reported_by=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Resolve compliance violation"""
        violation = self.get_object()
        
        if violation.is_resolved:
            return Response(
                {'error': 'Violation is already resolved'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        resolution_notes = request.data.get('resolution_notes', '')
        
        violation.is_resolved = True
        violation.resolution_date = timezone.now()
        violation.resolution_notes = resolution_notes
        violation.save()
        
        return Response({'message': f'Violation {violation.title} resolved'})
    
    @action(detail=True, methods=['post'])
    def notify_authority(self, request, pk=None):
        """Notify regulatory authority"""
        violation = self.get_object()
        
        authority = request.data.get('authority', '')
        
        violation.regulatory_notification = True
        violation.notification_date = timezone.now()
        violation.notification_authority = authority
        violation.save()
        
        return Response({'message': f'Regulatory authority notified: {authority}'})
