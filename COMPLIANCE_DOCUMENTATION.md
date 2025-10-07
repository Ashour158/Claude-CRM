# Compliance & Security Maturity Features

## Overview

The Claude-CRM compliance module provides comprehensive security and compliance features to meet GDPR, CCPA, SOC2, and HIPAA requirements.

## Features

### 1. Policy-as-Code

Define and manage compliance policies using YAML configuration files.

#### Policy Structure

```yaml
name: GDPR Compliance Policy
version: 1.0.0
type: gdpr

enforcement:
  level: hard  # soft or hard
  scope: company

rules:
  - id: gdpr-001
    name: Data Retention
    type: retention
    condition:
      entity_type: Lead
      age_days: 365
    action: delete
    severity: high

retention:
  policies:
    - entity_type: Lead
      retention_days: 365
      deletion_method: soft
    - entity_type: Contact
      retention_days: 730
      deletion_method: hard

data_residency:
  regions:
    - us-east-1
    - eu-west-1
  enforce: true
```

#### CLI Commands

**Validate Policy:**
```bash
python manage.py validate_policy --file policy.yaml
python manage.py validate_policy --policy-id <uuid>
```

**Dry-Run Impact Analysis:**
```bash
python manage.py apply_policy <policy-id> --dry-run
```

**Apply Policy:**
```bash
python manage.py apply_policy <policy-id>
```

**Rollback Policy:**
```bash
# Via API
POST /api/compliance/policies/<id>/rollback/
```

### 2. Data Residency Enforcement

Enforce data storage in specific geographic regions for compliance.

#### Configuration

```python
from compliance.models import DataResidency

residency = DataResidency.objects.create(
    company=company,
    primary_region='us-east-1',
    allowed_regions=['us-east-1', 'us-west-2'],
    storage_prefix='company-data-us',
    enforce_region=True,
    block_cross_region=True,
    compliance_frameworks=['GDPR', 'CCPA']
)
```

#### API Endpoints

- `GET /api/compliance/data-residency/` - List configurations
- `POST /api/compliance/data-residency/` - Create configuration
- `PUT /api/compliance/data-residency/<id>/` - Update configuration

### 3. Data Subject Rights (DSR)

Handle GDPR/CCPA data subject requests with audit trails and rollback capability.

#### Request Types

- **Erasure** - Right to be forgotten
- **Access** - Right to access data
- **Portability** - Right to data portability
- **Rectification** - Right to correct data
- **Restriction** - Right to restrict processing
- **Objection** - Right to object

#### Creating DSR Request

```python
from compliance.models import DataSubjectRequest
from datetime import timedelta

dsr = DataSubjectRequest.objects.create(
    company=company,
    request_type='erasure',
    subject_email='user@example.com',
    subject_name='John Doe',
    entities_affected=['Contact', 'Lead', 'Activity'],
    due_date=timezone.now() + timedelta(days=30)
)
```

#### Processing DSR

```bash
# Via API
POST /api/compliance/dsr-requests/<id>/process/
```

#### Rollback DSR

```bash
# Via API
POST /api/compliance/dsr-requests/<id>/rollback/
```

### 4. Field-Level Encryption

Encrypt sensitive PII fields using KMS-backed envelope encryption.

#### Usage

```python
from compliance.encryption import PIIEncryption

# Encrypt field
encrypted = PIIEncryption.encrypt_field('sensitive-data')

# Decrypt field
decrypted = PIIEncryption.decrypt_field(encrypted)

# Data masking
from compliance.encryption import DataMasking

masked_email = DataMasking.mask_email('user@example.com')  # u***r@example.com
masked_phone = DataMasking.mask_phone('1234567890')  # ****7890
```

#### KMS Configuration

Set encryption key in settings or environment:

```python
# settings.py
ENCRYPTION_MASTER_KEY = os.environ.get('ENCRYPTION_MASTER_KEY')
```

### 5. Central Secrets Vault

Secure storage for API credentials and secrets with automatic rotation.

#### Creating Secret

```python
from compliance.models import SecretVault
from compliance.encryption import SecretEncryption

encryption = SecretEncryption()
encrypted_value = encryption.encrypt('my-api-key')

secret = SecretVault.objects.create(
    company=company,
    name='Stripe API Key',
    secret_type='api_key',
    secret_value=encrypted_value,
    rotation_enabled=True,
    rotation_days=90,
    owner=user
)
```

#### Rotating Secrets

```bash
# Manual rotation via API
POST /api/compliance/secrets/<id>/rotate/
{
  "new_value": "new-secret-value"
}

# Automated rotation (runs daily)
python manage.py run_celery_tasks
```

#### Revealing Secrets

```bash
# Restricted to authorized users
GET /api/compliance/secrets/<id>/reveal/
```

### 6. Automated Access Reviews

Quarterly access reviews to identify stale permissions.

#### Running Review

```bash
# CLI
python manage.py run_access_review
python manage.py run_access_review --company-id <uuid>

# API
POST /api/compliance/access-reviews/start_review/
```

#### Resolving Stale Access

```bash
POST /api/compliance/stale-access/<id>/resolve/
{
  "resolution": "revoked"  # or "retained"
}
```

#### Automated Schedule

Add to Celery beat schedule:

```python
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'quarterly-access-review': {
        'task': 'compliance.tasks.run_quarterly_access_review',
        'schedule': crontab(day_of_month='1', month_of_year='1,4,7,10'),
    },
}
```

### 7. Retention Enforcement

Automatic data retention and deletion based on policies.

#### Creating Retention Policy

