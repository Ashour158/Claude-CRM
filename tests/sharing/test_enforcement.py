# tests/sharing/test_enforcement.py
# Tests for sharing enforcement

import pytest
from django.contrib.auth import get_user_model
from core.models import Company, UserCompanyAccess
from crm.models import Lead, Account, Contact
from deals.models import Deal
from sharing.models import SharingRule, RecordShare
from sharing.enforcement import SharingEnforcer

User = get_user_model()


@pytest.mark.django_db
class TestSharingEnforcement:
    """Test sharing enforcement logic"""
    
    @pytest.fixture
    def setup_data(self):
        """Setup test data"""
        # Create company
        company = Company.objects.create(
            name='Test Company',
            code='TEST001',
            is_active=True
        )
        
        # Create users
        owner = User.objects.create_user(
            email='owner@test.com',
            password='password123'
        )
        other_user = User.objects.create_user(
            email='other@test.com',
            password='password123'
        )
        unrelated_user = User.objects.create_user(
            email='unrelated@test.com',
            password='password123'
        )
        
        # Grant company access
        for user in [owner, other_user, unrelated_user]:
            UserCompanyAccess.objects.create(
                user=user,
                company=company,
                role='user',
                is_active=True
            )
        
        return {
            'company': company,
            'owner': owner,
            'other_user': other_user,
            'unrelated_user': unrelated_user
        }
    
    def test_ownership_only_visibility(self, setup_data):
        """Test that owner can see their own leads, others cannot (default deny)"""
        company = setup_data['company']
        owner = setup_data['owner']
        unrelated_user = setup_data['unrelated_user']
        
        # Create lead owned by owner
        lead = Lead.objects.create(
            company=company,
            first_name='John',
            last_name='Doe',
            status='new',
            owner=owner
        )
        
        # Owner should see the lead
        queryset = Lead.objects.filter(company=company)
        filtered = SharingEnforcer.enforce_sharing(
            queryset=queryset,
            user=owner,
            company=company,
            object_type='lead',
            ownership_field='owner'
        )
        assert filtered.count() == 1
        assert lead in filtered
        
        # Unrelated user should NOT see the lead (default deny)
        filtered_unrelated = SharingEnforcer.enforce_sharing(
            queryset=queryset,
            user=unrelated_user,
            company=company,
            object_type='lead',
            ownership_field='owner'
        )
        assert filtered_unrelated.count() == 0
    
    def test_rule_based_access(self, setup_data):
        """Test that users can see records matching sharing rules"""
        company = setup_data['company']
        owner = setup_data['owner']
        other_user = setup_data['other_user']
        
        # Create qualified lead
        qualified_lead = Lead.objects.create(
            company=company,
            first_name='Jane',
            last_name='Smith',
            status='qualified',
            owner=owner
        )
        
        # Create new lead
        new_lead = Lead.objects.create(
            company=company,
            first_name='Bob',
            last_name='Jones',
            status='new',
            owner=owner
        )
        
        # Create sharing rule for qualified leads
        rule = SharingRule.objects.create(
            company=company,
            name='Qualified Leads Visibility',
            object_type='lead',
            predicate={
                'field': 'status',
                'operator': 'eq',
                'value': 'qualified'
            },
            access_level='read_only',
            is_active=True
        )
        
        # other_user should see qualified lead due to rule
        queryset = Lead.objects.filter(company=company)
        filtered = SharingEnforcer.enforce_sharing(
            queryset=queryset,
            user=other_user,
            company=company,
            object_type='lead',
            ownership_field='owner'
        )
        
        assert filtered.count() == 1
        assert qualified_lead in filtered
        assert new_lead not in filtered
    
    def test_explicit_record_share_access(self, setup_data):
        """Test explicit record sharing"""
        company = setup_data['company']
        owner = setup_data['owner']
        other_user = setup_data['other_user']
        
        # Create lead owned by owner
        lead = Lead.objects.create(
            company=company,
            first_name='Alice',
            last_name='Williams',
            status='new',
            owner=owner
        )
        
        # Create explicit share with other_user
        share = RecordShare.objects.create(
            company=company,
            object_type='lead',
            object_id=lead.id,
            user=other_user,
            access_level='read_only'
        )
        
        # other_user should see the lead due to explicit share
        queryset = Lead.objects.filter(company=company)
        filtered = SharingEnforcer.enforce_sharing(
            queryset=queryset,
            user=other_user,
            company=company,
            object_type='lead',
            ownership_field='owner'
        )
        
        assert filtered.count() == 1
        assert lead in filtered
    
    def test_default_deny_with_no_access(self, setup_data):
        """Test default deny when no ownership, rule, or share"""
        company = setup_data['company']
        owner = setup_data['owner']
        unrelated_user = setup_data['unrelated_user']
        
        # Create lead owned by owner
        lead = Lead.objects.create(
            company=company,
            first_name='Charlie',
            last_name='Brown',
            status='new',
            owner=owner
        )
        
        # Unrelated user with no ownership, no matching rules, no shares
        queryset = Lead.objects.filter(company=company)
        filtered = SharingEnforcer.enforce_sharing(
            queryset=queryset,
            user=unrelated_user,
            company=company,
            object_type='lead',
            ownership_field='owner'
        )
        
        # Should return empty queryset (default deny)
        assert filtered.count() == 0
    
    def test_multiple_rules_or_semantics(self, setup_data):
        """Test that multiple rules are combined with OR"""
        company = setup_data['company']
        owner = setup_data['owner']
        other_user = setup_data['other_user']
        
        # Create leads with different statuses
        qualified_lead = Lead.objects.create(
            company=company,
            first_name='Lead1',
            last_name='Qualified',
            status='qualified',
            owner=owner
        )
        
        converted_lead = Lead.objects.create(
            company=company,
            first_name='Lead2',
            last_name='Converted',
            status='converted',
            owner=owner
        )
        
        new_lead = Lead.objects.create(
            company=company,
            first_name='Lead3',
            last_name='New',
            status='new',
            owner=owner
        )
        
        # Create rule for qualified leads
        rule1 = SharingRule.objects.create(
            company=company,
            name='Qualified Leads',
            object_type='lead',
            predicate={'field': 'status', 'operator': 'eq', 'value': 'qualified'},
            access_level='read_only',
            is_active=True
        )
        
        # Create rule for converted leads
        rule2 = SharingRule.objects.create(
            company=company,
            name='Converted Leads',
            object_type='lead',
            predicate={'field': 'status', 'operator': 'eq', 'value': 'converted'},
            access_level='read_only',
            is_active=True
        )
        
        # other_user should see both qualified and converted leads (OR semantics)
        queryset = Lead.objects.filter(company=company)
        filtered = SharingEnforcer.enforce_sharing(
            queryset=queryset,
            user=other_user,
            company=company,
            object_type='lead',
            ownership_field='owner'
        )
        
        assert filtered.count() == 2
        assert qualified_lead in filtered
        assert converted_lead in filtered
        assert new_lead not in filtered
    
    def test_can_user_access_record_ownership(self, setup_data):
        """Test can_user_access_record with ownership"""
        company = setup_data['company']
        owner = setup_data['owner']
        other_user = setup_data['other_user']
        
        lead = Lead.objects.create(
            company=company,
            first_name='Test',
            last_name='Lead',
            status='new',
            owner=owner
        )
        
        # Owner should have access
        assert SharingEnforcer.can_user_access_record(
            user=owner,
            company=company,
            record=lead,
            object_type='lead',
            ownership_field='owner'
        )
        
        # Other user should not have access
        assert not SharingEnforcer.can_user_access_record(
            user=other_user,
            company=company,
            record=lead,
            object_type='lead',
            ownership_field='owner'
        )
    
    def test_can_user_access_record_via_rule(self, setup_data):
        """Test can_user_access_record with matching rule"""
        company = setup_data['company']
        owner = setup_data['owner']
        other_user = setup_data['other_user']
        
        lead = Lead.objects.create(
            company=company,
            first_name='Test',
            last_name='Lead',
            status='qualified',
            owner=owner
        )
        
        # Create rule
        rule = SharingRule.objects.create(
            company=company,
            name='Qualified Leads',
            object_type='lead',
            predicate={'field': 'status', 'operator': 'eq', 'value': 'qualified'},
            access_level='read_only',
            is_active=True
        )
        
        # Other user should have access via rule
        assert SharingEnforcer.can_user_access_record(
            user=other_user,
            company=company,
            record=lead,
            object_type='lead',
            ownership_field='owner'
        )
    
    def test_can_user_access_record_via_share(self, setup_data):
        """Test can_user_access_record with explicit share"""
        company = setup_data['company']
        owner = setup_data['owner']
        other_user = setup_data['other_user']
        
        lead = Lead.objects.create(
            company=company,
            first_name='Test',
            last_name='Lead',
            status='new',
            owner=owner
        )
        
        # Create share
        share = RecordShare.objects.create(
            company=company,
            object_type='lead',
            object_id=lead.id,
            user=other_user,
            access_level='read_only'
        )
        
        # Other user should have access via share
        assert SharingEnforcer.can_user_access_record(
            user=other_user,
            company=company,
            record=lead,
            object_type='lead',
            ownership_field='owner'
        )
    
    def test_inactive_rules_ignored(self, setup_data):
        """Test that inactive rules are not applied"""
        company = setup_data['company']
        owner = setup_data['owner']
        other_user = setup_data['other_user']
        
        lead = Lead.objects.create(
            company=company,
            first_name='Test',
            last_name='Lead',
            status='qualified',
            owner=owner
        )
        
        # Create inactive rule
        rule = SharingRule.objects.create(
            company=company,
            name='Qualified Leads',
            object_type='lead',
            predicate={'field': 'status', 'operator': 'eq', 'value': 'qualified'},
            access_level='read_only',
            is_active=False  # INACTIVE
        )
        
        # other_user should NOT see the lead
        queryset = Lead.objects.filter(company=company)
        filtered = SharingEnforcer.enforce_sharing(
            queryset=queryset,
            user=other_user,
            company=company,
            object_type='lead',
            ownership_field='owner'
        )
        
        assert filtered.count() == 0
