# deals/serializers.py
from rest_framework import serializers
from deals.models import PipelineStage, Deal, DealProduct, DealActivity, DealForecast
from crm.serializers import AccountSerializer, ContactSerializer
from territories.serializers import TerritorySerializer
from products.serializers import ProductSerializer
from core.serializers import UserBasicSerializer

class PipelineStageSerializer(serializers.ModelSerializer):
    """Serializer for PipelineStage"""
    deal_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PipelineStage
        fields = [
            'id', 'name', 'description', 'sequence', 'probability',
            'is_closed', 'is_won', 'color', 'is_active',
            'deal_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_deal_count(self, obj):
        return obj.deals.filter(is_active=True).count()

class PipelineStageListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for pipeline stage lists"""
    
    class Meta:
        model = PipelineStage
        fields = ['id', 'name', 'sequence', 'probability', 'is_closed', 'is_won', 'color']

class DealProductSerializer(serializers.ModelSerializer):
    """Serializer for DealProduct"""
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    
    class Meta:
        model = DealProduct
        fields = [
            'id', 'product', 'product_name', 'product_sku',
            'quantity', 'unit_price', 'discount_percentage', 'total_price',
            'description', 'created_at'
        ]
        read_only_fields = ['id', 'total_price', 'created_at']

class DealActivitySerializer(serializers.ModelSerializer):
    """Serializer for DealActivity"""
    participants_detail = UserBasicSerializer(source='participants', many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = DealActivity
        fields = [
            'id', 'activity_type', 'subject', 'description',
            'activity_date', 'duration_minutes', 'outcome',
            'next_action', 'next_action_date', 'participants',
            'participants_detail', 'created_by_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class DealForecastSerializer(serializers.ModelSerializer):
    """Serializer for DealForecast"""
    
    class Meta:
        model = DealForecast
        fields = [
            'id', 'forecast_period', 'forecast_date', 'forecast_amount',
            'confidence_level', 'notes', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class DealListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for deal lists"""
    account_name = serializers.CharField(source='account.name', read_only=True)
    contact_name = serializers.CharField(source='contact.full_name', read_only=True)
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    stage_name = serializers.CharField(source='stage.name', read_only=True)
    days_in_stage = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    
    class Meta:
        model = Deal
        fields = [
            'id', 'name', 'account', 'account_name', 'contact', 'contact_name',
            'stage', 'stage_name', 'status', 'amount', 'currency', 'probability',
            'expected_revenue', 'expected_close_date', 'owner', 'owner_name',
            'priority', 'source', 'days_in_stage', 'is_overdue', 'created_at'
        ]

class DealSerializer(serializers.ModelSerializer):
    """Full serializer for Deal with related data"""
    # Read-only computed fields
    account_name = serializers.CharField(source='account.name', read_only=True)
    contact_name = serializers.CharField(source='contact.full_name', read_only=True)
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    stage_name = serializers.CharField(source='stage.name', read_only=True)
    territory_name = serializers.CharField(source='territory.name', read_only=True)
    days_in_stage = serializers.ReadOnlyField()
    is_overdue = serializers.ReadOnlyField()
    
    # Related object serializers
    account_detail = AccountSerializer(source='account', read_only=True)
    contact_detail = ContactSerializer(source='contact', read_only=True)
    owner_detail = UserBasicSerializer(source='owner', read_only=True)
    stage_detail = PipelineStageSerializer(source='stage', read_only=True)
    territory_detail = TerritorySerializer(source='territory', read_only=True)
    
    # Nested serializers
    products = DealProductSerializer(many=True, read_only=True)
    activities = DealActivitySerializer(many=True, read_only=True)
    forecast = DealForecastSerializer(read_only=True)
    
    # Custom fields
    product_count = serializers.SerializerMethodField()
    activity_count = serializers.SerializerMethodField()
    last_activity_date = serializers.SerializerMethodField()
    
    class Meta:
        model = Deal
        fields = [
            'id', 'name', 'description',
            'account', 'account_name', 'account_detail',
            'contact', 'contact_name', 'contact_detail',
            'lead', 'stage', 'stage_name', 'stage_detail',
            'status', 'amount', 'currency', 'probability',
            'expected_revenue', 'expected_close_date', 'actual_close_date',
            'owner', 'owner_name', 'owner_detail',
            'territory', 'territory_name', 'territory_detail',
            'priority', 'source', 'competitor', 'next_step', 'notes',
            'tags', 'metadata', 'is_active',
            'products', 'activities', 'forecast',
            'product_count', 'activity_count', 'last_activity_date',
            'days_in_stage', 'is_overdue',
            'created_at', 'updated_at', 'created_by_name'
        ]
        read_only_fields = [
            'id', 'expected_revenue', 'days_in_stage', 'is_overdue',
            'created_at', 'updated_at'
        ]
    
    def get_product_count(self, obj):
        return obj.products.count()
    
    def get_activity_count(self, obj):
        return obj.activities.count()
    
    def get_last_activity_date(self, obj):
        last_activity = obj.activities.order_by('-activity_date').first()
        return last_activity.activity_date if last_activity else None
    
    def create(self, validated_data):
        # Auto-set company from request
        request = self.context.get('request')
        validated_data['company'] = request.active_company
        validated_data['created_by'] = request.user
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Track who updated
        request = self.context.get('request')
        validated_data['updated_by'] = request.user
        return super().update(instance, validated_data)

class DealCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating deals with minimal required fields"""
    
    class Meta:
        model = Deal
        fields = [
            'name', 'description', 'account', 'contact', 'stage',
            'amount', 'currency', 'probability', 'expected_close_date',
            'owner', 'priority', 'source', 'next_step', 'notes'
        ]
    
    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['company'] = request.active_company
        validated_data['created_by'] = request.user
        return super().create(validated_data)

class DealUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating deals"""
    
    class Meta:
        model = Deal
        fields = [
            'name', 'description', 'account', 'contact', 'stage',
            'status', 'amount', 'currency', 'probability',
            'expected_close_date', 'actual_close_date', 'owner',
            'priority', 'source', 'competitor', 'next_step', 'notes',
            'tags', 'metadata', 'is_active'
        ]
    
    def update(self, instance, validated_data):
        request = self.context.get('request')
        validated_data['updated_by'] = request.user
        return super().update(instance, validated_data)

class DealPipelineSerializer(serializers.ModelSerializer):
    """Serializer for pipeline kanban view"""
    deals = DealListSerializer(many=True, read_only=True)
    deal_count = serializers.SerializerMethodField()
    total_value = serializers.SerializerMethodField()
    weighted_value = serializers.SerializerMethodField()
    
    class Meta:
        model = PipelineStage
        fields = [
            'id', 'name', 'description', 'sequence', 'probability',
            'is_closed', 'is_won', 'color', 'deals',
            'deal_count', 'total_value', 'weighted_value'
        ]
    
    def get_deal_count(self, obj):
        return obj.deals.filter(is_active=True).count()
    
    def get_total_value(self, obj):
        from django.db.models import Sum
        return obj.deals.filter(is_active=True).aggregate(
            total=Sum('amount')
        )['total'] or 0
    
    def get_weighted_value(self, obj):
        from django.db.models import Sum
        return obj.deals.filter(is_active=True).aggregate(
            total=Sum('expected_revenue')
        )['total'] or 0

class DealStatsSerializer(serializers.Serializer):
    """Serializer for deal statistics"""
    total_deals = serializers.IntegerField()
    open_deals = serializers.IntegerField()
    won_deals = serializers.IntegerField()
    lost_deals = serializers.IntegerField()
    total_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    weighted_value = serializers.DecimalField(max_digits=15, decimal_places=2)
    average_deal_size = serializers.DecimalField(max_digits=15, decimal_places=2)
    win_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    average_sales_cycle = serializers.IntegerField()
    deals_by_stage = serializers.DictField()
    deals_by_owner = serializers.DictField()
    deals_by_source = serializers.DictField()
    monthly_trend = serializers.ListField()
    quarterly_forecast = serializers.ListField()