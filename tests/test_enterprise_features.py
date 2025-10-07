# tests/test_enterprise_features.py
# Comprehensive tests for enterprise parity gap features

from django.test import TestCase
from django.contrib.auth import get_user_model
from analytics.models import Report, SalesForecast
from territories.models import Territory
from workflow.models import ApprovalProcess, ApprovalRequest
from data_import.models import ImportTemplate, ImportJob, DuplicateRule
from api_versioning.models import APIVersion, APIEndpoint, APIClient
from marketplace.models import Plugin, PluginInstallation
from audit.models import AuditLog, AuditPolicy
from core.models import Company
from datetime import date, datetime
from decimal import Decimal

User = get_user_model()


class ReportingTests(TestCase):
    """Tests for interactive reporting pivot UI"""
    
    def setUp(self):
        self.company = Company.objects.create(name="Test Company")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            company=self.company
        )
    
    def test_create_pivot_report(self):
        """Test creating an interactive pivot report"""
        report = Report.objects.create(
            company=self.company,
            name="Sales Pivot",
            report_type="interactive_pivot",
            data_source="deals",
            owner=self.user,
            pivot_rows=["territory", "product"],
            pivot_columns=["stage"],
            pivot_values=[{"field": "amount", "aggregation": "sum"}],
            chart_config={"type": "bar", "x_axis": "territory"}
        )
        self.assertEqual(report.report_type, "interactive_pivot")
        self.assertEqual(len(report.pivot_rows), 2)
    
    def test_scheduled_report(self):
        """Test scheduled report delivery"""
        report = Report.objects.create(
            company=self.company,
            name="Weekly Sales",
            report_type="table",
            data_source="sales",
            owner=self.user,
            is_scheduled=True,
            schedule_frequency="weekly",
            schedule_recipients=["manager@example.com"],
            delivery_format="pdf"
        )
        self.assertTrue(report.is_scheduled)
        self.assertEqual(report.schedule_frequency, "weekly")
        self.assertEqual(report.delivery_format, "pdf")


class TerritoryHierarchyTests(TestCase):
    """Tests for territory hierarchy features"""
    
    def setUp(self):
        self.company = Company.objects.create(name="Test Company")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            company=self.company
        )
    
    def test_territory_hierarchy(self):
        """Test creating a territory hierarchy"""
        north_america = Territory.objects.create(
            company=self.company,
            name="North America",
            code="NA",
            type="geographic",
            rollup_metrics=True
        )
        
        west = Territory.objects.create(
            company=self.company,
            name="West",
            code="WEST",
            parent_territory=north_america,
            share_with_parent=True
        )
        
        california = Territory.objects.create(
            company=self.company,
            name="California",
            code="CA",
            parent_territory=west
        )
        
        # Test hierarchy methods
        hierarchy = california.get_territory_hierarchy()
        self.assertEqual(len(hierarchy), 3)
        self.assertEqual(hierarchy[0], north_america)
        self.assertEqual(hierarchy[2], california)
    
    def test_get_all_children(self):
        """Test getting all child territories"""
        parent = Territory.objects.create(
            company=self.company,
            name="Parent",
            code="P"
        )
        
        child1 = Territory.objects.create(
            company=self.company,
            name="Child 1",
            code="C1",
            parent_territory=parent
        )
        
        child2 = Territory.objects.create(
            company=self.company,
            name="Child 2",
            code="C2",
            parent_territory=parent
        )
        
        grandchild = Territory.objects.create(
            company=self.company,
            name="Grandchild",
            code="GC",
            parent_territory=child1
        )
        
        children = parent.get_all_children(include_self=False)
        self.assertEqual(len(children), 3)  # 2 children + 1 grandchild
    
    def test_recursive_sharing(self):
        """Test recursive sharing configuration"""
        territory = Territory.objects.create(
            company=self.company,
            name="Test Territory",
            code="TT",
            share_with_parent=True,
            share_with_children=True,
            recursive_sharing=True
        )
        self.assertTrue(territory.recursive_sharing)


