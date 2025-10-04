# crm/serializers/leads.py
# Serializers for Lead model

from rest_framework import serializers
from crm.models import Lead, Account, Contact, Deal
from core.models import User

class LeadSerializer(serializers.ModelSerializer):
    """Full serializer for Lead model"""
    
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    territory_name = serializers.CharField(source='territory.name', read_only=True)
    is_hot = serializers.BooleanField(read_only=True)
    is_qualified = serializers.BooleanField(read_only=True)
    days_since_creation = serializers.IntegerField(read_only=True)
    activities_count = serializers.IntegerField(read_only=True)
    full_address = serializers.SerializerMethodField()
    
    class Meta:
        model = Lead
        fields = [
            'id', 'first_name', 'last_name', 'full_name',
            'company_name', 'title',
            'email', 'phone', 'mobile', 'website',
            'lead_source', 'lead_status', 'rating', 'lead_score',
            'address_line1', 'address_line2', 'city', 'state',
            'postal_code', 'country', 'full_address',
            'industry', 'annual_revenue', 'employee_count',
            'territory', 'territory_name', 'owner', 'owner_name',
            'converted_at', 'converted_account', 'converted_contact', 'converted_deal',
            'campaign_name', 'utm_source', 'utm_medium', 'utm_campaign',
            'budget', 'timeline', 'description', 'custom_fields',
            'is_hot', 'is_qualified', 'days_since_creation', 'activities_count',
            'is_active', 'company', 'created_at', 'updated_at',
            'created_by', 'updated_by'
        ]
        read_only_fields = [
            'id', 'full_name', 'company', 'lead_score',
            'converted_at', 'converted_account', 'converted_contact', 'converted_deal',
            'is_hot', 'is_qualified', 'days_since_creation', 'activities_count',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
    
    def get_full_address(self, obj):
        return obj.get_full_address()


class LeadListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for lead list"""
    
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    territory_name = serializers.CharField(source='territory.name', read_only=True)
    is_hot = serializers.BooleanField(read_only=True)
    days_since_creation = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Lead
        fields = [
            'id', 'full_name', 'company_name', 'title',
            'email', 'phone', 'lead_source', 'lead_status',
            'rating', 'lead_score', 'owner', 'owner_name',
            'territory', 'territory_name', 'is_hot',
            'days_since_creation', 'is_active', 'created_at'
        ]


class LeadCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating leads"""
    
    class Meta:
        model = Lead
        fields = [
            'first_name', 'last_name', 'company_name', 'title',
            'email', 'phone', 'mobile', 'website',
            'lead_source', 'rating',
            'address_line1', 'address_line2', 'city', 'state',
            'postal_code', 'country',
            'industry', 'annual_revenue', 'employee_count',
            'territory', 'owner',
            'campaign_name', 'utm_source', 'utm_medium', 'utm_campaign',
            'budget', 'timeline', 'description', 'custom_fields'
        ]
    
    def create(self, validated_data):
        validated_data['company'] = self.context['request'].active_company
        validated_data['created_by'] = self.context['request'].user
        
        lead = super().create(validated_data)
        
        # Auto-calculate lead score
        lead.lead_score = lead.calculate_lead_score()
        
        # Auto-assign territory if not set
        if not lead.territory:
            lead.auto_assign_territory()
        
        lead.save()
        return lead


class LeadUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating leads"""
    
    class Meta:
        model = Lead
        fields = [
            'first_name', 'last_name', 'company_name', 'title',
            'email', 'phone', 'mobile', 'website',
            'lead_source', 'lead_status', 'rating',
            'address_line1', 'address_line2', 'city', 'state',
            'postal_code', 'country',
            'industry', 'annual_revenue', 'employee_count',
            'territory', 'owner',
            'campaign_name', 'utm_source', 'utm_medium', 'utm_campaign',
            'budget', 'timeline', 'description', 'custom_fields',
            'is_active'
        ]
    
    def update(self, instance, validated_data):
        validated_data['updated_by'] = self.context['request'].user
        
        lead = super().update(instance, validated_data)
        
        # Recalculate lead score
        lead.lead_score = lead.calculate_lead_score()
        lead.save()
        
        return lead


class LeadConvertSerializer(serializers.Serializer):
    """Serializer for lead conversion"""
    
    create_deal = serializers.BooleanField(default=True)
    deal_amount = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        required=False,
        allow_null=True
    )
    deal_name = serializers.CharField(required=False, allow_blank=True)
    deal_close_date = serializers.DateField(required=False, allow_null=True)


class LeadStatsSerializer(serializers.Serializer):
    """Serializer for lead statistics"""
    
    total_leads = serializers.IntegerField()
    new_leads = serializers.IntegerField()
    qualified_leads = serializers.IntegerField()
    converted_leads = serializers.IntegerField()
    hot_leads = serializers.IntegerField()
    by_source = serializers.DictField()
    by_status = serializers.DictField()
    conversion_rate = serializers.FloatField()
    avg_lead_score = serializers.FloatField()


class LeadImportSerializer(serializers.Serializer):
    """Serializer for CSV import"""
    
    file = serializers.FileField(required=True)
    owner_id = serializers.UUIDField(required=False, allow_null=True)
    
    def validate_file(self, value):
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError('Only CSV files are allowed.')
        return value


class BulkLeadActionSerializer(serializers.Serializer):
    """Serializer for bulk actions"""
    
    lead_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True,
        min_length=1
    )
    action = serializers.ChoiceField(
        choices=['delete', 'qualify', 'disqualify', 'assign_owner', 'assign_territory'],
        required=True
    )
    owner_id = serializers.UUIDField(required=False, allow_null=True)
    territory_id = serializers.UUIDField(required=False, allow_null=True)


class LeadScoringSerializer(serializers.Serializer):
    """Serializer for lead scoring results"""
    
    lead_id = serializers.UUIDField()
    score = serializers.IntegerField()
    factors = serializers.DictField()
    recommendation = serializers.CharField()