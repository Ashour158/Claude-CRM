# Custom Fields Design

## Overview
The custom field system allows organizations to extend CRM entities with additional fields without database schema changes.

## Design Philosophy

### Phase 1: JSON Storage (Current Implementation)
- **Storage**: Custom field values stored in `custom_data` JSONField on each entity
- **Definitions**: Metadata stored in `CustomFieldDefinition` model
- **Pros**:
  - Fast to implement
  - No schema migrations per field
  - Flexible for varying field counts
- **Cons**:
  - No database-level constraints
  - Limited query capabilities
  - No foreign key relationships

### Phase 2: Relational Pivot (Future)
- **Storage**: Values in separate `CustomFieldValue` table
- **Pros**:
  - Better query support
  - Database constraints available
  - Can support complex field types
- **Cons**:
  - More complex queries
  - More storage overhead
  - Requires careful indexing

## Current Implementation

### Model: CustomFieldDefinition

```python
class CustomFieldDefinition(TenantOwnedModel):
    entity_type = CharField(choices=['account', 'contact', 'lead', ...])
    name = CharField()  # Display name
    code = CharField()  # Internal key for JSON storage
    field_type = CharField(choices=['text', 'number', 'date', ...])
    is_required = BooleanField()
    is_active = BooleanField()
    choices = JSONField(null=True)  # For choice/multichoice fields
    ordering = IntegerField()  # Display order
    group_name = CharField()  # For UI grouping
    validation_rules = JSONField()  # Min, max, pattern, etc.
```

### Unique Constraint
```sql
UNIQUE(organization, entity_type, code)
```

### Supported Field Types

1. **Text**: Single-line text input
2. **Textarea**: Multi-line text
3. **Number**: Integer values
4. **Decimal**: Floating point values
5. **Date**: Date picker
6. **DateTime**: Date and time picker
7. **Boolean**: Checkbox
8. **Choice**: Single selection dropdown
9. **MultiChoice**: Multiple selection
10. **URL**: URL with validation
11. **Email**: Email with validation
12. **Phone**: Phone number

## Usage Examples

### Define a Custom Field

```python
from crm.system.models import CustomFieldDefinition

field = CustomFieldDefinition.objects.create(
    organization=org,
    entity_type='account',
    name='Industry Vertical',
    code='industry_vertical',
    field_type='choice',
    choices=['Healthcare', 'Finance', 'Technology', 'Retail'],
    is_required=False,
    is_active=True,
    ordering=10,
    group_name='Business Info'
)
```

### Assign Values

```python
from crm.accounts.models import Account
from crm.system.services.custom_field_service import validate_and_assign

account = Account.objects.get(id=123)

# Validate and assign custom field values
is_valid, errors = validate_and_assign(
    entity=account,
    data={
        'industry_vertical': 'Healthcare',
        'annual_spend': 50000
    }
)

if is_valid:
    account.save()
else:
    print(f"Validation errors: {errors}")
```

### Retrieve with Display Data

```python
from crm.system.services.custom_field_service import resolve_display

account = Account.objects.get(id=123)
display_data = resolve_display(account)

# Returns:
# {
#     'industry_vertical': {
#         'name': 'Industry Vertical',
#         'value': 'Healthcare',
#         'display_value': 'Healthcare',
#         'field_type': 'choice',
#         'group': 'Business Info',
#         'help_text': ''
#     }
# }
```

## Validation

### Built-in Validations

1. **Required Check**: Enforces `is_required` flag
2. **Type Validation**: Ensures value matches field_type
3. **Choice Validation**: Validates against allowed choices
4. **Number Range**: Checks min/max from validation_rules
5. **Email Format**: Uses Django's email validator
6. **Unknown Field**: Rejects undefined field codes

### Custom Validation Rules

Stored in `validation_rules` JSON field:

```python
{
    'min': 0,
    'max': 100,
    'pattern': r'^\d{3}-\d{4}$',  # For regex validation
    'min_length': 5,
    'max_length': 100
}
```

## API Integration

### GET Custom Fields for Entity Type

```http
GET /api/v1/custom-fields?entity_type=account
```

Response:
```json
{
    "fields": [
        {
            "code": "industry_vertical",
            "name": "Industry Vertical",
            "field_type": "choice",
            "is_required": false,
            "choices": ["Healthcare", "Finance", "Technology"],
            "ordering": 10,
            "group_name": "Business Info"
        }
    ]
}
```

### Submit with Custom Fields

```http
POST /api/v1/accounts/
Content-Type: application/json

{
    "name": "Acme Corp",
    "primary_email": "info@acme.com",
    "custom_data": {
        "industry_vertical": "Healthcare",
        "annual_spend": 50000
    }
}
```

## UI Considerations

### Display Grouping
- Fields with same `group_name` displayed together
- Groups sorted by minimum `ordering` value within group
- Ungrouped fields appear last

### Form Generation
- Field type determines input component
- `is_required` adds validation
- `help_text` shows as tooltip
- `choices` generates dropdown options

### Inline Editing
- Custom fields editable inline on detail pages
- Validation errors shown immediately
- Changes saved independently from core fields

## Performance Considerations

### Current (JSON Storage)
- **Read**: Fast - single table query
- **Write**: Fast - single UPDATE
- **Search**: Limited - JSONB operators for Postgres
- **Index**: Can index specific JSON keys if needed

### Future (Relational Pivot)
- **Read**: Slower - requires JOINs
- **Write**: Slower - multiple INSERTs
- **Search**: Better - standard SQL queries
- **Index**: Standard B-tree indexes

## Migration Path to Relational

When JSON storage becomes limiting:

1. **Create CustomFieldValue table**
   ```python
   class CustomFieldValue(TenantOwnedModel):
       definition = ForeignKey(CustomFieldDefinition)
       entity_content_type = ForeignKey(ContentType)
       entity_object_id = IntegerField()
       value_text = TextField(null=True)
       value_number = DecimalField(null=True)
       value_date = DateField(null=True)
       value_boolean = BooleanField(null=True)
   ```

2. **Migrate data from JSON to relational**
3. **Update services to use new storage**
4. **Deprecate custom_data JSONField**

## Best Practices

1. **Limit Field Count**: Recommend max 50 custom fields per entity type
2. **Use Descriptive Codes**: e.g., `customer_tier` not `cf1`
3. **Group Related Fields**: Use `group_name` for organization
4. **Set Reasonable Ordering**: Leave gaps (10, 20, 30) for insertions
5. **Validate Early**: Check field definitions before assigning values
6. **Document Fields**: Use `help_text` for user guidance

## Security

- Field definitions are organization-scoped
- Users need `manage_custom_fields` permission to create/edit definitions
- Values inherit entity permissions (if user can edit account, can edit its custom fields)
- No cross-organization field access

## Future Enhancements

- [ ] Formula fields (calculated values)
- [ ] Lookup fields (reference other entities)
- [ ] Conditional visibility rules
- [ ] Field-level permissions
- [ ] Change history tracking
- [ ] Bulk field value updates
- [ ] Field value rollup/aggregation
- [ ] Multi-language field labels
