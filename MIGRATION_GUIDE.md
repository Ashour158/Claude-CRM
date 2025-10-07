# MIGRATION_GUIDE.md - Enterprise Features

## Enterprise Parity Gaps Migration Guide

This guide will help you migrate and integrate the new enterprise features into your Claude-CRM installation.

---

## Pre-Migration Checklist

- [ ] Backup your database
- [ ] Review current system version
- [ ] Verify Python version >= 3.8
- [ ] Verify Django version >= 4.2
- [ ] Ensure all current migrations are applied
- [ ] Review disk space (recommend 10GB+ free)

---

## Step 1: Update Settings

### 1.1 Add New Apps to INSTALLED_APPS

Edit `config/settings.py`:

```python
INSTALLED_APPS = [
    # ... existing apps ...
    
    # Existing CRM modules
    'core',
    'crm',
    'deals',
    'sales',
    'territories',
    'products',
    'vendors',
    'activities',
    'workflow',
    'analytics',
    'integrations',
    'marketing',
    'master_data',
    'sharing',
    'system_config',
    'monitoring',
    
    # New enterprise modules
    'data_import',        # Import staging & deduplication
    'api_versioning',     # API version management
    'marketplace',        # Plugin marketplace
    'audit',             # Audit explorer
]
```

### 1.2 Configure File Upload Settings

For data import functionality, add to settings:

```python
# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB

# Import file storage
IMPORT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
IMPORT_FILE_ROOT = os.path.join(MEDIA_ROOT, 'imports')
```

### 1.3 Configure Audit Settings

```python
# Audit logging
AUDIT_LOG_ENABLED = True
AUDIT_LOG_RETENTION_DAYS = 365  # Default retention
AUDIT_SENSITIVE_FIELDS = [
    'password', 'ssn', 'credit_card', 'tax_id'
]
```

---

## Step 2: Update URLs

### 2.1 Add New URL Patterns

Edit `config/urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    # ... existing patterns ...
    
    # Existing API patterns
    path('api/v1/analytics/', include('analytics.urls')),
    path('api/v1/territories/', include('territories.urls')),
    path('api/v1/workflow/', include('workflow.urls')),
    path('api/v1/integrations/', include('integrations.urls')),
    
    # New enterprise API patterns
    path('api/v1/data-import/', include('data_import.urls')),
    path('api/v1/api-versioning/', include('api_versioning.urls')),
    path('api/v1/marketplace/', include('marketplace.urls')),
    path('api/v1/audit/', include('audit.urls')),
    
    # Media files (for file uploads)
    path('media/', include([
        path('<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
    ])),
]
```

---

## Step 3: Create Migrations

### 3.1 Generate Migrations

Run migrations for all updated and new modules:

```bash
# Create migrations
python manage.py makemigrations analytics
python manage.py makemigrations territories
python manage.py makemigrations workflow
python manage.py makemigrations data_import
python manage.py makemigrations api_versioning
python manage.py makemigrations marketplace
python manage.py makemigrations audit

# Review migrations before applying
python manage.py showmigrations
```

### 3.2 Apply Migrations

```bash
# Apply all migrations
python manage.py migrate

# Verify migrations
python manage.py showmigrations
```

### 3.3 Troubleshooting Migrations

If you encounter migration conflicts:

```bash
# Reset migrations for a specific app (CAUTION: dev only)
python manage.py migrate data_import zero
python manage.py migrate data_import

# Or squash migrations if needed
python manage.py squashmigrations data_import 0001 0005
```

---

## Step 4: Create Initial Data

### 4.1 Create Default API Version

```bash
python manage.py shell
```

```python
from api_versioning.models import APIVersion

# Create v1 as default
v1 = APIVersion.objects.create(
    version_number='v1',
    version_name='Version 1.0',
    status='stable',
    is_default=True,
    is_active=True,
    description='Initial API version'
)
print(f"Created {v1}")
```

### 4.2 Create Default Audit Policy

