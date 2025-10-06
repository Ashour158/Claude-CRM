# Field-Level Permissions

## Overview
Field-level permissions provide granular control over data access at the field level, enabling organizations to implement least-privilege access and data privacy requirements. This system integrates with GDPR masking and role-based access control.

## Architecture

### Components
1. **Role** - User role definition
2. **RoleFieldPermission** - Field-level permission rules
3. **GDPRRegistry** - PII field masking configuration
4. **MaskingAuditLog** - Audit trail for masking decisions
5. **FieldPermissionService** - Permission evaluation logic
6. **MaskingService** - Data masking implementation

## Permission Modes

### View Mode (`view`)
- **Access Level**: Full access to field
- **Use Case**: Standard fields that users can read
- **Data Handling**: Field displayed as-is
- **Example**: Contact name, company name

### Mask Mode (`mask`)
- **Access Level**: Partial visibility with masking
- **Use Case**: Sensitive data that should be partially hidden
- **Data Handling**: Field value masked according to GDPR registry
- **Example**: Email (`jo**@example.com`), Phone (`***-***-1234`)

### Hidden Mode (`hidden`)
- **Access Level**: No access
- **Use Case**: Highly sensitive or irrelevant fields
- **Data Handling**: Field excluded from API response
- **Example**: SSN, credit card numbers, internal notes

### Edit Mode (`edit`)
- **Access Level**: Full read and write access
- **Use Case**: Fields users can modify
- **Data Handling**: Field can be read and updated
- **Example**: Lead status, contact phone (for owner)

## Precedence Rules

### Permission Resolution Order
1. **Explicit field permission** - Most specific wins
2. **Role default permission** - Role-level default
3. **System default** - `view` mode by default

### Conflict Resolution
- More restrictive permission takes precedence
- `hidden` > `mask` > `view` > `edit`
- Cross-role permissions: Most restrictive applies

### Inheritance
- Roles can inherit from parent roles (future enhancement)
- Field permissions DO NOT inherit - explicit only
- Company-level overrides possible

## GDPR Masking Types

### Hash (`hash`)
- **Method**: One-way SHA-256 hash
- **Format**: `hash:a1b2c3d4e5f6...`
- **Use Case**: Irreversible anonymization
- **Reversible**: No

### Partial (`partial`)
- **Method**: Show first/last N characters, mask middle
- **Format**: `jo**@example.com`, `***-***-1234`
- **Configuration**:
  ```json
  {
    "show_first": 2,
    "show_last": 2,
    "mask_char": "*"
  }
  ```
- **Use Case**: Recognizable but protected
- **Reversible**: No

### Redact (`redact`)
- **Method**: Replace entire value
- **Format**: `[REDACTED]`
- **Use Case**: Complete hiding
- **Reversible**: No

### Encrypt (`encrypt`)
- **Method**: Reversible encryption (AES-256)
- **Format**: `enc:a1b2c3d4e5f6...`
- **Use Case**: Protected but recoverable
- **Reversible**: Yes (with key)

### Tokenize (`tokenize`)
- **Method**: Deterministic token generation
- **Format**: `token_a1b2c3d4`
- **Use Case**: Cross-reference while maintaining privacy
- **Reversible**: Via token mapping

## Implementation

### Serializer Integration

#### Apply Mixin to Serializer
```python
from core.permissions_service import FieldPermissionMixin

class LeadSerializer(FieldPermissionMixin, serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = '__all__'
```

#### Field Filtering
Fields with `hidden` mode are automatically excluded from API responses.

#### Field Masking
Fields with `mask` mode are automatically masked in API responses based on GDPR registry configuration.

### Service Layer Integration

```python
from core.permissions_service import FieldPermissionService

# Check permission
can_view = FieldPermissionService.can_view_field(
    role=user_role,
    object_type='lead',
    field_name='email'
)

# Filter data
filtered_data = FieldPermissionService.filter_fields_for_role(
    data=lead_data,
    role=user_role,
    object_type='lead',
    apply_masking=True
)
```

### Search Results Integration

```python
# In search result processing
for result in search_results:
    result['_source'] = FieldPermissionService.filter_fields_for_role(
        data=result['_source'],
        role=request.user_role,
        object_type='lead'
    )
```

## Configuration Examples

### Example 1: Sales Representative
```python
# Role: Sales Rep
# Object: Lead

# Visible fields (view mode)
- first_name, last_name, company_name, phone, title

# Masked fields (mask mode)
- email (partial masking)
- mobile (partial masking)

# Hidden fields (hidden mode)
- ssn, credit_score, internal_notes

# Editable fields (edit mode)
- status, next_action, notes
```

### Example 2: Marketing User
```python
# Role: Marketing
# Object: Contact

# Visible fields
- first_name, last_name, company_name, industry

# Masked fields
- email (tokenized for campaign tracking)
- phone (hidden - not needed for email marketing)

# Hidden fields
- revenue, budget, deal_history

# Editable fields
- email_opt_in, marketing_tags
```

### Example 3: Finance User
```python
# Role: Finance
# Object: Deal

# Visible fields
- deal_name, amount, close_date, stage

# Masked fields
- None (finance needs full visibility on financial data)

# Hidden fields
- internal_notes, competitor_intel

# Editable fields
- amount, discount, payment_terms
```

