# Custom Fields Design

## Overview
The custom field system allows organizations to extend core CRM entities (Accounts, Contacts, Leads, Deals) with custom attributes without modifying the database schema.

## Architecture

### Phase 1 (Current): JSON-Based Storage
Custom field values are stored in a `custom_data` JSONField on each entity model.

**Advantages:**
- No additional tables needed
- Fast reads/writes
- Schema changes don't require migrations
- Simple implementation

**Limitations:**
- Cannot query/filter efficiently on custom field values
- No database-level constraints
- Limited indexing capabilities

### Phase 2 (Future): Hybrid EAV Pattern
For fields requiring indexing/filtering, we'll introduce a separate value table with selective materialization.

## Data Model

### CustomFieldDefinition
Defines available custom fields for each entity type.

```python
class CustomFieldDefinition(TenantOwnedModel):
    name            # Display name (e.g., "Preferred Contact Time")
    code            # Internal code (e.g., "preferred_contact_time")
    field_type      # text, number, date, datetime, boolean, select, multi_select, url, email, phone, textarea
    entity_type     # account, contact, lead, deal
    is_required     # Whether field must have a value
    choices         # JSON list for select/multi_select types
    default_value   # Default value for new records
    help_text       # User-facing help text
    display_order   # Order in UI
    field_group     # Grouping for UI organization
    is_active       # Whether field is currently active
```

**Unique Constraint**: `(organization, entity_type, code)`

### Field Types

| Type | Description | Storage Format | Example |
|------|-------------|----------------|---------|
| `text` | Short text | String | "John Doe" |
| `textarea` | Long text | String | "Detailed notes..." |
| `number` | Numeric value | Number | 42 or 3.14 |
| `date` | Date only | ISO Date String | "2024-01-15" |
| `datetime` | Date and time | ISO DateTime String | "2024-01-15T10:30:00Z" |
| `boolean` | Yes/No | Boolean | true |
| `select` | Single choice | String | "option1" |
| `multi_select` | Multiple choices | Array of Strings | ["opt1", "opt2"] |
| `url` | Web URL | String | "https://example.com" |
| `email` | Email address | String | "user@example.com" |
| `phone` | Phone number | String | "+1-555-0123" |

## Storage Format

### Entity Models
Each entity has a `custom_data` field:

```python
class Account(TenantOwnedModel):
    # ... standard fields ...
    custom_data = models.JSONField(default=dict, blank=True)
```

### Example Storage
```json
{
  "preferred_color": "blue",
  "account_tier": "platinum",
  "renewal_date": "2024-12-31",
  "custom_tags": ["vip", "high-value"],
  "satisfaction_score": 9.5
}
```

## Service Layer

### CustomFieldService
Provides CRUD operations and validation for custom field values.

#### Key Methods

**get_field_definitions(organization, entity_type, active_only=True)**
- Returns all custom field definitions for an entity type
- Ordered by display_order and name

**get_custom_data(entity, include_definitions=False)**
- Retrieves custom field values from an entity
- Optionally includes field definitions for UI rendering

**set_custom_field(entity, field_code, value, validate=True)**
- Sets a single custom field value
- Validates value against field definition

**set_custom_fields(entity, field_values, validate=True, save=False)**
- Sets multiple custom field values
- Bulk validation
- Optional auto-save

**validate_all_custom_fields(entity)**
- Validates all custom fields on an entity
- Checks required fields
- Type-specific validation

## Validation Rules

### Type-Specific Validation
- **number**: Must be numeric (int or float)
- **boolean**: Must be true/false
- **select**: Value must be in choices list
- **multi_select**: All values must be in choices list
- **email**: Must be valid email format
- **url**: Must be valid URL format

### Required Fields
If `is_required=True`, the field must have a non-empty value.

### Example Validation
```python
# Valid
custom_data = {
    "account_tier": "gold",  # select field
    "renewal_date": "2024-12-31",  # date field
    "satisfaction_score": 8.5  # number field
}

# Invalid
custom_data = {
    "account_tier": "diamond",  # not in choices
    "renewal_date": "invalid-date",  # not ISO date
    "satisfaction_score": "high"  # not a number
}
```