class ApprovalChainTests(TestCase):
    """Tests for multi-step approval chains"""
    
    def setUp(self):
        self.company = Company.objects.create(name="Test Company")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            company=self.company
        )
    
    def test_multi_step_approval(self):
        """Test multi-step approval process"""
        process = ApprovalProcess.objects.create(
            company=self.company,
            name="Discount Approval",
            process_type="multi_step",
            entity_type="deal",
            owner=self.user,
            steps=[
                {"step": 1, "approvers": ["manager@example.com"]},
                {"step": 2, "approvers": ["director@example.com"]}
            ],
            require_all_approvers=True
        )
        self.assertEqual(process.process_type, "multi_step")
        self.assertEqual(len(process.steps), 2)
    
    def test_parallel_approval(self):
        """Test parallel approval process"""
        process = ApprovalProcess.objects.create(
            company=self.company,
            name="Budget Approval",
            process_type="parallel",
            entity_type="expense",
            owner=self.user,
            approvers=["director1@example.com", "director2@example.com"],
            require_all_approvers=False
        )
        self.assertEqual(process.process_type, "parallel")
        self.assertFalse(process.require_all_approvers)
    
    def test_escalation(self):
        """Test escalation configuration"""
        process = ApprovalProcess.objects.create(
            company=self.company,
            name="High Value Deal",
            process_type="escalation",
            entity_type="deal",
            owner=self.user,
            enable_escalation=True,
            escalation_after_hours=24,
            escalation_chain=["vp@example.com", "ceo@example.com"]
        )
        self.assertTrue(process.enable_escalation)
        self.assertEqual(process.escalation_after_hours, 24)
        self.assertEqual(len(process.escalation_chain), 2)


class ForecastingTests(TestCase):
    """Tests for weighted pipeline forecasting"""
    
    def setUp(self):
        self.company = Company.objects.create(name="Test Company")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            company=self.company
        )
    
    def test_weighted_forecast(self):
        """Test weighted pipeline forecast"""
        forecast = SalesForecast.objects.create(
            company=self.company,
            name="Q4 Forecast",
            forecast_type="weighted",
            period_start=date(2024, 10, 1),
            period_end=date(2024, 12, 31),
            forecasted_amount=Decimal("1000000.00"),
            weighted_amount=Decimal("750000.00"),
            methodology="Stage probability weighting",
            owner=self.user,
            stage_weights={
                "prospecting": 0.1,
                "qualification": 0.2,
                "proposal": 0.5,
                "negotiation": 0.75,
                "closed_won": 1.0
            }
        )
        self.assertEqual(forecast.forecast_type, "weighted")
        self.assertEqual(len(forecast.stage_weights), 5)
    
    def test_scenario_modeling(self):
        """Test scenario modeling"""
        forecast = SalesForecast.objects.create(
            company=self.company,
            name="Revenue Scenarios",
            forecast_type="scenario",
            period_start=date(2024, 10, 1),
            period_end=date(2024, 12, 31),
            forecasted_amount=Decimal("1000000.00"),
            best_case_amount=Decimal("1200000.00"),
            worst_case_amount=Decimal("800000.00"),
            methodology="Scenario analysis",
            owner=self.user,
            scenarios=[
                {"name": "conservative", "adjustment": 0.8},
                {"name": "aggressive", "adjustment": 1.2}
            ],
            selected_scenario="conservative"
        )
        self.assertEqual(len(forecast.scenarios), 2)
        self.assertEqual(forecast.selected_scenario, "conservative")


class DataImportTests(TestCase):
    """Tests for data import and deduplication"""
    
    def setUp(self):
        self.company = Company.objects.create(name="Test Company")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            company=self.company
        )
    
    def test_import_template(self):
        """Test creating an import template"""
        template = ImportTemplate.objects.create(
            company=self.company,
            name="Contact Import",
            entity_type="contact",
            owner=self.user,
            field_mapping={
                "First Name": "first_name",
                "Last Name": "last_name",
                "Email": "email"
            },
            required_fields=["first_name", "last_name", "email"],
            dedupe_enabled=True,
            dedupe_fields=["email"],
            dedupe_strategy="skip"
        )
        self.assertEqual(template.entity_type, "contact")
        self.assertTrue(template.dedupe_enabled)
    
    def test_duplicate_rule(self):
        """Test duplicate detection rule"""
        rule = DuplicateRule.objects.create(
            company=self.company,
            name="Email Match",
            entity_type="contact",
            owner=self.user,
            match_fields=["email"],
            match_type="exact",
            match_threshold=Decimal("100.0"),
            field_weights={"email": 1.0}
        )
        self.assertEqual(rule.match_type, "exact")
        self.assertEqual(rule.match_threshold, Decimal("100.0"))


