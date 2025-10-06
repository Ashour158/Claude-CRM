# tests/test_field_permissions.py
# Tests for Field-Level Permissions Phase 4+

import pytest
from django.contrib.auth import get_user_model
from core.models import Company
from core.permissions_models import (
    Role, RoleFieldPermission, GDPRRegistry, MaskingAuditLog
)
from core.permissions_service import (
    FieldPermissionService, MaskingService
)

User = get_user_model()

@pytest.fixture
def company(db):
    return Company.objects.create(
        name="Test Company",
        code="TEST001"
    )

@pytest.fixture
def user(db):
    return User.objects.create_user(
        email="test@example.com",
        password="testpass123"
    )

@pytest.fixture
def sales_role(db, company):
    return Role.objects.create(
        company=company,
        name="sales_rep",
        description="Sales Representative"
    )

@pytest.fixture
def marketing_role(db, company):
    return Role.objects.create(
        company=company,
        name="marketing",
        description="Marketing User"
    )

class TestRoleFieldPermission:
    """Test role field permission model"""
    
    @pytest.mark.django_db
    def test_create_field_permission(self, sales_role):
        """Test creating a field permission"""
        perm = RoleFieldPermission.objects.create(
            role=sales_role,
            company=sales_role.company,
            object_type="lead",
            field_name="email",
            mode="mask"
        )
        
        assert perm.role == sales_role
        assert perm.object_type == "lead"
        assert perm.field_name == "email"
        assert perm.mode == "mask"
    
    @pytest.mark.django_db
    def test_unique_constraint(self, sales_role):
        """Test that role + object_type + field_name must be unique"""
        RoleFieldPermission.objects.create(
            role=sales_role,
            company=sales_role.company,
            object_type="lead",
            field_name="email",
            mode="mask"
        )
        
        # Creating duplicate should raise error
        with pytest.raises(Exception):
            RoleFieldPermission.objects.create(
                role=sales_role,
                company=sales_role.company,
                object_type="lead",
                field_name="email",
                mode="view"
            )

class TestFieldPermissionService:
    """Test field permission service"""
    
    @pytest.mark.django_db
    def test_get_field_permissions(self, sales_role):
        """Test retrieving field permissions for a role"""
        RoleFieldPermission.objects.create(
            role=sales_role,
            company=sales_role.company,
            object_type="lead",
            field_name="email",
            mode="mask"
        )
        RoleFieldPermission.objects.create(
            role=sales_role,
            company=sales_role.company,
            object_type="lead",
            field_name="ssn",
            mode="hidden"
        )
        
        perms = FieldPermissionService.get_field_permissions(sales_role, "lead")
        
        assert perms["email"] == "mask"
        assert perms["ssn"] == "hidden"
    
    @pytest.mark.django_db
    def test_can_view_field_visible(self, sales_role):
        """Test can_view_field for visible field"""
        RoleFieldPermission.objects.create(
            role=sales_role,
            company=sales_role.company,
            object_type="lead",
            field_name="email",
            mode="view"
        )
        
        can_view = FieldPermissionService.can_view_field(
            sales_role, "lead", "email"
        )
        
        assert can_view is True
    
    @pytest.mark.django_db
    def test_can_view_field_hidden(self, sales_role):
        """Test can_view_field for hidden field"""
        RoleFieldPermission.objects.create(
            role=sales_role,
            company=sales_role.company,
            object_type="lead",
            field_name="ssn",
            mode="hidden"
        )
        
        can_view = FieldPermissionService.can_view_field(
            sales_role, "lead", "ssn"
        )
        
        assert can_view is False
    
    @pytest.mark.django_db
    def test_can_edit_field(self, sales_role):
        """Test can_edit_field check"""
        RoleFieldPermission.objects.create(
            role=sales_role,
            company=sales_role.company,
            object_type="lead",
            field_name="status",
            mode="edit"
        )
        RoleFieldPermission.objects.create(
            role=sales_role,
            company=sales_role.company,
            object_type="lead",
            field_name="email",
            mode="view"
        )
        
        assert FieldPermissionService.can_edit_field(sales_role, "lead", "status") is True
        assert FieldPermissionService.can_edit_field(sales_role, "lead", "email") is False
    
    @pytest.mark.django_db
    def test_should_mask_field(self, sales_role):
        """Test should_mask_field check"""
        RoleFieldPermission.objects.create(
            role=sales_role,
            company=sales_role.company,
            object_type="lead",
            field_name="email",
            mode="mask"
        )
        
        assert FieldPermissionService.should_mask_field(sales_role, "lead", "email") is True
    
    @pytest.mark.django_db
    def test_filter_fields_for_role_hides_hidden(self, sales_role):
        """Test that hidden fields are filtered out"""
        RoleFieldPermission.objects.create(
            role=sales_role,
            company=sales_role.company,
            object_type="lead",
            field_name="ssn",
            mode="hidden"
        )
        
        data = {
            "name": "John Doe",
            "email": "john@example.com",
            "ssn": "123-45-6789"
        }
        
        filtered = FieldPermissionService.filter_fields_for_role(
            data, sales_role, "lead", apply_masking=False
        )
        
        assert "name" in filtered
        assert "email" in filtered
        assert "ssn" not in filtered  # Hidden field removed
    
    @pytest.mark.django_db
    def test_filter_fields_for_role_masks_masked(self, sales_role, company):
        """Test that masked fields are masked"""
        RoleFieldPermission.objects.create(
            role=sales_role,
            company=company,
            object_type="lead",
            field_name="email",
            mode="mask"
        )
        GDPRRegistry.objects.create(
            company=company,
            object_type="lead",
            field_name="email",
            mask_type="partial",
            mask_config={"show_first": 2}
        )
        
        data = {
            "name": "John Doe",
            "email": "john@example.com"
        }
        
        filtered = FieldPermissionService.filter_fields_for_role(
            data, sales_role, "lead", apply_masking=True
        )
        
        assert "name" in filtered
        assert "email" in filtered
        assert filtered["email"] != "john@example.com"  # Should be masked
        assert "*" in filtered["email"]  # Should contain mask char

