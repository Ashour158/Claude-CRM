# analytics/serializers.py
# Analytics serializers

from rest_framework import serializers
from .models import (
    Dashboard, Report, KPI, KPIMeasurement, SalesForecast,
    ActivityAnalytics, SalesAnalytics, LeadAnalytics
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