```python
from audit.models import AuditPolicy
from django.contrib.auth import get_user_model

User = get_user_model()
admin_user = User.objects.filter(is_superuser=True).first()

policy = AuditPolicy.objects.create(
    company=admin_user.company,
    name='Default Audit Policy',
    description='Standard audit and compliance policy',
    rules=[
        {'condition': 'action == "delete"', 'alert': True},
        {'condition': 'is_sensitive == True', 'alert': True}
    ],
    applies_to_entities=['account', 'contact', 'deal', 'invoice'],
    applies_to_actions=['create', 'read', 'update', 'delete'],
    alert_on_violation=True,
    owner=admin_user
)
```

### 4.3 Create Sample Import Template

```python
from data_import.models import ImportTemplate

template = ImportTemplate.objects.create(
    company=admin_user.company,
    name='Contact Import Template',
    entity_type='contact',
    field_mapping={
        'First Name': 'first_name',
        'Last Name': 'last_name',
        'Email': 'email',
        'Phone': 'phone',
        'Company': 'account'
    },
    required_fields=['first_name', 'last_name', 'email'],
    dedupe_enabled=True,
    dedupe_fields=['email'],
    dedupe_strategy='skip',
    owner=admin_user
)
```

---

## Step 5: Test the Installation

### 5.1 Run Tests

```bash
# Run all tests
python manage.py test tests.test_enterprise_features

# Run specific test classes
python manage.py test tests.test_enterprise_features.ReportingTests
python manage.py test tests.test_enterprise_features.TerritoryHierarchyTests
python manage.py test tests.test_enterprise_features.ApprovalChainTests
```

### 5.2 Verify Admin Interface

```bash
# Start development server
python manage.py runserver

# Visit admin interface
http://localhost:8000/admin/

# Verify these sections are visible:
# - Data Import
# - API Versioning
# - Marketplace
# - Audit
```

### 5.3 Test API Endpoints

```bash
# Get API versions
curl http://localhost:8000/api/v1/api-versioning/versions/

# Get import templates
curl http://localhost:8000/api/v1/data-import/templates/

# Get plugins
curl http://localhost:8000/api/v1/marketplace/plugins/

# Get audit logs
curl http://localhost:8000/api/v1/audit/logs/
```

---

## Step 6: Configure Permissions

### 6.1 Create Permission Groups

```python
from django.contrib.auth.models import Group, Permission

# Data Import Manager group
import_group = Group.objects.create(name='Data Import Managers')
import_permissions = Permission.objects.filter(
    content_type__app_label='data_import'
)
import_group.permissions.set(import_permissions)

# Audit Reviewer group
audit_group = Group.objects.create(name='Audit Reviewers')
audit_permissions = Permission.objects.filter(
    content_type__app_label='audit',
    codename__in=['view_auditlog', 'change_auditlog']
)
audit_group.permissions.set(audit_permissions)

# Marketplace Admin group
marketplace_group = Group.objects.create(name='Marketplace Admins')
marketplace_permissions = Permission.objects.filter(
    content_type__app_label='marketplace'
)
marketplace_group.permissions.set(marketplace_permissions)
```

---

## Step 7: Update Frontend (Optional)

If you have a frontend application:

### 7.1 Update API Client

```javascript
// Add new endpoints to API client
export const enterpriseAPI = {
  // Data Import
  importTemplates: '/api/v1/data-import/templates/',
  importJobs: '/api/v1/data-import/jobs/',
  
  // Marketplace
  plugins: '/api/v1/marketplace/plugins/',
  installations: '/api/v1/marketplace/installations/',
  
  // Audit
  auditLogs: '/api/v1/audit/logs/',
  complianceReports: '/api/v1/audit/compliance-reports/',
  
  // API Versioning
  apiVersions: '/api/v1/api-versioning/versions/',
};
```

### 7.2 Add Version Header

```javascript
// Add Accept-Version header to requests
axios.defaults.headers.common['Accept-Version'] = 'v1';
```

---

## Step 8: Production Deployment

### 8.1 Environment Variables

