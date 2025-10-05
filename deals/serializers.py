# deals/serializers.py
# Deals Serializers

from rest_framework import serializers
from .models import Deal

class DealSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deal
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']