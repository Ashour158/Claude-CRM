# analytics/serializers.py
# Analytics serializers

from rest_framework import serializers
from .models import (
    Dashboard, Report, KPI, KPIMeasurement, SalesForecast,
    ActivityAnalytics, SalesAnalytics, LeadAnalytics,
    FactDealStageTransition, FactActivity, FactLeadConversion,
    AnalyticsExportJob
)
from core.serializers import UserSerializer

class DashboardSerializer(serializers.ModelSerializer):
    """Dashboard serializer"""
    owner = UserSerializer(read_only=True)
    shared_with = UserSerializer(many=True, read_only=True)
    
    class Meta:
        model = Dashboard
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class ReportSerializer(serializers.ModelSerializer):
    """Report serializer"""
    owner = UserSerializer(read_only=True)
    shared_with = UserSerializer(many=True, read_only=True)
    
    class Meta:
        model = Report
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class KPISerializer(serializers.ModelSerializer):
    """KPI serializer"""
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = KPI
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class KPIMeasurementSerializer(serializers.ModelSerializer):
    """KPI measurement serializer"""
    
    class Meta:
        model = KPIMeasurement
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class SalesForecastSerializer(serializers.ModelSerializer):
    """Sales forecast serializer"""
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = SalesForecast
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class ActivityAnalyticsSerializer(serializers.ModelSerializer):
    """Activity analytics serializer"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ActivityAnalytics
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class SalesAnalyticsSerializer(serializers.ModelSerializer):
    """Sales analytics serializer"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = SalesAnalytics
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

class LeadAnalyticsSerializer(serializers.ModelSerializer):
    """Lead analytics serializer"""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = LeadAnalytics
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class FactDealStageTransitionSerializer(serializers.ModelSerializer):
    """Fact deal stage transition serializer"""
    owner = UserSerializer(read_only=True)
    deal_name = serializers.CharField(source='deal.name', read_only=True)
    
    class Meta:
        model = FactDealStageTransition
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class FactActivitySerializer(serializers.ModelSerializer):
    """Fact activity serializer"""
    assigned_to_name = serializers.CharField(source='assigned_to.get_full_name', read_only=True)
    
    class Meta:
        model = FactActivity
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class FactLeadConversionSerializer(serializers.ModelSerializer):
    """Fact lead conversion serializer"""
    owner = UserSerializer(read_only=True)
    lead_name = serializers.SerializerMethodField()
    
    class Meta:
        model = FactLeadConversion
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_lead_name(self, obj):
        return f"{obj.lead.first_name} {obj.lead.last_name}".strip() if obj.lead else ""


class AnalyticsExportJobSerializer(serializers.ModelSerializer):
    """Analytics export job serializer"""
    owner = UserSerializer(read_only=True)
    
    class Meta:
        model = AnalyticsExportJob
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at', 'status', 'progress_percent', 
                          'output_file', 'total_records', 'error_message', 
                          'started_at', 'completed_at', 'notification_sent']