Add to your `.env` file:

```bash
# Audit configuration
AUDIT_LOG_ENABLED=true
AUDIT_RETENTION_DAYS=365

# Import configuration
IMPORT_MAX_FILE_SIZE=10485760
IMPORT_ALLOWED_TYPES=csv,xlsx,json

# API versioning
DEFAULT_API_VERSION=v1

# Marketplace
MARKETPLACE_ENABLED=true
PLUGIN_INSTALL_DIR=/opt/crm/plugins
```

### 8.2 Celery Tasks (for async processing)

Add to celery configuration:

```python
# celery.py
from celery import Celery
from celery.schedules import crontab

app = Celery('crm')

# Scheduled tasks
app.conf.beat_schedule = {
    'process-import-jobs': {
        'task': 'data_import.tasks.process_pending_imports',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
    },
    'generate-scheduled-reports': {
        'task': 'analytics.tasks.generate_scheduled_reports',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2am
    },
    'cleanup-old-audit-logs': {
        'task': 'audit.tasks.cleanup_expired_logs',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3am
    },
}
```

### 8.3 Nginx Configuration

Update nginx config for file uploads:

```nginx
# Increase upload size limits
client_max_body_size 100M;

# Media files
location /media/ {
    alias /path/to/media/;
    expires 30d;
}
```

---

## Step 9: Monitoring & Maintenance

### 9.1 Monitor Audit Logs

```bash
# Check audit log size
python manage.py shell -c "from audit.models import AuditLog; print(f'Audit logs: {AuditLog.objects.count()}')"

# Archive old logs
python manage.py archive_audit_logs --days 365
```

### 9.2 Monitor Import Jobs

```bash
# Check pending imports
python manage.py shell -c "from data_import.models import ImportJob; print(f'Pending: {ImportJob.objects.filter(status=\"pending\").count()}')"
```

### 9.3 Monitor Plugin Health

```bash
# Check plugin installations
python manage.py shell -c "from marketplace.models import PluginInstallation; print(f'Active: {PluginInstallation.objects.filter(is_enabled=True).count()}')"
```

---

## Rollback Plan

If you need to rollback:

### 1. Rollback Migrations

```bash
# Rollback to previous state
python manage.py migrate data_import zero
python manage.py migrate api_versioning zero
python manage.py migrate marketplace zero
python manage.py migrate audit zero

# Revert changes to existing apps
python manage.py migrate analytics 0001  # Adjust to previous migration
python manage.py migrate territories 0001
python manage.py migrate workflow 0001
```

### 2. Restore Settings

Remove new apps from `INSTALLED_APPS` and revert URL changes.

### 3. Restore Database

```bash
# Restore from backup
pg_restore -d crm_db backup.sql
```

---

## Support & Troubleshooting

### Common Issues

**Issue**: Import module not found
```bash
# Solution: Ensure new apps are in INSTALLED_APPS
python manage.py check
```

**Issue**: Migration conflicts
```bash
# Solution: Delete conflicting migrations and regenerate
find . -path "*/migrations/*.py" -name "0*.py" -delete
python manage.py makemigrations
```

**Issue**: Permission denied errors
```bash
# Solution: Ensure proper permissions on media directory
chmod -R 755 media/
chown -R www-data:www-data media/
```

---

## Next Steps

After successful migration:

1. **Train Users**: Provide training on new features
2. **Configure Policies**: Set up audit and compliance policies
3. **Import Data**: Use import templates to migrate existing data
4. **Install Plugins**: Browse marketplace and install useful plugins
5. **Monitor System**: Set up monitoring for new features
6. **Optimize**: Review and optimize database indexes for audit logs

---

## Version History

- **v1.0** (2024-10-07): Initial enterprise features release
  - Interactive reporting pivot UI
  - Territory hierarchy
  - Multi-step approvals
  - Weighted forecasting
  - Import engine
  - API versioning
  - Plugin marketplace
  - Audit explorer

---

*For additional support, consult the main documentation or contact the development team.*
