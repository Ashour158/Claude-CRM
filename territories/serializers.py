# territories/serializers.py
# Territories Serializers

from rest_framework import serializers
from .models import Territory

class TerritorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Territory
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']