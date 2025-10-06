# Custom Fields Design

## Overview
The CRM system supports custom fields that can be added to any entity (Accounts, Contacts, Leads, Deals) without modifying the database schema. This provides flexibility for businesses with unique data requirements.

## Architecture

### Phase 1: JSON Strategy (Current Implementation)

Custom field values are stored in a `custom_fields` JSON column on each entity model.

#### Advantages
- ✅ No schema migrations needed when adding fields
- ✅ Flexible and easy to implement
- ✅ Works well with PostgreSQL's JSON support
- ✅ Good for dynamic/varying field requirements

#### Disadvantages
- ❌ Limited query capabilities (can't easily filter/sort)
- ❌ No database-level validation
- ❌ Indexing challenges
- ❌ Type safety concerns

## Data Model

### CustomFieldDefinition
```python
class CustomFieldDefinition(TenantOwnedModel):
    name = CharField()              # Internal field name (key)
    label = CharField()             # Display label
    field_type = CharField()        # text, number, date, boolean, etc.
    entity_type = CharField()       # account, contact, lead, deal
    is_required = BooleanField()
    is_unique = BooleanField()
    default_value = TextField()
    choices = JSONField()           # For choice/multichoice fields
    validation_rules = JSONField()  # min, max, regex, etc.
    display_order = IntegerField()
    is_visible = BooleanField()
    is_editable = BooleanField()
    is_searchable = BooleanField()
```

### Field Types
1. **text** - Single-line text
2. **textarea** - Multi-line text
3. **number** - Integer
4. **decimal** - Decimal number
5. **date** - Date only
6. **datetime** - Date and time
7. **boolean** - True/False
8. **choice** - Single selection from list
9. **multichoice** - Multiple selections from list
10. **url** - URL with validation
11. **email** - Email with validation

### Storage Example

**CustomFieldDefinition:**
```json
{
  "id": "uuid",
  "organization": "org-uuid",
  "name": "contract_value",
  "label": "Contract Value",
  "field_type": "decimal",
  "entity_type": "account",
  "is_required": true,
  "validation_rules": {
    "min": 0,
    "max": 10000000
  }
}
```

**Account.custom_fields:**
```json
{
  "contract_value": 50000.00,
  "renewal_date": "2025-12-31",
  "priority_customer": true,
  "custom_tags": ["vip", "enterprise"]
}
```

## Usage

### Define Custom Field
```python
from crm.system.models import CustomFieldDefinition

field = CustomFieldDefinition.objects.create(
    organization=org,
    name='contract_value',
    label='Contract Value',
    field_type='decimal',
    entity_type='account',
    is_required=True,
    validation_rules={'min': 0, 'max': 10000000}
)
```

### Validate and Set Values
```python
from crm.system.services.custom_field_service import CustomFieldService

# Validate custom fields
is_valid, validated_data, errors = CustomFieldService.validate_and_assign(
    entity_type='account',
    custom_fields_data={
        'contract_value': 50000.00,
        'priority_customer': True
    },
    organization=org
)

if is_valid:
    account.custom_fields = validated_data
    account.save()
```

### Query Custom Fields
```python
# Get all accounts with contract_value > 10000
accounts = Account.objects.for_organization(org).filter(
    custom_fields__contract_value__gt=10000
)

# Note: PostgreSQL JSON queries work but have limitations
```

### Display Custom Fields
```python
from crm.system.services.custom_field_service import CustomFieldService

# Get display-friendly values
display_data = CustomFieldService.resolve_display(
    entity_type='account',
    custom_fields_data=account.custom_fields,
    organization=org
)

# Returns: {'Contract Value': 50000.00, 'Priority Customer': True}
```

## Validation

The CustomFieldService handles validation:

1. **Type Validation**
   - Numbers must be numeric
   - Emails must be valid format
   - URLs must start with http:// or https://
   - Dates must be ISO 8601 format

2. **Rule Validation**
   - Min/max for numbers
   - Regex patterns for text
   - Choice validation for select fields

3. **Required Fields**
   - Ensures required fields are provided
   - Returns detailed error messages

## Best Practices

### 1. Naming Conventions
- Use snake_case for field names
- Keep names short but descriptive
- Avoid special characters

### 2. Performance
- Limit number of custom fields per entity
- Use indexes sparingly (JSON indexing is expensive)
- Consider caching field definitions

### 3. Validation
- Always validate before saving
- Provide clear error messages
- Use appropriate field types

### 4. Display
- Set meaningful labels
- Use display_order for consistent UI
- Group related fields together

### 5. Migration
- Plan field additions carefully
- Provide default values for existing records
- Test thoroughly before deployment

## Future Enhancements

### Phase 2: Hybrid Approach (Planned)
- Store frequently queried fields in dedicated columns
- Keep rarely used fields in JSON
- Automatic migration path

### Additional Features
- **Conditional Visibility**: Show/hide fields based on other values
- **Calculated Fields**: Computed from other fields
- **Field Groups**: Organize fields into sections
- **Validation Extensions**: Custom validation functions
- **Import/Export**: Bulk field definition management
- **Version History**: Track field definition changes

## Related Documentation

- [Domain Migration Status](./DOMAIN_MIGRATION_STATUS.md)
- [Permissions Matrix](./PERMISSIONS_MATRIX.md)
- [API Documentation](./API_DOCUMENTATION.md)
