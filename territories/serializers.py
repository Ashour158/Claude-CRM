# territories/serializers.py
# Territory Serializers

from rest_framework import serializers
from territories.models import Territory, TerritoryRule, TerritoryAssignment
from core.serializers.auth import UserSerializer


class TerritorySerializer(serializers.ModelSerializer):
    """Full territory serializer with computed fields"""
    
    # Computed fields
    manager_name = serializers.SerializerMethodField()
    parent_name = serializers.SerializerMethodField()
    children_count = serializers.SerializerMethodField()
    users_count = serializers.SerializerMethodField()
    accounts_count = serializers.SerializerMethodField()
    leads_count = serializers.SerializerMethodField()
    deals_count = serializers.SerializerMethodField()
    total_deal_value = serializers.SerializerMethodField()
    full_path = serializers.SerializerMethodField()
    
    class Meta:
        model = Territory
        fields = [
            'id', 'name', 'code', 'description', 'type', 'parent', 'parent_name',
            'manager', 'manager_name', 'countries', 'states', 'cities', 'postal_codes',
            'product_categories', 'product_ids', 'customer_types', 'revenue_min',
            'revenue_max', 'industries', 'currency', 'quota_amount', 'quota_period',
            'is_active', 'created_at', 'updated_at', 'created_by', 'updated_by',
            'children_count', 'users_count', 'accounts_count', 'leads_count',
            'deals_count', 'total_deal_value', 'full_path'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'created_by', 'updated_by',
            'manager_name', 'parent_name', 'children_count', 'users_count',
            'accounts_count', 'leads_count', 'deals_count', 'total_deal_value',
            'full_path'
        ]
    
    def get_manager_name(self, obj):
        return obj.manager.get_full_name() if obj.manager else None
    
    def get_parent_name(self, obj):
        return obj.parent.name if obj.parent else None
    
    def get_children_count(self, obj):
        return obj.children.count()
    
    def get_users_count(self, obj):
        return obj.get_all_users().count()
    
    def get_accounts_count(self, obj):
        return obj.accounts.count()
    
    def get_leads_count(self, obj):
        return obj.leads.count()
    
    def get_deals_count(self, obj):
        return obj.deals.count()
    
    def get_total_deal_value(self, obj):
        from django.db.models import Sum
        return obj.deals.aggregate(total=Sum('amount'))['total'] or 0
    
    def get_full_path(self, obj):
        return obj.get_full_path()


class TerritoryListSerializer(serializers.ModelSerializer):
    """Lightweight territory serializer for list views"""
    
    manager_name = serializers.SerializerMethodField()
    parent_name = serializers.SerializerMethodField()
    users_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Territory
        fields = [
            'id', 'name', 'code', 'type', 'manager', 'manager_name',
            'parent', 'parent_name', 'is_active', 'users_count'
        ]
    
    def get_manager_name(self, obj):
        return obj.manager.get_full_name() if obj.manager else None
    
    def get_parent_name(self, obj):
        return obj.parent.name if obj.parent else None
    
    def get_users_count(self, obj):
        return obj.get_all_users().count()


class TerritoryCreateSerializer(serializers.ModelSerializer):
    """Territory creation serializer"""
    
    class Meta:
        model = Territory
        fields = [
            'name', 'code', 'description', 'type', 'parent', 'manager',
            'countries', 'states', 'cities', 'postal_codes', 'product_categories',
            'product_ids', 'customer_types', 'revenue_min', 'revenue_max',
            'industries', 'currency', 'quota_amount', 'quota_period', 'is_active'
        ]
    
    def validate_code(self, value):
        """Validate territory code uniqueness within company"""
        if Territory.objects.filter(
            company=self.context['request'].active_company,
            code=value
        ).exists():
            raise serializers.ValidationError(
                "Territory code must be unique within company"
            )
        return value
    
    def validate_parent(self, value):
        """Validate parent territory belongs to same company"""
        if value and value.company != self.context['request'].active_company:
            raise serializers.ValidationError(
                "Parent territory must belong to the same company"
            )
        return value
    
    def validate_manager(self, value):
        """Validate manager has access to company"""
        if value and not value.has_company_access(self.context['request'].active_company):
            raise serializers.ValidationError(
                "Manager must have access to the company"
            )
        return value


