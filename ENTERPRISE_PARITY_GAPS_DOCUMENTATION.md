# Enterprise Parity Gaps - Feature Documentation

This document describes all enterprise features implemented to close the parity gaps with leading CRM systems.

## 1. Interactive Reporting Pivot UI

### Overview
Advanced reporting system with interactive pivot tables, chart builder, and scheduled delivery.

### Features
- **Interactive Pivot Tables**: Dynamic row/column pivoting with aggregation functions
- **Chart Builder**: Multiple chart types (bar, line, pie, area, scatter, heatmap, gauge)
- **Scheduled Delivery**: Automated report generation and email delivery
- **Export Formats**: PDF, Excel, CSV, HTML

### Models
- `Report`: Enhanced with pivot configuration and chart builder settings
  - `pivot_rows`, `pivot_columns`, `pivot_values`: Pivot table configuration
  - `pivot_filters`: Pivot-specific filters
  - `chart_config`: Chart visualization settings
  - `schedule_recipients`: Email list for scheduled delivery
  - `delivery_format`: Export format selection

### API Endpoints
- `GET /api/v1/analytics/reports/` - List all reports
- `POST /api/v1/analytics/reports/` - Create new report
- `GET /api/v1/analytics/reports/{id}/` - Get report details
- `PATCH /api/v1/analytics/reports/{id}/` - Update report
- `DELETE /api/v1/analytics/reports/{id}/` - Delete report

### Example Usage
```python
# Create an interactive pivot report
report = {
    "name": "Sales by Territory & Product",
    "report_type": "interactive_pivot",
    "data_source": "deals",
    "pivot_rows": ["territory", "product"],
    "pivot_columns": ["stage", "quarter"],
    "pivot_values": [
        {"field": "amount", "aggregation": "sum"},
        {"field": "count", "aggregation": "count"}
    ],
    "chart_config": {
        "type": "bar",
        "x_axis": "territory",
        "y_axis": "amount",
        "color_by": "stage"
    },
    "is_scheduled": true,
    "schedule_frequency": "weekly",
    "schedule_recipients": ["manager@example.com", "exec@example.com"],
    "delivery_format": "pdf"
}
```

---

## 2. Territory Hierarchy

### Overview
Comprehensive territory management with tree structure, roll-up metrics, and recursive sharing.

### Features
- **Hierarchical Structure**: Parent-child territory relationships with unlimited depth
- **Tree Operations**: Get all children, get all parents, traverse hierarchy
- **Roll-up Metrics**: Aggregate metrics up the hierarchy tree
- **Recursive Sharing**: Share records with all descendants
- **Hierarchy Path**: Full path tracking for efficient queries

### Models
- `Territory`: Enhanced with hierarchy features
  - `hierarchy_level`: Depth in the tree (0 = root)
  - `hierarchy_path`: Full path (e.g., "/north-america/west/california/")
  - `share_with_parent`: Share records with parent territory
  - `share_with_children`: Share records with children
  - `recursive_sharing`: Share with all descendants
  - `rollup_metrics`: Roll up metrics to parents

### New Methods
- `get_all_children(include_self=False)`: Get all descendant territories
- `get_all_parents(include_self=False)`: Get all ancestor territories
- `update_hierarchy_path()`: Update path based on parent

### API Endpoints
- `GET /api/v1/territories/` - List territories
- `POST /api/v1/territories/` - Create territory
- `GET /api/v1/territories/{id}/` - Get territory details
- `GET /api/v1/territories/{id}/children/` - Get child territories
- `GET /api/v1/territories/{id}/hierarchy/` - Get full hierarchy

### Example Usage
```python
# Create a territory hierarchy
north_america = Territory.objects.create(
    name="North America",
    code="NA",
    type="geographic",
    rollup_metrics=True
)

west_region = Territory.objects.create(
    name="West Region",
    code="WEST",
    parent_territory=north_america,
    share_with_parent=True,
    recursive_sharing=True
)

california = Territory.objects.create(
    name="California",
    code="CA",
    parent_territory=west_region
)

# Get all children recursively
all_children = north_america.get_all_children(include_self=True)
```

---

## 3. Multi-Step and Parallel Approval Chains

### Overview
Advanced approval workflows with multi-step processes, parallel approvals, and escalation.

### Features
- **Sequential Approval**: Step-by-step approval chain
- **Parallel Approval**: Multiple approvers at the same step
- **Conditional Approval**: Rules-based routing
- **Escalation**: Automatic escalation after timeout
- **Hybrid Workflows**: Mix of sequential and parallel steps

