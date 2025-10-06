# Custom Fields Design

## Overview
Custom fields allow per-company customization of entity schemas without altering the database structure. This document describes the design, implementation, and future enhancements.

## Current Implementation (Phase 2)

### Model: CustomField

```python
# system_config/models.py
class CustomField(CompanyIsolatedModel):
    name = models.CharField(max_length=255)  # Field identifier
    label = models.CharField(max_length=255)  # Display label
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    entity_type = models.CharField(max_length=20, choices=ENTITY_TYPES)
    
    # Configuration
    is_required = models.BooleanField(default=False)
    is_unique = models.BooleanField(default=False)
    default_value = models.TextField(blank=True)
    choices = models.JSONField(default=list)  # For choice fields
    validation_rules = models.JSONField(default=dict)
    
    # Display
    display_order = models.IntegerField(default=0)
    is_visible = models.BooleanField(default=True)
    help_text = models.TextField(blank=True)
    
    # Access control
    is_editable = models.BooleanField(default=True)
    is_searchable = models.BooleanField(default=True)
```

### Supported Field Types
- `text` - Single-line text input
- `textarea` - Multi-line text input
- `number` - Integer values
- `decimal` - Decimal/float values
- `date` - Date picker
- `datetime` - Date and time picker
- `boolean` - Checkbox (true/false)
- `choice` - Single selection dropdown
- `multichoice` - Multiple selection
- `url` - URL field with validation
- `email` - Email field with validation
- `phone` - Phone number field

### Supported Entity Types
- `account` - Company/Account records
- `contact` - Contact records
- `lead` - Lead records
- `deal` - Deal/Opportunity records
- `product` - Product records
- `campaign` - Marketing campaign records

## Storage Strategy

### Phase 2: JSON Field Approach
Custom field values are stored in a `custom_fields` JSON field on each entity model.

**Advantages:**
- Simple to implement
- No schema changes required
- Fast initial development

**Limitations:**
- Limited query performance
- No database-level constraints
- Harder to index

### Phase 3: Relational Pivot Table (Planned)

For better performance and querying, implement a pivot table:

```python
class CustomFieldValue(CompanyIsolatedModel):
    custom_field = models.ForeignKey(CustomField, on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.UUIDField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Store value in appropriate column based on field_type
    value_text = models.TextField(blank=True, null=True)
    value_number = models.IntegerField(blank=True, null=True)
    value_decimal = models.DecimalField(max_digits=20, decimal_places=6, blank=True, null=True)
    value_date = models.DateField(blank=True, null=True)
    value_datetime = models.DateTimeField(blank=True, null=True)
    value_boolean = models.BooleanField(blank=True, null=True)
    
    class Meta:
        unique_together = ('custom_field', 'content_type', 'object_id')
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['custom_field', 'value_text']),
            models.Index(fields=['custom_field', 'value_number']),
        ]
```

**Advantages:**
- Better query performance
- Database-level constraints possible
- Can index individual values
- Easier to generate reports

**Migration Strategy:**
1. Create CustomFieldValue model
2. Add migration script to copy JSON values to pivot table
3. Gradually transition code to use pivot table
4. Eventually deprecate JSON field approach

## Validation

### Client-Side Validation
Forms should implement validation based on field configuration:

```javascript
// Example validation rules
{
    "min_length": 3,
    "max_length": 100,
    "pattern": "^[A-Z][a-z]+$",
    "min_value": 0,
    "max_value": 999999,
    "required_if": "other_field=value"
}
```

### Server-Side Validation
Implement in model save or serializer:

```python
def validate_custom_fields(entity, custom_fields_data):
    """Validate custom field values against definitions"""
    entity_type = entity.__class__.__name__.lower()
    
    # Get custom field definitions
    field_defs = CustomField.objects.filter(
        company=entity.company,
        entity_type=entity_type
    )
    
    errors = {}
    
    for field_def in field_defs:
        value = custom_fields_data.get(field_def.name)
        
        # Required validation
        if field_def.is_required and not value:
            errors[field_def.name] = f"{field_def.label} is required"
            continue
        
        if value:
            # Type-specific validation
            if field_def.field_type == 'number':
                try:
                    int(value)
                except ValueError:
                    errors[field_def.name] = f"{field_def.label} must be a number"
            
            elif field_def.field_type == 'email':
                # Email validation
                from django.core.validators import validate_email
                try:
                    validate_email(value)
                except ValidationError:
                    errors[field_def.name] = f"{field_def.label} must be a valid email"
            
            # Add more validations...
    
    return errors
```

## API Integration

### List Custom Fields
```
GET /api/v1/custom-fields/?entity_type=account
```

Response:
```json
{
    "results": [
        {
            "id": "uuid",
            "name": "industry_segment",
            "label": "Industry Segment",
            "field_type": "choice",
            "choices": ["Enterprise", "Mid-Market", "SMB"],
            "is_required": true,
            "display_order": 1
        }
    ]
}
```

### Get Entity with Custom Fields
```
GET /api/v1/accounts/{id}/
```

Response:
```json
{
    "id": "uuid",
    "name": "Acme Corp",
    "industry": "Technology",
    "custom_fields": {
        "industry_segment": "Enterprise",
        "contract_renewal_date": "2024-12-31",
        "preferred_support_tier": "Premium"
    }
}
```

### Update Custom Fields
```
PATCH /api/v1/accounts/{id}/
{
    "custom_fields": {
        "industry_segment": "Mid-Market",
        "contract_renewal_date": "2025-06-30"
    }
}
```

## UI Considerations

### Dynamic Form Generation
Forms should be generated dynamically based on CustomField definitions:

1. Fetch field definitions for entity type
2. Render appropriate input component for each field type
3. Apply validation rules
4. Handle conditional visibility (if implemented)

### Admin Interface
Provide UI for administrators to:
- Create new custom fields
- Edit field properties
- Reorder fields
- Set visibility/editability
- Preview field in form

## Performance Optimization

### Caching
Cache custom field definitions per company:

```python
from django.core.cache import cache

def get_custom_fields_for_entity(company_id, entity_type):
    cache_key = f"custom_fields:{company_id}:{entity_type}"
    fields = cache.get(cache_key)
    
    if fields is None:
        fields = list(CustomField.objects.filter(
            company_id=company_id,
            entity_type=entity_type,
            is_visible=True
        ).order_by('display_order'))
        
        cache.set(cache_key, fields, timeout=3600)  # 1 hour
    
    return fields
```

### Indexing (Phase 3 with Pivot Table)
- Index commonly queried custom fields
- Consider PostgreSQL GIN indexes for JSON search
- Use database triggers to maintain search indexes

## Future Enhancements (Phase 3+)

1. **Conditional Fields**
   - Show/hide fields based on other field values
   - Dynamic validation rules

2. **Formula Fields**
   - Calculated fields based on other field values
   - Support for basic formulas (SUM, AVERAGE, etc.)

3. **Field Dependencies**
   - Cascade updates between related fields
   - Lookup fields from related entities

4. **Field History**
   - Track changes to custom field values
   - Audit trail for compliance

5. **Bulk Operations**
   - Bulk update custom field values
   - Import/export with custom fields

6. **Advanced Field Types**
   - File upload
   - Rich text editor
   - Geo-location
   - Color picker

7. **Field Permissions**
   - Role-based field visibility
   - Read-only fields for certain roles

## Testing Checklist

- [ ] Create custom field via API
- [ ] Update entity with custom field values
- [ ] Validate required fields
- [ ] Validate field types (number, email, etc.)
- [ ] Test choice field with invalid choice
- [ ] Test unique constraint (if implemented)
- [ ] Test custom field ordering
- [ ] Test visibility flag
- [ ] Test searchability flag
- [ ] Test cross-company isolation
- [ ] Performance test with 50+ custom fields
- [ ] Cache invalidation test