class TerritoryUpdateSerializer(serializers.ModelSerializer):
    """Territory update serializer"""
    
    class Meta:
        model = Territory
        fields = [
            'name', 'code', 'description', 'type', 'parent', 'manager',
            'countries', 'states', 'cities', 'postal_codes', 'product_categories',
            'product_ids', 'customer_types', 'revenue_min', 'revenue_max',
            'industries', 'currency', 'quota_amount', 'quota_period', 'is_active'
        ]
    
    def validate_code(self, value):
        """Validate territory code uniqueness within company"""
        if Territory.objects.filter(
            company=self.context['request'].active_company,
            code=value
        ).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError(
                "Territory code must be unique within company"
            )
        return value
    
    def validate_parent(self, value):
        """Validate parent territory belongs to same company and not self"""
        if value:
            if value.company != self.context['request'].active_company:
                raise serializers.ValidationError(
                    "Parent territory must belong to the same company"
                )
            if value.id == self.instance.id:
                raise serializers.ValidationError(
                    "Territory cannot be its own parent"
                )
        return value
    
    def validate_manager(self, value):
        """Validate manager has access to company"""
        if value and not value.has_company_access(self.context['request'].active_company):
            raise serializers.ValidationError(
                "Manager must have access to the company"
            )
        return value


class TerritoryStatsSerializer(serializers.ModelSerializer):
    """Territory statistics serializer"""
    
    users_count = serializers.SerializerMethodField()
    accounts_count = serializers.SerializerMethodField()
    leads_count = serializers.SerializerMethodField()
    deals_count = serializers.SerializerMethodField()
    total_deal_value = serializers.SerializerMethodField()
    weighted_deal_value = serializers.SerializerMethodField()
    
    class Meta:
        model = Territory
        fields = [
            'id', 'name', 'code', 'type', 'quota_amount', 'quota_period',
            'users_count', 'accounts_count', 'leads_count', 'deals_count',
            'total_deal_value', 'weighted_deal_value'
        ]
    
    def get_users_count(self, obj):
        return obj.get_all_users().count()
    
    def get_accounts_count(self, obj):
        return obj.accounts.count()
    
    def get_leads_count(self, obj):
        return obj.leads.count()
    
    def get_deals_count(self, obj):
        return obj.deals.count()
    
    def get_total_deal_value(self, obj):
        from django.db.models import Sum
        return obj.deals.aggregate(total=Sum('amount'))['total'] or 0
    
    def get_weighted_deal_value(self, obj):
        from django.db.models import Sum, F
        return obj.deals.aggregate(
            total=Sum(F('amount') * F('probability') / 100)
        )['total'] or 0


class TerritoryRuleSerializer(serializers.ModelSerializer):
    """Territory rule serializer"""
    
    territory_name = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = TerritoryRule
        fields = [
            'id', 'territory', 'territory_name', 'name', 'description',
            'priority', 'conditions', 'auto_assign', 'notify_manager',
            'is_active', 'created_at', 'updated_at', 'created_by',
            'created_by_name', 'updated_by'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'created_by', 'updated_by',
            'territory_name', 'created_by_name'
        ]
    
    def get_territory_name(self, obj):
        return obj.territory.name if obj.territory else None
    
    def get_created_by_name(self, obj):
        return obj.created_by.get_full_name() if obj.created_by else None


class TerritoryRuleCreateSerializer(serializers.ModelSerializer):
    """Territory rule creation serializer"""
    
    class Meta:
        model = TerritoryRule
        fields = [
            'territory', 'name', 'description', 'priority', 'conditions',
            'auto_assign', 'notify_manager', 'is_active'
        ]
    
    def validate_territory(self, value):
        """Validate territory belongs to company"""
        if value.company != self.context['request'].active_company:
            raise serializers.ValidationError(
                "Territory must belong to the same company"
            )
        return value
    
    def validate_conditions(self, value):
        """Validate conditions JSON structure"""
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                "Conditions must be a valid JSON object"
            )
        return value


class TerritoryRuleUpdateSerializer(serializers.ModelSerializer):
    """Territory rule update serializer"""
    
    class Meta:
        model = TerritoryRule
        fields = [
            'territory', 'name', 'description', 'priority', 'conditions',
            'auto_assign', 'notify_manager', 'is_active'
        ]
    
    def validate_territory(self, value):
        """Validate territory belongs to company"""
        if value.company != self.context['request'].active_company:
            raise serializers.ValidationError(
                "Territory must belong to the same company"
            )
        return value
    
    def validate_conditions(self, value):
        """Validate conditions JSON structure"""
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                "Conditions must be a valid JSON object"
            )
        return value


class TerritoryAssignmentSerializer(serializers.ModelSerializer):
    """Territory assignment serializer"""
    
    territory_name = serializers.SerializerMethodField()
    assigned_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = TerritoryAssignment
        fields = [
            'id', 'territory', 'territory_name', 'entity_type', 'entity_id',
            'assigned_by', 'assigned_by_name', 'assignment_reason',
            'is_active', 'created_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'territory_name', 'assigned_by_name'
        ]
    
    def get_territory_name(self, obj):
        return obj.territory.name if obj.territory else None
    
    def get_assigned_by_name(self, obj):
        return obj.assigned_by.get_full_name() if obj.assigned_by else None