class TestGDPRRegistry:
    """Test GDPR registry model"""
    
    @pytest.mark.django_db
    def test_create_gdpr_registry_entry(self, company):
        """Test creating GDPR registry entry"""
        entry = GDPRRegistry.objects.create(
            company=company,
            object_type="lead",
            field_name="email",
            mask_type="partial",
            mask_config={"show_first": 2, "show_last": 0},
            is_pii=True
        )
        
        assert entry.object_type == "lead"
        assert entry.field_name == "email"
        assert entry.mask_type == "partial"
        assert entry.is_pii is True

class TestMaskingService:
    """Test masking service"""
    
    @pytest.mark.django_db
    def test_mask_field_hash(self, company):
        """Test hash masking"""
        GDPRRegistry.objects.create(
            company=company,
            object_type="lead",
            field_name="ssn",
            mask_type="hash",
            is_pii=True
        )
        
        masked = MaskingService.mask_field(
            "123-45-6789",
            "lead",
            "ssn",
            company
        )
        
        assert masked != "123-45-6789"
        assert masked.startswith("hash:")
    
    @pytest.mark.django_db
    def test_mask_field_partial(self, company):
        """Test partial masking"""
        GDPRRegistry.objects.create(
            company=company,
            object_type="lead",
            field_name="email",
            mask_type="partial",
            mask_config={"show_first": 2, "show_last": 2, "mask_char": "*"}
        )
        
        masked = MaskingService.mask_field(
            "john@example.com",
            "lead",
            "email",
            company
        )
        
        assert masked != "john@example.com"
        assert masked.startswith("jo")  # First 2 chars
        assert masked.endswith("om")  # Last 2 chars
        assert "*" in masked  # Contains mask char
    
    @pytest.mark.django_db
    def test_mask_field_redact(self, company):
        """Test redaction masking"""
        GDPRRegistry.objects.create(
            company=company,
            object_type="lead",
            field_name="ssn",
            mask_type="redact"
        )
        
        masked = MaskingService.mask_field(
            "123-45-6789",
            "lead",
            "ssn",
            company
        )
        
        assert masked == "[REDACTED]"
    
    @pytest.mark.django_db
    def test_mask_field_tokenize(self, company):
        """Test tokenization masking"""
        GDPRRegistry.objects.create(
            company=company,
            object_type="lead",
            field_name="email",
            mask_type="tokenize"
        )
        
        masked = MaskingService.mask_field(
            "john@example.com",
            "lead",
            "email",
            company
        )
        
        assert masked != "john@example.com"
        assert masked.startswith("token_")
    
    @pytest.mark.django_db
    def test_mask_field_no_config_defaults_to_redact(self, company):
        """Test that missing config defaults to redaction"""
        masked = MaskingService.mask_field(
            "sensitive-data",
            "lead",
            "some_field",
            company
        )
        
        assert masked == "[REDACTED]"
    
    @pytest.mark.django_db
    def test_mask_field_null_value(self, company):
        """Test masking null value"""
        masked = MaskingService.mask_field(
            None,
            "lead",
            "email",
            company
        )
        
        assert masked is None
    
    @pytest.mark.django_db
    def test_mask_field_empty_string(self, company):
        """Test masking empty string"""
        masked = MaskingService.mask_field(
            "",
            "lead",
            "email",
            company
        )
        
        assert masked == ""