## Masking Configuration

### Configure Masking for Email
```python
GDPRRegistry.objects.create(
    company=company,
    object_type='lead',
    field_name='email',
    mask_type='partial',
    mask_config={
        'show_first': 2,
        'show_last': 0,
        'mask_char': '*'
    },
    is_pii=True
)
```

### Configure Masking for Phone
```python
GDPRRegistry.objects.create(
    company=company,
    object_type='contact',
    field_name='phone',
    mask_type='partial',
    mask_config={
        'show_first': 0,
        'show_last': 4,
        'mask_char': '*'
    },
    is_pii=True
)
```

### Configure Masking for SSN
```python
GDPRRegistry.objects.create(
    company=company,
    object_type='contact',
    field_name='ssn',
    mask_type='redact',
    is_pii=True
)
```

## Audit Logging

### Automatic Logging
- All masked field accesses logged
- User, object, field, and action recorded
- Timestamp and reason tracked

### Log Entry Structure
```python
{
    'user_id': 'uuid',
    'object_type': 'lead',
    'object_id': 'lead-uuid',
    'field_name': 'email',
    'action': 'masked',
    'timestamp': '2024-01-15T10:30:00Z',
    'reason': 'mask mode for sales_rep role'
}
```

### Query Audit Logs
```python
# Get masking audit logs for user
logs = MaskingAuditLog.objects.filter(
    user=user,
    created_at__gte=start_date
)

# Get masking events for specific object
logs = MaskingAuditLog.objects.filter(
    object_type='lead',
    object_id=lead_id
)
```

## Performance Optimization

### Caching
- Permission rules cached per role/object_type
- Cache TTL: 5 minutes (configurable)
- Cache invalidation on permission update

### Batch Processing
- Bulk permission checks for list views
- Single query per object type
- Pre-load permissions for common patterns

### Query Optimization
- Indexed lookups on role + object_type
- Composite indexes for audit logs
- Separate masking from filtering

## Security Considerations

### Permission Bypass Prevention
- All API endpoints check permissions
- Direct model access prohibited
- Middleware enforcement at request level

### Audit Trail
- Complete history of access decisions
- Immutable audit logs
- Regular audit log reviews

### Data Leakage Prevention
- Masked data never stored unmasked
- Export includes masking
- Real-time event streams include masking

## Testing Strategy

### Test Cases

#### Permission Matrix
- Test all mode combinations
- Test role hierarchies
- Test cross-role conflicts

#### Masking Functions
- Test each masking type
- Test edge cases (empty, null, special chars)
- Test reversibility where applicable

#### Integration
- Test serializer field filtering
- Test API response masking
- Test search result masking
- Test export data masking

### Example Test
```python
def test_mask_mode_applies_masking():
    # Setup
    role = Role.objects.create(name='sales_rep', company=company)
    RoleFieldPermission.objects.create(
        role=role,
        object_type='lead',
        field_name='email',
        mode='mask'
    )
    GDPRRegistry.objects.create(
        company=company,
        object_type='lead',
        field_name='email',
        mask_type='partial',
        mask_config={'show_first': 2}
    )
    
    # Execute
    data = {'email': 'john@example.com'}
    filtered = FieldPermissionService.filter_fields_for_role(
        data, role, 'lead'
    )
    
    # Assert
    assert filtered['email'] == 'jo**@example.com'
```

## API Endpoints

### List Field Permissions
```
GET /api/v1/roles/{role_id}/field-permissions/
```

### Create Field Permission
```
POST /api/v1/roles/{role_id}/field-permissions/
{
  "object_type": "lead",
  "field_name": "email",
  "mode": "mask"
}
```

### Update Field Permission
```
PUT /api/v1/roles/{role_id}/field-permissions/{id}/
```

### Delete Field Permission
```
DELETE /api/v1/roles/{role_id}/field-permissions/{id}/
```

### List GDPR Masking Rules
```
GET /api/v1/gdpr/masking-rules/
```

### Query Audit Logs
```
GET /api/v1/audit/masking-logs/?user_id={id}&date_from={date}
```

## Best Practices

1. **Start Restrictive**: Default to `hidden` or `mask`, grant `view` explicitly
2. **Regular Audits**: Review permission configurations quarterly
3. **Least Privilege**: Grant minimum permissions needed for role
4. **Document Decisions**: Record why fields have specific modes
5. **Test Thoroughly**: Verify permissions in all access paths
6. **Monitor Usage**: Track which fields are most accessed/masked

## Future Enhancements

- Dynamic permissions based on data classification
- Time-based permission grants (temporary access)
- Conditional permissions (e.g., only for records you own)
- ML-based anomaly detection for permission violations
- Automated permission recommendations
- Fine-grained permissions (read vs write separately)

## Compliance

This system helps meet requirements for:
- **GDPR**: Article 5 (data minimization), Article 32 (security)
- **CCPA**: Consumer data protection
- **HIPAA**: PHI protection (healthcare)
- **SOC 2**: Access control requirements
- **ISO 27001**: Information security management
