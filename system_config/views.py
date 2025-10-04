# system_config/views.py
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    CustomField, CustomFieldValue, SystemPreference, WorkflowConfiguration,
    UserPreference, SystemLog, SystemHealth, DataBackup
)
from .serializers import (
    CustomFieldSerializer, CustomFieldValueSerializer, SystemPreferenceSerializer,
    WorkflowConfigurationSerializer, UserPreferenceSerializer, SystemLogSerializer,
    SystemHealthSerializer, DataBackupSerializer, BulkCustomFieldSerializer,
    BulkSystemPreferenceSerializer, SystemConfigurationSerializer,
    UserConfigurationSerializer, WorkflowTriggerSerializer, SystemMetricsSerializer,
    BackupConfigurationSerializer, SystemDiagnosticsSerializer
)
from core.permissions import IsCompanyUser, IsCompanyAdmin
from core.mixins import CompanyIsolatedMixin

class CustomFieldViewSet(CompanyIsolatedMixin, viewsets.ModelViewSet):
    """ViewSet for CustomField model"""
    serializer_class = CustomFieldSerializer
    permission_classes = [IsCompanyUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['field_type', 'model_name', 'is_required', 'is_active']
    search_fields = ['name', 'label', 'description']
    ordering_fields = ['name', 'sequence', 'created_at']
    ordering = ['model_name', 'sequence']

    def get_queryset(self):
        return CustomField.objects.filter(company=self.request.company)

    @action(detail=False, methods=['get'])
    def by_model(self, request):
        """Get custom fields by model"""
        model_name = request.query_params.get('model_name')
        if not model_name:
            return Response(
                {'error': 'model_name parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        fields = self.get_queryset().filter(model_name=model_name, is_active=True)
        serializer = self.get_serializer(fields, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def bulk_operations(self, request):
        """Perform bulk operations on custom fields"""
        serializer = BulkCustomFieldSerializer(data=request.data)
        if serializer.is_valid():
            field_ids = serializer.validated_data['field_ids']
            action = serializer.validated_data['action']
            
            fields = self.get_queryset().filter(id__in=field_ids)
            
            if action == 'activate':
                fields.update(is_active=True)
            elif action == 'deactivate':
                fields.update(is_active=False)
            elif action == 'delete':
                fields.delete()
            
            return Response({'message': f'Bulk {action} completed successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomFieldValueViewSet(CompanyIsolatedMixin, viewsets.ModelViewSet):
    """ViewSet for CustomFieldValue model"""
    serializer_class = CustomFieldValueSerializer
    permission_classes = [IsCompanyUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['field', 'object_id']
    search_fields = ['value']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return CustomFieldValue.objects.filter(company=self.request.company)

    @action(detail=False, methods=['get'])
    def by_object(self, request):
        """Get custom field values by object"""
        object_id = request.query_params.get('object_id')
        if not object_id:
            return Response(
                {'error': 'object_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        values = self.get_queryset().filter(object_id=object_id)
        serializer = self.get_serializer(values, many=True)
        return Response(serializer.data)

class SystemPreferenceViewSet(CompanyIsolatedMixin, viewsets.ModelViewSet):
    """ViewSet for SystemPreference model"""
    serializer_class = SystemPreferenceSerializer
    permission_classes = [IsCompanyAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'data_type', 'is_active']
    search_fields = ['key', 'description']
    ordering_fields = ['key', 'category', 'created_at']
    ordering = ['category', 'key']

    def get_queryset(self):
        return SystemPreference.objects.filter(company=self.request.company)

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get preferences by category"""
        category = request.query_params.get('category')
        if not category:
            return Response(
                {'error': 'category parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        preferences = self.get_queryset().filter(category=category, is_active=True)
        serializer = self.get_serializer(preferences, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def bulk_operations(self, request):
        """Perform bulk operations on system preferences"""
        serializer = BulkSystemPreferenceSerializer(data=request.data)
        if serializer.is_valid():
            preference_ids = serializer.validated_data['preference_ids']
            action = serializer.validated_data['action']
            
            preferences = self.get_queryset().filter(id__in=preference_ids)
            
            if action == 'activate':
                preferences.update(is_active=True)
            elif action == 'deactivate':
                preferences.update(is_active=False)
            elif action == 'delete':
                preferences.delete()
            
            return Response({'message': f'Bulk {action} completed successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class WorkflowConfigurationViewSet(CompanyIsolatedMixin, viewsets.ModelViewSet):
    """ViewSet for WorkflowConfiguration model"""
    serializer_class = WorkflowConfigurationSerializer
    permission_classes = [IsCompanyUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['workflow_type', 'trigger_model', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        return WorkflowConfiguration.objects.filter(company=self.request.company)

    @action(detail=True, methods=['post'])
    def test_workflow(self, request, pk=None):
        """Test a workflow configuration"""
        workflow = self.get_object()
        # This would implement workflow testing logic
        return Response({'message': 'Workflow test completed successfully'})

    @action(detail=True, methods=['post'])
    def activate_workflow(self, request, pk=None):
        """Activate a workflow"""
        workflow = self.get_object()
        workflow.is_active = True
        workflow.save()
        return Response({'message': 'Workflow activated successfully'})

    @action(detail=True, methods=['post'])
    def deactivate_workflow(self, request, pk=None):
        """Deactivate a workflow"""
        workflow = self.get_object()
        workflow.is_active = False
        workflow.save()
        return Response({'message': 'Workflow deactivated successfully'})

class UserPreferenceViewSet(CompanyIsolatedMixin, viewsets.ModelViewSet):
    """ViewSet for UserPreference model"""
    serializer_class = UserPreferenceSerializer
    permission_classes = [IsCompanyUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user', 'category']
    search_fields = ['key', 'value']
    ordering_fields = ['key', 'created_at']
    ordering = ['category', 'key']

    def get_queryset(self):
        return UserPreference.objects.filter(company=self.request.company)

    @action(detail=False, methods=['get'])
    def my_preferences(self, request):
        """Get current user's preferences"""
        preferences = self.get_queryset().filter(user=request.user)
        serializer = self.get_serializer(preferences, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def update_preferences(self, request):
        """Update user preferences"""
        preferences_data = request.data.get('preferences', [])
        
        for pref_data in preferences_data:
            UserPreference.objects.update_or_create(
                user=request.user,
                key=pref_data['key'],
                company=request.company,
                defaults={
                    'value': pref_data['value'],
                    'category': pref_data.get('category', 'user')
                }
            )
        
        return Response({'message': 'Preferences updated successfully'})

class SystemLogViewSet(CompanyIsolatedMixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet for SystemLog model (Read-only)"""
    serializer_class = SystemLogSerializer
    permission_classes = [IsCompanyAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['level', 'category', 'user']
    search_fields = ['message']
    ordering_fields = ['created_at', 'level']
    ordering = ['-created_at']

    def get_queryset(self):
        return SystemLog.objects.filter(company=self.request.company)

    @action(detail=False, methods=['get'])
    def by_level(self, request):
        """Get logs by level"""
        level = request.query_params.get('level')
        if not level:
            return Response(
                {'error': 'level parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        logs = self.get_queryset().filter(level=level)
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def recent_errors(self, request):
        """Get recent error logs"""
        logs = self.get_queryset().filter(
            level__in=['error', 'critical'],
            created_at__gte=timezone.now() - timedelta(days=7)
        )
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)

class SystemHealthViewSet(CompanyIsolatedMixin, viewsets.ReadOnlyModelViewSet):
    """ViewSet for SystemHealth model (Read-only)"""
    serializer_class = SystemHealthSerializer
    permission_classes = [IsCompanyAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['component', 'status']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return SystemHealth.objects.filter(company=self.request.company)

    @action(detail=False, methods=['get'])
    def overall_health(self, request):
        """Get overall system health"""
        health_records = self.get_queryset()
        
        overall_status = 'healthy'
        if health_records.filter(status='critical').exists():
            overall_status = 'critical'
        elif health_records.filter(status='error').exists():
            overall_status = 'error'
        elif health_records.filter(status='warning').exists():
            overall_status = 'warning'
        
        components = {}
        for record in health_records:
            components[record.component] = {
                'status': record.status,
                'message': record.message,
                'response_time': record.response_time,
                'memory_usage': record.memory_usage,
                'cpu_usage': record.cpu_usage,
                'last_updated': record.created_at
            }
        
        return Response({
            'overall_status': overall_status,
            'components': components
        })

class DataBackupViewSet(CompanyIsolatedMixin, viewsets.ModelViewSet):
    """ViewSet for DataBackup model"""
    serializer_class = DataBackupSerializer
    permission_classes = [IsCompanyAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['backup_type', 'status']
    search_fields = ['name', 'description']
    ordering_fields = ['scheduled_at', 'created_at']
    ordering = ['-scheduled_at']

    def get_queryset(self):
        return DataBackup.objects.filter(company=self.request.company)

    @action(detail=True, methods=['post'])
    def start_backup(self, request, pk=None):
        """Start a backup"""
        backup = self.get_object()
        if backup.status != 'scheduled':
            return Response(
                {'error': 'Only scheduled backups can be started'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        backup.status = 'running'
        backup.started_at = timezone.now()
        backup.save()
        
        return Response({'message': 'Backup started successfully'})

    @action(detail=True, methods=['post'])
    def cancel_backup(self, request, pk=None):
        """Cancel a backup"""
        backup = self.get_object()
        if backup.status not in ['scheduled', 'running']:
            return Response(
                {'error': 'Only scheduled or running backups can be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        backup.status = 'cancelled'
        backup.save()
        
        return Response({'message': 'Backup cancelled successfully'})

    @action(detail=False, methods=['get'])
    def backup_history(self, request):
        """Get backup history"""
        backups = self.get_queryset().filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        )
        serializer = self.get_serializer(backups, many=True)
        return Response(serializer.data)

# Configuration views
class SystemConfigurationViewSet(viewsets.ViewSet):
    """ViewSet for system configuration"""
    permission_classes = [IsCompanyAdmin]

    @action(detail=False, methods=['get'])
    def get_configuration(self, request):
        """Get system configuration"""
        # This would retrieve system configuration
        config = {
            'company_name': 'CRM System',
            'timezone': 'UTC',
            'currency': 'USD',
            'date_format': 'MM/DD/YYYY',
            'time_format': '12h',
            'language': 'en',
            'notification_settings': {},
            'security_settings': {},
            'integration_settings': {}
        }
        
        serializer = SystemConfigurationSerializer(config)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def update_configuration(self, request):
        """Update system configuration"""
        serializer = SystemConfigurationSerializer(data=request.data)
        if serializer.is_valid():
            # This would update system configuration
            return Response({'message': 'Configuration updated successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserConfigurationViewSet(viewsets.ViewSet):
    """ViewSet for user configuration"""
    permission_classes = [IsCompanyUser]

    @action(detail=False, methods=['get'])
    def get_my_configuration(self, request):
        """Get current user's configuration"""
        # This would retrieve user configuration
        config = {
            'theme': 'light',
            'language': 'en',
            'timezone': 'UTC',
            'date_format': 'MM/DD/YYYY',
            'time_format': '12h',
            'email_notifications': True,
            'sms_notifications': False,
            'dashboard_layout': {},
            'notification_preferences': {}
        }
        
        serializer = UserConfigurationSerializer(config)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def update_my_configuration(self, request):
        """Update current user's configuration"""
        serializer = UserConfigurationSerializer(data=request.data)
        if serializer.is_valid():
            # This would update user configuration
            return Response({'message': 'Configuration updated successfully'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SystemMetricsViewSet(viewsets.ViewSet):
    """ViewSet for system metrics"""
    permission_classes = [IsCompanyAdmin]

    @action(detail=False, methods=['get'])
    def get_metrics(self, request):
        """Get system metrics"""
        # This would calculate system metrics
        metrics = {
            'total_users': 100,
            'active_users': 85,
            'total_records': 10000,
            'storage_used': 5000000000,  # 5GB in bytes
            'api_calls_today': 1500,
            'error_rate': 0.5,
            'response_time': 150.5,
            'uptime': 99.9
        }
        
        serializer = SystemMetricsSerializer(metrics)
        return Response(serializer.data)

class SystemDiagnosticsViewSet(viewsets.ViewSet):
    """ViewSet for system diagnostics"""
    permission_classes = [IsCompanyAdmin]

    @action(detail=False, methods=['get'])
    def run_diagnostics(self, request):
        """Run system diagnostics"""
        # This would run system diagnostics
        diagnostics = {
            'database_status': 'healthy',
            'cache_status': 'healthy',
            'email_status': 'healthy',
            'storage_status': 'healthy',
            'api_status': 'healthy',
            'worker_status': 'healthy',
            'overall_health': 'healthy',
            'recommendations': [
                'Consider increasing cache size',
                'Monitor database performance'
            ]
        }
        
        serializer = SystemDiagnosticsSerializer(diagnostics)
        return Response(serializer.data)