## Usage Examples

### Creating a Custom Field Definition
```python
from crm.custom_fields.models import CustomFieldDefinition

field = CustomFieldDefinition.objects.create(
    organization=org,
    name="Account Tier",
    code="account_tier",
    field_type="select",
    entity_type="account",
    is_required=True,
    choices=["bronze", "silver", "gold", "platinum"],
    display_order=1
)
```

### Setting Custom Field Values
```python
from crm.custom_fields.services import CustomFieldService
from crm.accounts.models import Account

account = Account.objects.get(id=account_id)

# Set single field
CustomFieldService.set_custom_field(
    account,
    "account_tier",
    "platinum"
)

# Set multiple fields
CustomFieldService.set_custom_fields(
    account,
    {
        "account_tier": "platinum",
        "renewal_date": "2024-12-31",
        "satisfaction_score": 9.5
    },
    save=True
)
```

### Retrieving Custom Field Values
```python
# Get raw values
custom_data = CustomFieldService.get_custom_data(account)
# Returns: {"account_tier": "platinum", "renewal_date": "2024-12-31"}

# Get values with definitions
data_with_defs = CustomFieldService.get_custom_data(account, include_definitions=True)
# Returns:
# {
#   "account_tier": {
#     "definition": {"name": "Account Tier", "field_type": "select", "choices": [...]},
#     "value": "platinum"
#   },
#   ...
# }
```

## UI Integration

### Field Grouping
Fields can be grouped for better UI organization:

```python
# Create fields with groups
CustomFieldDefinition.objects.create(
    organization=org,
    name="Billing Contact",
    code="billing_contact",
    entity_type="account",
    field_group="Billing Information",
    display_order=1
)
```

### Display Order
Fields within a group are ordered by `display_order` then `name`.

## Future Enhancements (Phase 2+)

### Planned Features
1. **Conditional Fields**: Show/hide fields based on other field values
2. **Calculated Fields**: Fields computed from other fields
3. **Field Dependencies**: Validation rules across multiple fields
4. **Field History**: Track changes to custom field values
5. **Indexed Fields**: Selective materialization for filtering/searching
6. **Field Templates**: Pre-defined field sets for common use cases
7. **Validation Expressions**: Custom validation logic
8. **Field Permissions**: Per-field access control

### EAV Table (Phase 2)
For fields requiring database queries:

```python
class CustomFieldValue(TenantOwnedModel):
    field_definition = models.ForeignKey(CustomFieldDefinition)
    entity_content_type = GenericForeignKey
    entity_object_id = UUID
    value_text = models.TextField(null=True)
    value_number = models.DecimalField(null=True)
    value_date = models.DateField(null=True)
    value_bool = models.BooleanField(null=True)
```

## Performance Considerations

### Current (Phase 1)
- **Reads**: O(1) - Direct JSON access
- **Writes**: O(1) - JSON update
- **Queries**: Not supported - cannot filter on custom field values
- **Indexes**: Not possible

### Future (Phase 2 with EAV)
- **Reads**: O(1) from cache, O(n) from DB
- **Writes**: O(n) - One row per field
- **Queries**: O(log n) with indexes
- **Indexes**: Possible on materialized columns

## Limitations

### Current Limitations
1. Cannot filter records by custom field values in database
2. No database-level validation
3. No referential integrity for select field choices
4. Limited to 1MB total custom data per record (PostgreSQL JSONB limit)

### Workarounds
1. Use application-level filtering for custom fields
2. Validate in service layer before save
3. Maintain choices in CustomFieldDefinition
4. Keep custom data compact; move large text to attachments

## Migration Path

### From Legacy custom_fields
The system maintains backward compatibility with the old `custom_fields` JSONField:

```python
# Old format (legacy)
account.custom_fields = {"tier": "gold"}

# New format (Phase 2)
account.custom_data = {"account_tier": "gold"}
```

Both fields exist during migration. Data can be migrated using:
```python
# Migration script (future)
for account in Account.objects.all():
    if account.custom_fields:
        account.custom_data = migrate_custom_fields(account.custom_fields)
        account.save()
```