### Models
- `ApprovalProcess`: Enhanced with multi-step configuration
  - `steps`: Configuration for multi-step workflows
  - `current_step`: Track progress through steps
  - `require_all_approvers`: For parallel approvals
  - `enable_escalation`: Turn on/off escalation
  - `escalation_after_hours`: Timeout before escalation
  - `escalation_chain`: List of escalation users
  - `escalation_level`: Current escalation level

### API Endpoints
- `GET /api/v1/workflow/approval-processes/` - List approval processes
- `POST /api/v1/workflow/approval-processes/` - Create process
- `POST /api/v1/workflow/approval-requests/` - Submit approval request
- `POST /api/v1/workflow/approval-requests/{id}/approve/` - Approve
- `POST /api/v1/workflow/approval-requests/{id}/reject/` - Reject
- `POST /api/v1/workflow/approval-requests/{id}/escalate/` - Escalate

### Example Usage
```python
# Create a multi-step approval process with escalation
approval_process = {
    "name": "Discount Approval",
    "process_type": "multi_step",
    "entity_type": "deal",
    "steps": [
        {
            "step": 1,
            "name": "Manager Approval",
            "approvers": ["manager@example.com"],
            "type": "sequential"
        },
        {
            "step": 2,
            "name": "Director Approval",
            "approvers": ["director1@example.com", "director2@example.com"],
            "type": "parallel",
            "require_all": False  # Only need one director
        }
    ],
    "enable_escalation": True,
    "escalation_after_hours": 24,
    "escalation_chain": ["vp@example.com", "ceo@example.com"]
}
```

---

## 4. Weighted Pipeline Forecasting

### Overview
Advanced sales forecasting with weighted probabilities and scenario modeling.

### Features
- **Weighted Forecasting**: Apply probability weights by deal stage
- **Scenario Modeling**: Best case, worst case, and custom scenarios
- **Multiple Methodologies**: Support different forecasting approaches
- **Confidence Levels**: Track forecast accuracy

### Models
- `SalesForecast`: Enhanced with weighting and scenarios
  - `weighted_amount`: Forecast weighted by stage probabilities
  - `best_case_amount`: Best case scenario
  - `worst_case_amount`: Worst case scenario
  - `stage_weights`: Probability by stage
  - `scenarios`: List of scenario definitions
  - `selected_scenario`: Current active scenario

### API Endpoints
- `GET /api/v1/analytics/forecasts/` - List forecasts
- `POST /api/v1/analytics/forecasts/` - Create forecast
- `POST /api/v1/analytics/forecasts/{id}/calculate/` - Recalculate
- `POST /api/v1/analytics/forecasts/{id}/scenario/` - Switch scenario

### Example Usage
```python
# Create a weighted forecast with scenarios
forecast = {
    "name": "Q4 2024 Revenue Forecast",
    "forecast_type": "weighted",
    "period_start": "2024-10-01",
    "period_end": "2024-12-31",
    "forecasted_amount": 1000000,
    "stage_weights": {
        "prospecting": 0.10,
        "qualification": 0.20,
        "proposal": 0.50,
        "negotiation": 0.75,
        "closed_won": 1.00
    },
    "scenarios": [
        {
            "name": "conservative",
            "description": "Conservative estimate",
            "adjustment_factor": 0.8
        },
        {
            "name": "aggressive",
            "description": "Aggressive estimate",
            "adjustment_factor": 1.2
        }
    ],
    "selected_scenario": "conservative"
}
```

---

## 5. Import Staging & Deduplication Engine

### Overview
Robust data import system with staging area, field mapping, validation, and duplicate detection.

### Features
- **Import Templates**: Reusable field mapping configurations
- **Staging Area**: Preview and validate before import
- **Field Mapping**: Map source fields to target entity fields
- **Data Transformation**: Apply transformations during import
- **Validation Rules**: Field-level validation
- **Duplicate Detection**: Multiple matching algorithms
- **Deduplication Strategies**: Skip, update, merge, or create new

### Models
- `ImportTemplate`: Field mapping and validation rules
- `ImportJob`: Import job execution tracking
- `ImportStagingRecord`: Individual records in staging
- `DuplicateRule`: Duplicate detection configuration

### API Endpoints
- `GET /api/v1/data-import/templates/` - List import templates
- `POST /api/v1/data-import/templates/` - Create template
- `POST /api/v1/data-import/jobs/` - Start import job
- `GET /api/v1/data-import/jobs/{id}/staging/` - View staged records
- `POST /api/v1/data-import/jobs/{id}/start/` - Process import
- `GET /api/v1/data-import/duplicate-rules/` - List dedupe rules