class APIVersioningTests(TestCase):
    """Tests for API versioning"""
    
    def test_api_version(self):
        """Test creating an API version"""
        version = APIVersion.objects.create(
            version_number="v2",
            version_name="Version 2.0",
            status="stable",
            is_default=True,
            is_active=True,
            release_date=date(2024, 10, 1)
        )
        self.assertEqual(version.version_number, "v2")
        self.assertTrue(version.is_default)
    
    def test_api_endpoint(self):
        """Test API endpoint versioning"""
        version = APIVersion.objects.create(
            version_number="v2",
            status="stable"
        )
        
        endpoint = APIEndpoint.objects.create(
            path="/api/accounts/",
            method="GET",
            api_version=version,
            serializer_class="accounts.serializers.AccountSerializerV2",
            field_mappings={"customer": "account"}
        )
        self.assertEqual(endpoint.api_version, version)
        self.assertEqual(endpoint.method, "GET")


class MarketplaceTests(TestCase):
    """Tests for marketplace plugin kernel"""
    
    def setUp(self):
        self.company = Company.objects.create(name="Test Company")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            company=self.company
        )
    
    def test_plugin(self):
        """Test creating a plugin"""
        plugin = Plugin.objects.create(
            plugin_id="salesforce-sync",
            name="Salesforce Sync",
            description="Sync with Salesforce",
            plugin_type="integration",
            version="1.0.0",
            developer_name="Test Developer",
            developer_email="dev@example.com",
            manifest={
                "entry_point": "plugins.salesforce.main",
                "permissions": ["read:accounts"]
            },
            is_free=False,
            price=Decimal("99.00"),
            pricing_model="subscription"
        )
        self.assertEqual(plugin.plugin_type, "integration")
        self.assertFalse(plugin.is_free)
    
    def test_plugin_installation(self):
        """Test plugin installation"""
        plugin = Plugin.objects.create(
            plugin_id="test-plugin",
            name="Test Plugin",
            description="Test",
            plugin_type="widget",
            version="1.0.0",
            developer_name="Test",
            developer_email="test@example.com"
        )
        
        installation = PluginInstallation.objects.create(
            company=self.company,
            plugin=plugin,
            installed_version="1.0.0",
            status="active",
            is_enabled=True,
            installed_by=self.user
        )
        self.assertEqual(installation.status, "active")
        self.assertTrue(installation.is_enabled)


class AuditTests(TestCase):
    """Tests for audit explorer"""
    
    def setUp(self):
        self.company = Company.objects.create(name="Test Company")
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            company=self.company
        )
    
    def test_audit_log(self):
        """Test creating an audit log entry"""
        log = AuditLog.objects.create(
            company=self.company,
            user=self.user,
            user_email=self.user.email,
            action="update",
            action_description="Updated account",
            entity_type="account",
            entity_id="123",
            entity_name="Acme Corp",
            old_values={"name": "Old Name"},
            new_values={"name": "New Name"},
            changed_fields=["name"],
            is_sensitive=False
        )
        self.assertEqual(log.action, "update")
        self.assertEqual(log.entity_type, "account")
        self.assertIn("name", log.changed_fields)
    
    def test_audit_policy(self):
        """Test audit policy"""
        policy = AuditPolicy.objects.create(
            company=self.company,
            name="Sensitive Data Policy",
            description="Monitor sensitive data access",
            owner=self.user,
            rules=[
                {"condition": "is_sensitive == True", "alert": True}
            ],
            applies_to_entities=["account", "contact"],
            applies_to_actions=["read", "update"],
            alert_on_violation=True,
            retention_days=2555
        )
        self.assertEqual(policy.name, "Sensitive Data Policy")
        self.assertTrue(policy.alert_on_violation)
        self.assertEqual(policy.retention_days, 2555)


# Run all tests
if __name__ == '__main__':
    import unittest
    unittest.main()
