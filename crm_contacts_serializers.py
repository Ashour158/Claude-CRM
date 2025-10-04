# crm/serializers/contacts.py
# Serializers for Contact model

from rest_framework import serializers
from crm.models import Contact, Account
from core.models import User

class ContactSerializer(serializers.ModelSerializer):
    """
    Full serializer for Contact model with all fields and relationships
    """
    
    # Read-only computed fields
    account_name = serializers.CharField(source='account.name', read_only=True)
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    reports_to_name = serializers.CharField(source='reports_to.full_name', read_only=True)
    activities_count = serializers.IntegerField(read_only=True)
    deals_count = serializers.IntegerField(read_only=True)
    age = serializers.IntegerField(read_only=True)
    full_mailing_address = serializers.SerializerMethodField()
    
    class Meta:
        model = Contact
        fields = [
            # IDs
            'id',
            
            # Basic Info
            'first_name', 'last_name', 'full_name', 'title', 'department',
            
            # Contact Info
            'email', 'phone', 'mobile', 'fax',
            
            # Social
            'linkedin_url', 'twitter_handle', 'facebook_url',
            
            # Relationships
            'account', 'account_name',
            'reports_to', 'reports_to_name',
            'owner', 'owner_name',
            
            # Mailing Address
            'mailing_address_line1', 'mailing_address_line2',
            'mailing_city', 'mailing_state', 'mailing_postal_code',
            'mailing_country', 'full_mailing_address',
            
            # Other Address
            'other_address_line1', 'other_address_line2',
            'other_city', 'other_state', 'other_postal_code',
            'other_country',
            
            # Preferences
            'email_opt_out', 'do_not_call', 'preferred_contact_method',
            
            # Classification
            'contact_type', 'is_primary',
            
            # Important Dates
            'date_of_birth', 'age',
            'assistant_name', 'assistant_phone',
            
            # Notes
            'description',
            
            # Custom Fields
            'custom_fields',
            
            # Status
            'is_active',
            
            # Computed
            'activities_count', 'deals_count',
            
            # Metadata
            'company', 'created_at', 'updated_at',
            'created_by', 'updated_by'
        ]
        read_only_fields = [
            'id', 'full_name', 'company', 'age',
            'activities_count', 'deals_count',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
    
    def get_full_mailing_address(self, obj):
        return obj.get_full_address('mailing')
    
    def validate_email(self, value):
        """Validate email is unique within company"""
        if value:
            company = self.context['request'].active_company
            query = Contact.objects.filter(company=company, email=value)
            
            # Exclude current instance if updating
            if self.instance:
                query = query.exclude(id=self.instance.id)
            
            if query.exists():
                raise serializers.ValidationError(
                    'A contact with this email already exists in your company.'
                )
        
        return value


class ContactListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for contact list view
    """
    
    account_name = serializers.CharField(source='account.name', read_only=True)
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    
    class Meta:
        model = Contact
        fields = [
            'id', 'first_name', 'last_name', 'full_name',
            'title', 'email', 'phone', 'mobile',
            'account', 'account_name',
            'owner', 'owner_name',
            'contact_type', 'is_primary',
            'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'full_name', 'created_at']


class ContactCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating contacts
    """
    
    class Meta:
        model = Contact
        fields = [
            'first_name', 'last_name', 'title', 'department',
            'email', 'phone', 'mobile', 'fax',
            'linkedin_url', 'twitter_handle', 'facebook_url',
            'account', 'reports_to', 'owner',
            'mailing_address_line1', 'mailing_address_line2',
            'mailing_city', 'mailing_state', 'mailing_postal_code',
            'mailing_country',
            'email_opt_out', 'do_not_call', 'preferred_contact_method',
            'contact_type', 'is_primary',
            'date_of_birth', 'assistant_name', 'assistant_phone',
            'description', 'custom_fields'
        ]
    
    def create(self, validated_data):
        # Set company and created_by from context
        validated_data['company'] = self.context['request'].active_company
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class ContactUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating contacts
    """
    
    class Meta:
        model = Contact
        fields = [
            'first_name', 'last_name', 'title', 'department',
            'email', 'phone', 'mobile', 'fax',
            'linkedin_url', 'twitter_handle', 'facebook_url',
            'account', 'reports_to', 'owner',
            'mailing_address_line1', 'mailing_address_line2',
            'mailing_city', 'mailing_state', 'mailing_postal_code',
            'mailing_country',
            'other_address_line1', 'other_address_line2',
            'other_city', 'other_state', 'other_postal_code',
            'other_country',
            'email_opt_out', 'do_not_call', 'preferred_contact_method',
            'contact_type', 'is_primary',
            'date_of_birth', 'assistant_name', 'assistant_phone',
            'description', 'custom_fields', 'is_active'
        ]
    
    def update(self, instance, validated_data):
        # Set updated_by
        validated_data['updated_by'] = self.context['request'].user
        return super().update(instance, validated_data)


class ContactStatsSerializer(serializers.Serializer):
    """
    Serializer for contact statistics
    """
    
    total_contacts = serializers.IntegerField()
    active_contacts = serializers.IntegerField()
    contacts_with_accounts = serializers.IntegerField()
    decision_makers = serializers.IntegerField()
    by_contact_type = serializers.DictField()


class ContactImportSerializer(serializers.Serializer):
    """
    Serializer for CSV import
    """
    
    file = serializers.FileField(required=True)
    account_id = serializers.UUIDField(required=False, allow_null=True)
    
    def validate_file(self, value):
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError('Only CSV files are allowed.')
        return value


class BulkContactActionSerializer(serializers.Serializer):
    """
    Serializer for bulk actions on contacts
    """
    
    contact_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=True,
        min_length=1
    )
    action = serializers.ChoiceField(
        choices=['delete', 'deactivate', 'activate', 'assign_owner'],
        required=True
    )
    owner_id = serializers.UUIDField(required=False, allow_null=True)
    
    def validate(self, attrs):
        if attrs['action'] == 'assign_owner' and not attrs.get('owner_id'):
            raise serializers.ValidationError({
                'owner_id': 'Owner ID is required for assign_owner action.'
            })
        return attrs