```python
from compliance.models import RetentionPolicy

policy = RetentionPolicy.objects.create(
    company=company,
    name='Lead Retention Policy',
    entity_type='Lead',
    retention_days=365,
    deletion_method='soft',  # soft, hard, or archive
    is_active=True
)
```

#### Executing Retention

```bash
# CLI - Preview
python manage.py execute_retention --policy-id <uuid> --preview

# CLI - Execute
python manage.py execute_retention --policy-id <uuid>

# CLI - Execute all scheduled
python manage.py execute_retention --all-scheduled

# API
POST /api/compliance/retention-policies/<id>/execute/
```

#### Automated Schedule

```python
CELERY_BEAT_SCHEDULE = {
    'daily-retention-enforcement': {
        'task': 'compliance.tasks.execute_retention_policies',
        'schedule': crontab(hour='2', minute='0'),  # 2 AM daily
    },
}
```

## API Endpoints

### Policies
- `GET /api/compliance/policies/` - List policies
- `POST /api/compliance/policies/` - Create policy
- `GET /api/compliance/policies/<id>/` - Get policy
- `PUT /api/compliance/policies/<id>/` - Update policy
- `DELETE /api/compliance/policies/<id>/` - Delete policy
- `POST /api/compliance/policies/<id>/validate/` - Validate policy
- `POST /api/compliance/policies/<id>/dry_run/` - Dry-run analysis
- `POST /api/compliance/policies/<id>/apply/` - Apply policy
- `POST /api/compliance/policies/<id>/rollback/` - Rollback policy

### Data Residency
- `GET /api/compliance/data-residency/` - List configurations
- `POST /api/compliance/data-residency/` - Create configuration
- `GET /api/compliance/data-residency/<id>/` - Get configuration
- `PUT /api/compliance/data-residency/<id>/` - Update configuration

### DSR Requests
- `GET /api/compliance/dsr-requests/` - List requests
- `POST /api/compliance/dsr-requests/` - Create request
- `GET /api/compliance/dsr-requests/<id>/` - Get request
- `POST /api/compliance/dsr-requests/<id>/process/` - Process request
- `POST /api/compliance/dsr-requests/<id>/rollback/` - Rollback processing

### Secrets Vault
- `GET /api/compliance/secrets/` - List secrets
- `POST /api/compliance/secrets/` - Create secret
- `GET /api/compliance/secrets/<id>/` - Get secret (redacted)
- `GET /api/compliance/secrets/<id>/reveal/` - Reveal secret (restricted)
- `POST /api/compliance/secrets/<id>/rotate/` - Rotate secret

### Access Reviews
- `GET /api/compliance/access-reviews/` - List reviews
- `POST /api/compliance/access-reviews/start_review/` - Start review
- `GET /api/compliance/stale-access/` - List stale access
- `POST /api/compliance/stale-access/<id>/resolve/` - Resolve stale access

### Retention Policies
- `GET /api/compliance/retention-policies/` - List policies
- `POST /api/compliance/retention-policies/` - Create policy
- `POST /api/compliance/retention-policies/<id>/execute/` - Execute policy

## Celery Tasks

### Setup

```python
# celeryconfig.py
from celery.schedules import crontab

beat_schedule = {
    'quarterly-access-review': {
        'task': 'compliance.tasks.run_quarterly_access_review',
        'schedule': crontab(day_of_month='1', month_of_year='1,4,7,10'),
    },
    'daily-retention': {
        'task': 'compliance.tasks.execute_retention_policies',
        'schedule': crontab(hour='2', minute='0'),
    },
    'daily-secret-rotation': {
        'task': 'compliance.tasks.rotate_secrets',
        'schedule': crontab(hour='3', minute='0'),
    },
    'daily-dsr-check': {
        'task': 'compliance.tasks.check_dsr_deadlines',
        'schedule': crontab(hour='9', minute='0'),
    },
}
```

## Testing

Run compliance tests:

```bash
python manage.py test compliance
```

Run specific test:

```bash
python manage.py test compliance.tests.PolicyValidatorTests
```

## Compliance Checklists

### GDPR Compliance
- [x] Right to erasure
- [x] Right to access
- [x] Right to portability
- [x] Right to rectification
- [x] Data retention policies
- [x] Audit trails
- [x] Data residency enforcement

### CCPA Compliance
- [x] Consumer data access
- [x] Consumer data deletion
- [x] Opt-out mechanisms
- [x] Data selling disclosure

### SOC2 Controls
- [x] Access controls
- [x] Encryption at rest
- [x] Audit logging
- [x] Access reviews
- [x] Retention policies

## Security Best Practices

1. **Encryption Keys**: Store master encryption keys in secure key management service (AWS KMS, Azure Key Vault)
2. **Secret Rotation**: Enable automatic rotation for all API credentials
3. **Access Reviews**: Run quarterly reviews and promptly revoke stale access
4. **Audit Logs**: Monitor policy audit logs for violations
5. **Data Residency**: Configure appropriate regions for your compliance requirements
6. **DSR Deadlines**: Set up alerts for approaching DSR deadlines (typically 30 days)

## Troubleshooting

### Policy Validation Errors

Check policy configuration syntax:
```bash
python manage.py validate_policy --file policy.yaml
```

### Encryption Errors

Verify encryption key is set:
```bash
echo $ENCRYPTION_MASTER_KEY
```

### Failed Retention Execution

Check retention logs:
```python
from compliance.models import RetentionLog
logs = RetentionLog.objects.filter(errors_encountered__gt=0)
```

## Support

For issues or questions, contact the security team or create an issue in the repository.