### Example Usage
```python
# Create an import template with deduplication
template = {
    "name": "Contact Import",
    "entity_type": "contact",
    "field_mapping": {
        "First Name": "first_name",
        "Last Name": "last_name",
        "Email": "email",
        "Phone": "phone"
    },
    "transformation_rules": [
        {"field": "email", "transform": "lowercase"},
        {"field": "phone", "transform": "normalize_phone"}
    ],
    "required_fields": ["first_name", "last_name", "email"],
    "dedupe_enabled": True,
    "dedupe_fields": ["email"],
    "dedupe_strategy": "skip"
}

# Create duplicate detection rule
duplicate_rule = {
    "name": "Contact Email Match",
    "entity_type": "contact",
    "match_fields": ["email"],
    "match_type": "exact",
    "match_threshold": 100.0,
    "field_weights": {"email": 1.0}
}
```

---

## 6. Integration Provider Framework

### Overview
The existing integration models already support OAuth, calendar, and email integrations. No changes needed.

### Features Already Present
- OAuth configuration for calendar and email providers
- Calendar sync (Google, Outlook, Exchange, CalDAV)
- Email integration (SMTP, SendGrid, Mailgun, SES, etc.)
- Webhook configurations
- Data synchronization

---

## 7. API Versioning

### Overview
Backward-compatible API versioning with Accept-Version header support and version management.

### Features
- **Version Management**: Define and manage API versions
- **Endpoint Versioning**: Version-specific endpoint configurations
- **Client Tracking**: Track which clients use which versions
- **Request Logging**: Log requests by version for analytics
- **Deprecation Cycle**: Manage version lifecycle (development → stable → deprecated → sunset)

### Models
- `APIVersion`: API version definitions
- `APIEndpoint`: Version-specific endpoint configurations
- `APIClient`: Client registration and version preferences
- `APIRequestLog`: Request tracking by version

### API Endpoints
- `GET /api/v1/api-versioning/versions/` - List API versions
- `POST /api/v1/api-versioning/versions/` - Create version
- `POST /api/v1/api-versioning/versions/{id}/set-default/` - Set default
- `GET /api/v1/api-versioning/clients/` - List API clients
- `GET /api/v1/api-versioning/logs/` - View request logs

### Usage
```python
# Create a new API version
version = {
    "version_number": "v2",
    "version_name": "Version 2.0",
    "status": "stable",
    "is_default": True,
    "release_date": "2024-10-01",
    "changelog": "Added new fields and improved performance",
    "breaking_changes": "Renamed 'customer' to 'account'"
}

# Client specifies version in request
headers = {
    "Accept-Version": "v2"
}
```

---

## 8. Marketplace Plugin Kernel

### Overview
Plugin marketplace with manifest-based installation, execution runtime, and lifecycle management.

### Features
- **Plugin Marketplace**: Discover and install plugins
- **Manifest System**: Declare dependencies and permissions
- **Installation Lifecycle**: Install, activate, deactivate, uninstall
- **Execution Runtime**: Track plugin executions
- **Reviews & Ratings**: User feedback system
- **Version Management**: Plugin versioning and updates

### Models
- `Plugin`: Plugin definitions and marketplace listing
- `PluginInstallation`: Company-specific installations
- `PluginExecution`: Execution logs and tracking
- `PluginReview`: User reviews and ratings

### API Endpoints
- `GET /api/v1/marketplace/plugins/` - Browse marketplace
- `POST /api/v1/marketplace/plugins/{id}/install/` - Install plugin
- `GET /api/v1/marketplace/installations/` - List installed plugins
- `POST /api/v1/marketplace/installations/{id}/activate/` - Activate
- `POST /api/v1/marketplace/installations/{id}/deactivate/` - Deactivate
- `GET /api/v1/marketplace/executions/` - View execution logs

### Example Usage
```python
# Define a plugin
plugin = {
    "plugin_id": "salesforce-sync",
    "name": "Salesforce Sync",
    "plugin_type": "integration",
    "version": "1.0.0",
    "manifest": {
        "entry_point": "plugins.salesforce.main",
        "permissions": ["read:accounts", "write:contacts"],
        "dependencies": ["api-client-v2"],
        "config_schema": {
            "api_key": {"type": "string", "required": True},
            "sync_frequency": {"type": "int", "default": 3600}
        }
    },
    "min_system_version": "1.0.0",
    "is_free": False,
    "price": 99.00,
    "pricing_model": "subscription"
}

# Install plugin for a company
installation = {
    "plugin": plugin_id,
    "configuration": {
        "api_key": "sk_xxx",
        "sync_frequency": 1800
    },
    "enabled_features": ["contacts", "deals"]
}
```

