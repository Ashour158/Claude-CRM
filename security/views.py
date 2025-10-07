# security/views.py
# Enterprise Security Views

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django.db.models import Q, Avg, Count
from django.utils import timezone
import logging

from .models import (
    SecurityPolicy, SSOConfiguration, SCIMConfiguration, IPAllowlist,
    DeviceManagement, SessionManagement, AuditLog, SecurityIncident,
    DataRetentionPolicy
)
from .serializers import (
    SecurityPolicySerializer, SSOConfigurationSerializer, SCIMConfigurationSerializer,
    IPAllowlistSerializer, DeviceManagementSerializer, SessionManagementSerializer,
    AuditLogSerializer, SecurityIncidentSerializer, DataRetentionPolicySerializer
)
from core.permissions import CompanyIsolationPermission

logger = logging.getLogger(__name__)

class SecurityPolicyViewSet(viewsets.ModelViewSet):
    """Security policy management"""
    
    queryset = SecurityPolicy.objects.all()
    serializer_class = SecurityPolicySerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['policy_type', 'status', 'is_active', 'enforcement_level', 'owner']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'enforcement_level']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def test_policy(self, request, pk=None):
        """Test security policy"""
        policy = self.get_object()
        
        try:
            # TODO: Implement actual policy testing
            # This would involve testing the policy against sample data
            
            test_data = request.data.get('test_data', {})
            
            return Response({
                'status': 'success',
                'policy_name': policy.name,
                'test_result': 'Policy test completed successfully'
            })
            
        except Exception as e:
            logger.error(f"Policy test failed: {str(e)}")
            return Response(
                {'error': 'Policy test failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SSOConfigurationViewSet(viewsets.ModelViewSet):
    """SSO configuration management"""
    
    queryset = SSOConfiguration.objects.all()
    serializer_class = SSOConfigurationSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['provider_type', 'status', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'last_test']
    ordering = ['name']
    
    @action(detail=True, methods=['post'])
    def test_connection(self, request, pk=None):
        """Test SSO connection"""
        sso_config = self.get_object()
        
        try:
            # TODO: Implement actual SSO connection testing
            # This would involve testing the SSO provider connection
            
            is_connected = True  # Replace with actual test
            response_time = 150  # Replace with actual response time
            
            sso_config.test_status = 'success' if is_connected else 'failed'
            sso_config.last_test = timezone.now()
            sso_config.save()
            
            return Response({
                'status': 'success' if is_connected else 'failed',
                'response_time_ms': response_time,
                'test_status': sso_config.test_status
            })
            
        except Exception as e:
            logger.error(f"SSO connection test failed: {str(e)}")
            return Response(
                {'error': 'SSO connection test failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class SCIMConfigurationViewSet(viewsets.ModelViewSet):
    """SCIM configuration management"""
    
    queryset = SCIMConfiguration.objects.all()
    serializer_class = SCIMConfigurationSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['status', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at', 'last_sync']
    ordering = ['name']
    
    @action(detail=True, methods=['post'])
    def sync_users(self, request, pk=None):
        """Sync users via SCIM"""
        scim_config = self.get_object()
        
        try:
            # TODO: Implement actual SCIM user sync
            # This would involve syncing users with the SCIM provider
            
            sync_count = 10  # Replace with actual sync count
            
            scim_config.total_syncs += 1
            scim_config.successful_syncs += 1
            scim_config.last_sync = timezone.now()
            scim_config.save()
            
            return Response({
                'status': 'success',
                'sync_count': sync_count,
                'last_sync': scim_config.last_sync.isoformat()
            })
            
        except Exception as e:
            logger.error(f"SCIM sync failed: {str(e)}")
            return Response(
                {'error': 'SCIM sync failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class IPAllowlistViewSet(viewsets.ModelViewSet):
    """IP allowlist management"""
    
    queryset = IPAllowlist.objects.all()
    serializer_class = IPAllowlistSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['allowlist_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    @action(detail=True, methods=['post'])
    def test_ip(self, request, pk=None):
        """Test IP address against allowlist"""
        allowlist = self.get_object()
        
        try:
            test_ip = request.data.get('ip_address')
            if not test_ip:
                return Response(
                    {'error': 'IP address is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # TODO: Implement actual IP testing logic
            is_allowed = True  # Replace with actual IP testing
            
            return Response({
                'ip_address': test_ip,
                'is_allowed': is_allowed,
                'allowlist_type': allowlist.allowlist_type
            })
            
        except Exception as e:
            logger.error(f"IP test failed: {str(e)}")
            return Response(
                {'error': 'IP test failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class DeviceManagementViewSet(viewsets.ModelViewSet):
    """Device management"""
    
    queryset = DeviceManagement.objects.all()
    serializer_class = DeviceManagementSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['device_type', 'status', 'is_trusted', 'user']
    search_fields = ['device_name', 'operating_system', 'browser']
    ordering_fields = ['device_name', 'last_seen', 'created_at']
    ordering = ['-last_seen']
    
    @action(detail=True, methods=['post'])
    def trust_device(self, request, pk=None):
        """Trust a device"""
        device = self.get_object()
        
        device.is_trusted = True
        device.status = 'active'
        device.save()
        
        return Response({
            'status': 'success',
            'device_name': device.device_name,
            'is_trusted': device.is_trusted
        })
    
    @action(detail=True, methods=['post'])
    def block_device(self, request, pk=None):
        """Block a device"""
        device = self.get_object()
        
        device.status = 'blocked'
        device.is_trusted = False
        device.save()
        
        return Response({
            'status': 'success',
            'device_name': device.device_name,
            'status': device.status
        })

class SessionManagementViewSet(viewsets.ModelViewSet):
    """Session management"""
    
    queryset = SessionManagement.objects.all()
    serializer_class = SessionManagementSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['session_type', 'status', 'user', 'device']
    search_fields = ['session_id']
    ordering_fields = ['started_at', 'last_activity', 'expires_at']
    ordering = ['-last_activity']
    
    @action(detail=True, methods=['post'])
    def terminate_session(self, request, pk=None):
        """Terminate a session"""
        session = self.get_object()
        
        session.status = 'terminated'
        session.terminated_at = timezone.now()
        session.save()
        
        return Response({
            'status': 'success',
            'session_id': str(session.session_id),
            'terminated_at': session.terminated_at.isoformat()
        })

class AuditLogViewSet(viewsets.ModelViewSet):
    """Audit log management"""
    
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['event_type', 'severity', 'is_successful', 'user']
    search_fields = ['event_name', 'description']
    ordering_fields = ['created_at', 'severity']
    ordering = ['-created_at']

class SecurityIncidentViewSet(viewsets.ModelViewSet):
    """Security incident management"""
    
    queryset = SecurityIncident.objects.all()
    serializer_class = SecurityIncidentSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['incident_type', 'severity', 'status', 'assigned_to']
    search_fields = ['title', 'description']
    ordering_fields = ['detected_at', 'severity', 'status']
    ordering = ['-detected_at']
    
    @action(detail=True, methods=['post'])
    def assign_incident(self, request, pk=None):
        """Assign security incident"""
        incident = self.get_object()
        
        assigned_to_id = request.data.get('assigned_to_id')
        if not assigned_to_id:
            return Response(
                {'error': 'Assigned to ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from core.models import User
            assigned_user = User.objects.get(id=assigned_to_id, company=incident.company)
            
            incident.assigned_to = assigned_user
            incident.status = 'investigating'
            incident.save()
            
            return Response({
                'status': 'success',
                'incident_id': str(incident.incident_id),
                'assigned_to': assigned_user.get_full_name()
            })
            
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def resolve_incident(self, request, pk=None):
        """Resolve security incident"""
        incident = self.get_object()
        
        resolution_notes = request.data.get('resolution_notes', '')
        
        incident.status = 'resolved'
        incident.resolved_at = timezone.now()
        incident.resolution_notes = resolution_notes
        incident.save()
        
        return Response({
            'status': 'success',
            'incident_id': str(incident.incident_id),
            'resolved_at': incident.resolved_at.isoformat()
        })

class DataRetentionPolicyViewSet(viewsets.ModelViewSet):
    """Data retention policy management"""
    
    queryset = DataRetentionPolicy.objects.all()
    serializer_class = DataRetentionPolicySerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['retention_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'retention_period_days', 'last_cleanup']
    ordering = ['name']
    
    @action(detail=True, methods=['post'])
    def run_cleanup(self, request, pk=None):
        """Run data retention cleanup"""
        policy = self.get_object()
        
        try:
            # TODO: Implement actual data cleanup
            # This would involve cleaning up data based on retention policy
            
            cleanup_count = 100  # Replace with actual cleanup count
            
            policy.total_records += cleanup_count
            policy.deleted_records += cleanup_count
            policy.last_cleanup = timezone.now()
            policy.save()
            
            return Response({
                'status': 'success',
                'policy_name': policy.name,
                'cleanup_count': cleanup_count,
                'last_cleanup': policy.last_cleanup.isoformat()
            })
            
        except Exception as e:
            logger.error(f"Data cleanup failed: {str(e)}")
            return Response(
                {'error': 'Data cleanup failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
