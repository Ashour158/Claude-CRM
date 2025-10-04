# crm/serializers/accounts.py
# Serializers for Account model

from rest_framework import serializers
from crm.models import Account
from core.models import User
from territories.models import Territory

class AccountSerializer(serializers.ModelSerializer):
    """
    Full serializer for Account model with all fields and relationships
    """
    
    # Read-only computed fields
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    territory_name = serializers.CharField(source='territory.name', read_only=True)
    parent_account_name = serializers.CharField(source='parent_account.name', read_only=True)
    contacts_count = serializers.IntegerField(read_only=True)
    deals_count = serializers.IntegerField(read_only=True)
    open_deals_value = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    full_billing_address = serializers.SerializerMethodField()
    full_shipping_address = serializers.SerializerMethodField()
    
    class Meta:
        model = Account
        fields = [
            # IDs
            'id', 'account_number',
            
            # Basic Info
            'name', 'legal_name', 'website',
            'account_type', 'industry', 'annual_revenue', 'employee_count',
            
            # Contact
            'phone', 'email',
            
            # Billing Address
            'billing_address_line1', 'billing_address_line2',
            'billing_city', 'billing_state', 'billing_postal_code',
            'billing_country', 'full_billing_address',
            
            # Shipping Address
            'shipping_address_line1', 'shipping_address_line2',
            'shipping_city', 'shipping_state', 'shipping_postal_code',
            'shipping_country', 'full_shipping_address',
            
            # Relationships
            'parent_account', 'parent_account_name',
            'territory', 'territory_name',
            'owner', 'owner_name',
            
            # Financial
            'payment_terms', 'credit_limit', 'tax_id',
            
            # Custom Fields
            'custom_fields',
            
            # Status
            'is_active',
            
            # Description
            'description',
            
            # Computed
            'contacts_count', 'deals_count', 'open_deals_value',
            
            # Metadata
            'company', 'created_at', 'updated_at',
            'created_by', 'updated_by'
        ]
        read_only_fields = [
            'id', 'account_number', 'company',
            'contacts_count', 'deals_count', 'open_deals_value',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
    
    def get_full_billing_address(self, obj):
        return obj.get_full_address('billing')
    
    def get_full_shipping_address(self, obj):
        return obj.get_full_address('shipping')
    
    def validate(self, attrs):
        # Custom validation
        if attrs.get('annual_revenue') and attrs['annual_revenue'] < 0:
            raise serializers.ValidationError({
                'annual_revenue': 'Annual revenue cannot be negative.'
            })
        
        if attrs.get('employee_count') and attrs['employee_count'] < 0:
            raise serializers.ValidationError({
                'employee_count': 'Employee count cannot be negative.'
            })
        
        return attrs


class AccountListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for account list view.
    Only includes essential fields for performance.
    """
    
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    territory_name = serializers.CharField(source='territory.name', read_only=True)
    contacts_count = serializers.IntegerField(read_only=True)
    deals_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Account
        fields = [
            'id', 'account_number', 'name', 'account_type',
            'industry', 'phone', 'email', 'website',
            'owner', 'owner_name', 'territory', 'territory_name',
            'contacts_count', 'deals_count',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'account_number', 'created_at']


class AccountCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating accounts.
    Simplified fields for account creation.
    """
    
    class Meta:
        model = Account
        fields = [
            'name', 'legal_name', 'website', 'account_type',
            'industry', 'annual_revenue', 'employee_count',
            'phone', 'email',
            'billing_address_line1', 'billing_address_line2',
            'billing_city', 'billing_state', 'billing_postal_code',
            'billing_country',
            'parent_account', 'territory', 'owner',
            'payment_terms', 'credit_limit', 'tax_id',
            'description', 'custom_fields'
        ]
    
    def create(self, validated_data):
        # Set company and created_by from context
        validated_data['company'] = self.context['request'].active_company
        validated_data['created_by'] = self.context['request'].user
        
        # Copy billing address to shipping if shipping is empty
        if not validated_data.get('shipping_address_line1'):
            validated_data['shipping_address_line1'] = validated_data.get('billing_address_line1', '')
            validated_data['shipping_address_line2'] = validated_data.get('billing_address_line2', '')
            validated_data['shipping_city'] = validated_data.get('billing_city', '')
            validated_data['shipping_state'] = validated_data.get('billing_state', '')
            validated_data['shipping_postal_code'] = validated_data.get('billing_postal_code', '')
            validated_data['shipping_country'] = validated_data.get('billing_country', '')
        
        return super().create(validated_data)


class AccountUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating accounts.
    """
    
    class Meta:
        model = Account
        fields = [
            'name', 'legal_name', 'website', 'account_type',
            'industry', 'annual_revenue', 'employee_count',
            'phone', 'email',
            'billing_address_line1', 'billing_address_line2',
            'billing_city', 'billing_state', 'billing_postal_code',
            'billing_country',
            'shipping_address_line1', 'shipping_address_line2',
            'shipping_city', 'shipping_state', 'shipping_postal_code',
            'shipping_country',
            'parent_account', 'territory', 'owner',
            'payment_terms', 'credit_limit', 'tax_id',
            'description', 'custom_fields', 'is_active'
        ]
    
    def update(self, instance, validated_data):
        # Set updated_by
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class AccountStatsSerializer(serializers.Serializer):
    """
    Serializer for account statistics
    """
    
    total_accounts = serializers.IntegerField()
    active_accounts = serializers.IntegerField()
    customers = serializers.IntegerField()
    prospects = serializers.IntegerField()
    by_industry = serializers.DictField()
    total_revenue = serializers.DecimalField(max_digits=15, decimal_places=2)


class AccountImportSerializer(serializers.Serializer):
    """
    Serializer for CSV import
    """
    
    file = serializers.FileField(required=True)
    
    def validate_file(self, value):
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError('Only CSV files are allowed.')
        return value