---

## 9. Audit Explorer UI

### Overview
Comprehensive audit logging with explorer UI, compliance reports, and policy management.

### Features
- **Comprehensive Logging**: Track all system changes
- **Entity Tracking**: Generic foreign key to any entity
- **Change Details**: Before/after values with field-level tracking
- **Request Context**: IP, user agent, session info
- **Compliance Flags**: Mark sensitive data and require review
- **Export Capabilities**: Export audit logs in multiple formats
- **Compliance Reports**: Generate compliance and security reports
- `Audit Policies**: Define monitoring and alerting rules

### Models
- `AuditLog`: Comprehensive audit entries
- `AuditLogExport`: Export job tracking
- `ComplianceReport`: Compliance and security reports
- `AuditPolicy`: Audit and compliance policies

### API Endpoints
- `GET /api/v1/audit/logs/` - List audit logs
- `GET /api/v1/audit/logs/by-entity/` - Get logs for specific entity
- `POST /api/v1/audit/logs/{id}/review/` - Mark as reviewed
- `POST /api/v1/audit/exports/` - Create export job
- `GET /api/v1/audit/compliance-reports/` - List reports
- `POST /api/v1/audit/policies/` - Create audit policy

### Example Usage
```python
# Create an audit log entry
audit_log = {
    "action": "update",
    "action_description": "Updated account billing address",
    "entity_type": "account",
    "entity_id": "123",
    "entity_name": "Acme Corp",
    "old_values": {
        "billing_address": "123 Old St"
    },
    "new_values": {
        "billing_address": "456 New Ave"
    },
    "changed_fields": ["billing_address"],
    "is_sensitive": False,
    "requires_review": False
}

# Create an audit policy
policy = {
    "name": "Sensitive Data Access Policy",
    "description": "Monitor access to sensitive customer data",
    "rules": [
        {
            "condition": "is_sensitive == True",
            "alert": True
        }
    ],
    "applies_to_entities": ["account", "contact", "deal"],
    "applies_to_actions": ["read", "update", "export"],
    "alert_on_violation": True,
    "alert_recipients": ["compliance@example.com"],
    "retention_days": 2555  # 7 years
}
```

---

## Migration Guide

### Database Migrations
Run the following commands to apply all model changes:

```bash
python manage.py makemigrations analytics territories workflow data_import api_versioning marketplace audit
python manage.py migrate
```

### Settings Configuration
Add the new apps to `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    # ... existing apps ...
    'data_import',
    'api_versioning',
    'marketplace',
    'audit',
]
```

### URL Configuration
Add the new URL patterns to your main `urls.py`:

```python
urlpatterns = [
    # ... existing patterns ...
    path('api/v1/data-import/', include('data_import.urls')),
    path('api/v1/api-versioning/', include('api_versioning.urls')),
    path('api/v1/marketplace/', include('marketplace.urls')),
    path('api/v1/audit/', include('audit.urls')),
]
```

---

## Testing

Each module includes comprehensive test coverage. Run tests with:

```bash
# Test all new modules
python manage.py test data_import api_versioning marketplace audit

# Test specific module
python manage.py test data_import.tests
```

---

## Best Practices

### Report Development
- Use pivot tables for complex multi-dimensional analysis
- Schedule reports during off-peak hours
- Limit scheduled recipients to avoid email overload

### Territory Management
- Design hierarchy before creating territories
- Use recursive sharing cautiously (performance impact)
- Update hierarchy paths after structure changes

### Approval Workflows
- Start with simple sequential approvals
- Test escalation chains thoroughly
- Set reasonable timeout values

### Data Import
- Always use staging area for large imports
- Test field mappings with sample data first
- Configure duplicate rules before import

### API Versioning
- Plan major versions carefully
- Give clients 6-12 months to migrate
- Document breaking changes clearly

### Plugin Development
- Follow manifest schema strictly
- Test in sandbox before publishing
- Provide clear documentation

### Audit & Compliance
- Review policies regularly
- Archive old logs as needed
- Set appropriate retention periods

---

## Support

For questions or issues:
- Check the inline code documentation
- Review model definitions in each module
- Contact the development team

---

*Last Updated: 2024*
*Version: 1.0*
