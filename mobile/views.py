# mobile/views.py
# Mobile Application Views

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
    MobileDevice, MobileSession, OfflineData, PushNotification,
    MobileAppConfig, MobileAnalytics, MobileCrash
)
from .serializers import (
    MobileDeviceSerializer, MobileSessionSerializer, OfflineDataSerializer,
    PushNotificationSerializer, MobileAppConfigSerializer, MobileAnalyticsSerializer,
    MobileCrashSerializer
)
from core.permissions import CompanyIsolationPermission

logger = logging.getLogger(__name__)

class MobileDeviceViewSet(viewsets.ModelViewSet):
    """Mobile device management"""
    
    queryset = MobileDevice.objects.all()
    serializer_class = MobileDeviceSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['device_type', 'status', 'is_trusted', 'user']
    search_fields = ['device_name', 'operating_system', 'browser']
    ordering_fields = ['device_name', 'last_seen', 'total_sessions']
    ordering = ['-last_seen']
    
    @action(detail=True, methods=['post'])
    def register_device(self, request, pk=None):
        """Register a mobile device"""
        try:
            device_data = request.data
            
            device = MobileDevice.objects.create(
                device_name=device_data.get('device_name', 'Unknown Device'),
                device_type=device_data.get('device_type', 'mobile'),
                operating_system=device_data.get('operating_system', ''),
                os_version=device_data.get('os_version', ''),
                app_version=device_data.get('app_version', '1.0.0'),
                device_model=device_data.get('device_model', ''),
                manufacturer=device_data.get('manufacturer', ''),
                user=request.user,
                push_token=device_data.get('push_token', ''),
                fingerprint=device_data.get('fingerprint', ''),
                app_config=device_data.get('app_config', {}),
                user_preferences=device_data.get('user_preferences', {})
            )
            
            return Response({
                'status': 'success',
                'device_id': str(device.device_id),
                'device_name': device.device_name
            })
            
        except Exception as e:
            logger.error(f"Device registration failed: {str(e)}")
            return Response(
                {'error': 'Device registration failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
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

class MobileSessionViewSet(viewsets.ModelViewSet):
    """Mobile session management"""
    
    queryset = MobileSession.objects.all()
    serializer_class = MobileSessionSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['session_type', 'status', 'user', 'device']
    search_fields = ['session_id']
    ordering_fields = ['started_at', 'last_activity', 'expires_at']
    ordering = ['-last_activity']
    
    @action(detail=True, methods=['post'])
    def end_session(self, request, pk=None):
        """End a mobile session"""
        session = self.get_object()
        
        session.status = 'terminated'
        session.ended_at = timezone.now()
        session.save()
        
        return Response({
            'status': 'success',
            'session_id': str(session.session_id),
            'ended_at': session.ended_at.isoformat()
        })

class OfflineDataViewSet(viewsets.ModelViewSet):
    """Offline data management"""
    
    queryset = OfflineData.objects.all()
    serializer_class = OfflineDataSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['device', 'session', 'sync_type', 'status']
    search_fields = ['entity_type']
    ordering_fields = ['created_at', 'synced_at', 'last_modified']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def sync_data(self, request, pk=None):
        """Sync offline data"""
        offline_data = self.get_object()
        
        try:
            # TODO: Implement actual data synchronization
            # This would involve syncing the offline data with the server
            
            offline_data.status = 'syncing'
            offline_data.save()
            
            # Simulate sync completion
            offline_data.status = 'completed'
            offline_data.synced_at = timezone.now()
            offline_data.save()
            
            return Response({
                'status': 'success',
                'entity_type': offline_data.entity_type,
                'entity_id': str(offline_data.entity_id),
                'synced_at': offline_data.synced_at.isoformat()
            })
            
        except Exception as e:
            offline_data.status = 'failed'
            offline_data.save()
            
            logger.error(f"Data sync failed: {str(e)}")
            return Response(
                {'error': 'Data sync failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class PushNotificationViewSet(viewsets.ModelViewSet):
    """Push notification management"""
    
    queryset = PushNotification.objects.all()
    serializer_class = PushNotificationSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['notification_type', 'status']
    search_fields = ['title', 'message']
    ordering_fields = ['created_at', 'scheduled_at', 'sent_at']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def send_notification(self, request, pk=None):
        """Send push notification"""
        notification = self.get_object()
        
        try:
            # TODO: Implement actual push notification sending
            # This would involve sending the notification to the target devices
            
            notification.status = 'sent'
            notification.sent_at = timezone.now()
            notification.total_sent = notification.devices.count()
            notification.save()
            
            return Response({
                'status': 'success',
                'notification_id': str(notification.id),
                'total_sent': notification.total_sent,
                'sent_at': notification.sent_at.isoformat()
            })
            
        except Exception as e:
            notification.status = 'failed'
            notification.save()
            
            logger.error(f"Push notification failed: {str(e)}")
            return Response(
                {'error': 'Push notification failed'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class MobileAppConfigViewSet(viewsets.ModelViewSet):
    """Mobile app configuration management"""
    
    queryset = MobileAppConfig.objects.all()
    serializer_class = MobileAppConfigSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['config_type', 'is_active', 'is_required']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'effective_from', 'effective_until']
    ordering = ['config_type', 'name']

class MobileAnalyticsViewSet(viewsets.ModelViewSet):
    """Mobile analytics management"""
    
    queryset = MobileAnalytics.objects.all()
    serializer_class = MobileAnalyticsSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['device', 'session', 'metric_type']
    search_fields = ['metric_name', 'action_name']
    ordering_fields = ['timestamp', 'metric_value']
    ordering = ['-timestamp']

class MobileCrashViewSet(viewsets.ModelViewSet):
    """Mobile crash management"""
    
    queryset = MobileCrash.objects.all()
    serializer_class = MobileCrashSerializer
    permission_classes = [IsAuthenticated, CompanyIsolationPermission]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['device', 'session', 'severity', 'status', 'assigned_to']
    search_fields = ['error_type', 'error_message', 'device__device_name']
    ordering_fields = ['created_at', 'severity']
    ordering = ['-created_at']
    
    @action(detail=True, methods=['post'])
    def assign_crash(self, request, pk=None):
        """Assign crash to developer"""
        crash = self.get_object()
        
        assigned_to_id = request.data.get('assigned_to_id')
        if not assigned_to_id:
            return Response(
                {'error': 'Assigned to ID is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            from core.models import User
            assigned_user = User.objects.get(id=assigned_to_id, company=crash.company)
            
            crash.assigned_to = assigned_user
            crash.status = 'investigating'
            crash.save()
            
            return Response({
                'status': 'success',
                'crash_id': str(crash.crash_id),
                'assigned_to': assigned_user.get_full_name()
            })
            
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