class TestMaskingAuditLog:
    """Test masking audit logging"""
    
    @pytest.mark.django_db
    def test_log_masking_decision(self, user, company):
        """Test logging masking decision"""
        # Setup user's company access
        from core.models import UserCompanyAccess
        UserCompanyAccess.objects.create(
            user=user,
            company=company,
            is_active=True
        )
        
        MaskingService.log_masking_decision(
            user=user,
            object_type="lead",
            object_id="lead-123",
            field_name="email",
            action="masked",
            reason="mask mode for sales_rep role"
        )
        
        # Verify log created
        log = MaskingAuditLog.objects.filter(
            user=user,
            object_type="lead",
            object_id="lead-123",
            field_name="email"
        ).first()
        
        assert log is not None
        assert log.action == "masked"
        assert "mask mode" in log.reason

class TestPermissionModes:
    """Test different permission mode combinations"""
    
    @pytest.mark.django_db
    def test_view_mode_shows_full_data(self, sales_role, company):
        """Test view mode shows complete data"""
        RoleFieldPermission.objects.create(
            role=sales_role,
            company=company,
            object_type="lead",
            field_name="email",
            mode="view"
        )
        
        data = {"email": "john@example.com"}
        filtered = FieldPermissionService.filter_fields_for_role(
            data, sales_role, "lead"
        )
        
        assert filtered["email"] == "john@example.com"
    
    @pytest.mark.django_db
    def test_mask_mode_masks_data(self, sales_role, company):
        """Test mask mode masks data"""
        RoleFieldPermission.objects.create(
            role=sales_role,
            company=company,
            object_type="lead",
            field_name="email",
            mode="mask"
        )
        GDPRRegistry.objects.create(
            company=company,
            object_type="lead",
            field_name="email",
            mask_type="redact"
        )
        
        data = {"email": "john@example.com"}
        filtered = FieldPermissionService.filter_fields_for_role(
            data, sales_role, "lead"
        )
        
        assert filtered["email"] == "[REDACTED]"
    
    @pytest.mark.django_db
    def test_hidden_mode_removes_field(self, sales_role):
        """Test hidden mode removes field entirely"""
        RoleFieldPermission.objects.create(
            role=sales_role,
            company=sales_role.company,
            object_type="lead",
            field_name="ssn",
            mode="hidden"
        )
        
        data = {"name": "John", "ssn": "123-45-6789"}
        filtered = FieldPermissionService.filter_fields_for_role(
            data, sales_role, "lead"
        )
        
        assert "name" in filtered
        assert "ssn" not in filtered
    
    @pytest.mark.django_db
    def test_edit_mode_allows_full_access(self, sales_role, company):
        """Test edit mode allows full access"""
        RoleFieldPermission.objects.create(
            role=sales_role,
            company=company,
            object_type="lead",
            field_name="status",
            mode="edit"
        )
        
        data = {"status": "qualified"}
        filtered = FieldPermissionService.filter_fields_for_role(
            data, sales_role, "lead"
        )
        
        assert filtered["status"] == "qualified"

class TestMultipleRoles:
    """Test scenarios with multiple roles"""
    
    @pytest.mark.django_db
    def test_different_roles_different_permissions(self, sales_role, marketing_role, company):
        """Test that different roles have different permissions"""
        # Sales can view email
        RoleFieldPermission.objects.create(
            role=sales_role,
            company=company,
            object_type="lead",
            field_name="email",
            mode="view"
        )
        
        # Marketing has email masked
        RoleFieldPermission.objects.create(
            role=marketing_role,
            company=company,
            object_type="lead",
            field_name="email",
            mode="mask"
        )
        
        GDPRRegistry.objects.create(
            company=company,
            object_type="lead",
            field_name="email",
            mask_type="redact"
        )
        
        data = {"email": "john@example.com"}
        
        # Sales sees full email
        sales_filtered = FieldPermissionService.filter_fields_for_role(
            data, sales_role, "lead"
        )
        assert sales_filtered["email"] == "john@example.com"
        
        # Marketing sees masked email
        marketing_filtered = FieldPermissionService.filter_fields_for_role(
            data, marketing_role, "lead"
        )
        assert marketing_filtered["email"] == "[REDACTED]"

class TestMaskingEdgeCases:
    """Test edge cases in masking"""
    
    @pytest.mark.django_db
    def test_partial_mask_short_string(self, company):
        """Test partial masking on very short string"""
        GDPRRegistry.objects.create(
            company=company,
            object_type="lead",
            field_name="code",
            mask_type="partial",
            mask_config={"show_first": 2, "show_last": 2}
        )
        
        # String too short
        masked = MaskingService.mask_field("ab", "lead", "code", company)
        
        # Should handle gracefully
        assert masked != "ab"
        assert len(masked) >= 2
    
    @pytest.mark.django_db
    def test_mask_special_characters(self, company):
        """Test masking strings with special characters"""
        GDPRRegistry.objects.create(
            company=company,
            object_type="lead",
            field_name="email",
            mask_type="partial",
            mask_config={"show_first": 2, "show_last": 2}
        )
        
        masked = MaskingService.mask_field(
            "test+tag@example.com",
            "lead",
            "email",
            company
        )
        
        assert masked != "test+tag@example.com"
        assert masked.startswith("te")
