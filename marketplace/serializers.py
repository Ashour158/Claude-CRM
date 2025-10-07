# marketplace/serializers.py
# Serializers for marketplace module

from rest_framework import serializers
from .models import Plugin, PluginInstallation, PluginExecution, PluginReview

class PluginSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plugin
        fields = '__all__'
        read_only_fields = ['install_count', 'active_installs', 'rating_average', 'rating_count', 
                           'download_count', 'created_at', 'updated_at', 'published_at']

class PluginInstallationSerializer(serializers.ModelSerializer):
    plugin_name = serializers.CharField(source='plugin.name', read_only=True)
    
    class Meta:
        model = PluginInstallation
        fields = '__all__'
        read_only_fields = ['installation_id', 'installed_at', 'last_updated', 'last_activated',
                           'last_deactivated', 'error_count', 'last_error', 'execution_count', 'last_execution']

class PluginExecutionSerializer(serializers.ModelSerializer):
    plugin_name = serializers.CharField(source='installation.plugin.name', read_only=True)
    
    class Meta:
        model = PluginExecution
        fields = '__all__'
        read_only_fields = ['execution_id', 'started_at', 'completed_at', 'duration_ms']

class PluginReviewSerializer(serializers.ModelSerializer):
    reviewer_name = serializers.CharField(source='reviewer.email', read_only=True)
    
    class Meta:
        model = PluginReview
        fields = '__all__'
        read_only_fields = ['helpful_count', 'not_helpful_count', 'created_at', 'updated_at']
