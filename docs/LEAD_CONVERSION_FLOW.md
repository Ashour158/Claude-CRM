# Lead Conversion Flow

## Overview
The lead conversion process transforms a qualified lead into an Account (company) and Contact (person), optionally creating a Deal/Opportunity.

## Process Flow

```
┌─────────────────┐
│  Qualified Lead │
└────────┬────────┘
         │
         ▼
┌────────────────────────────────┐
│  Pre-Conversion Validation     │
│  - Check lead status           │
│  - Verify required fields      │
│  - Check for duplicates        │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  User Chooses Options:         │
│  □ Create Account              │
│  □ Link to Existing Account    │
│  □ Create Deal                 │
└────────┬───────────────────────┘
         │
         ▼
┌────────────────────────────────┐
│  Transaction Begins            │
│  (select_for_update)           │
└────────┬───────────────────────┘
         │
         ├──────────────────────┐
         │                      │
         ▼                      ▼
┌─────────────────┐    ┌─────────────────┐
│ Create Account  │    │ Link Existing   │
│ (if requested)  │    │ Account         │
└────────┬────────┘    └────────┬────────┘
         │                      │
         └──────────┬───────────┘
                    │
                    ▼
         ┌────────────────────┐
         │  Create Contact    │
         │  - Copy fields     │
         │  - Link to Account │
         └────────┬───────────┘
                  │
                  ▼
         ┌────────────────────┐
         │  Create Deal       │
         │  (if requested)    │
         └────────┬───────────┘
                  │
                  ▼
         ┌────────────────────┐
         │  Update Lead       │
         │  - status=converted│
         │  - converted_at    │
         │  - links to created│
         └────────┬───────────┘
                  │
                  ▼
         ┌────────────────────┐
         │  Record Timeline   │
         │  Event             │
         └────────┬───────────┘
                  │
                  ▼
         ┌────────────────────┐
         │  Transaction       │
         │  Commits           │
         └────────┬───────────┘
                  │
                  ▼
         ┌────────────────────┐
         │  Return Result     │
         │  - lead_id         │
         │  - contact_id      │
         │  - account_id      │
         │  - deal_id         │
         └────────────────────┘
```

## Service API

### LeadConversionService.convert_lead()

```python
from crm.leads.services import LeadConversionService

result = LeadConversionService.convert_lead(
    lead_id=lead.id,
    create_account=True,
    user=request.user,
    organization=current_org
)

# Result object
print(result.lead_id)      # UUID of original lead
print(result.contact_id)   # UUID of created contact
print(result.account_id)   # UUID of created/linked account
print(result.status)       # 'success' or 'error'
print(result.message)      # Human-readable message
```

### Parameters
- **lead_id** (required): UUID of the lead to convert
- **create_account** (optional, default=True): Whether to create a new account
- **user** (optional): User performing the conversion (for audit trail)
- **organization** (optional): Organization context (uses lead's org if not provided)

### Return Value
Returns a `LeadConversionResult` object with:
- `lead_id`: UUID of the lead
- `contact_id`: UUID of created contact
- `account_id`: UUID of created/linked account (or None)
- `status`: 'success' or 'error'
- `message`: Human-readable status message

### Exceptions
- `Lead.DoesNotExist`: If lead doesn't exist
- `AlreadyConvertedError`: If lead was already converted
- `ValidationError`: If conversion fails validation

## Field Mapping

### Lead → Account
| Lead Field | Account Field | Notes |
|------------|---------------|-------|
| company_name | name | Required if no first/last name |
| email | email | |
| phone | phone | |
| website | website | |
| industry | industry | |
| annual_revenue | annual_revenue | |
| employee_count | employee_count | |
| address_line1 | billing_address_line1 | |
| address_line2 | billing_address_line2 | |
| city | billing_city | |
| state | billing_state | |
| postal_code | billing_postal_code | |
| country | billing_country | |
| territory | territory | |
| owner | owner | Falls back to conversion user |
| description | description | |
| custom_data | custom_data | Copied if present |

### Lead → Contact
| Lead Field | Contact Field | Notes |
|------------|---------------|-------|
| first_name | first_name | |
| last_name | last_name | |
| full_name | full_name | Auto-generated if empty |
| title | title | Job title |
| email | email | |
| phone | phone | |
| mobile | mobile | |
| - | account | Links to created/existing account |
| owner | owner | Falls back to conversion user |
| address_line1 | mailing_address_line1 | |
| address_line2 | mailing_address_line2 | |
| city | mailing_city | |
| state | mailing_state | |
| postal_code | mailing_postal_code | |
| country | mailing_country | |
| description | description | |
| custom_data | custom_data | Copied if present |

## Duplicate Detection

### Account Duplication Check
Before creating a new account, the system checks:
1. Exact match on company_name within the organization
2. If found, links to existing account instead of creating new one

```python
existing_account = Account.objects.filter(
    organization=lead.organization,
    name=lead.company_name
).first()

if existing_account:
    return existing_account  # Use existing
else:
    # Create new account
```

### Contact Duplication Check
Before creating a new contact, the system checks:
1. Exact match on email within the organization
2. If found, updates account link if needed
3. Returns existing contact

```python
existing_contact = Contact.objects.filter(
    organization=lead.organization,
    email=lead.email
).first()

if existing_contact:
    if account and not existing_contact.account:
        existing_contact.account = account
        existing_contact.save()
    return existing_contact
else:
    # Create new contact
```

## Pre-Conversion Validation

### LeadConversionService.can_convert_lead()
Check if a lead can be converted before attempting conversion.

```python
can_convert, reason = LeadConversionService.can_convert_lead(lead_id)

if can_convert:
    # Proceed with conversion
    result = LeadConversionService.convert_lead(lead_id)
else:
    # Show error to user
    print(f"Cannot convert: {reason}")
```

### Validation Rules
1. ✅ Lead exists
2. ✅ Lead is not already converted (status != 'converted')
3. ✅ Lead has either name (first/last) or company_name
4. ✅ Lead is not unqualified (status != 'unqualified')

## Concurrency Control

### Race Condition Prevention
Uses `select_for_update()` to lock the lead record during conversion:

```python
@transaction.atomic
def convert_lead(lead_id, ...):
    lead = Lead.objects.select_for_update().get(id=lead_id)
    # ... conversion logic ...
```

This ensures:
- Only one conversion can happen at a time per lead
- No duplicate accounts/contacts from simultaneous conversions
- Consistent state during the entire transaction

## Timeline Event

### Recorded Event
Upon successful conversion, a timeline event is recorded:

```json
{
  "event_type": "lead_converted",
  "actor": {
    "id": "user-uuid",
    "email": "user@example.com"
  },
  "target_object": {
    "type": "lead",
    "id": "lead-uuid"
  },
  "data": {
    "contact_id": "contact-uuid",
    "account_id": "account-uuid",
    "converted_at": "2024-01-15T10:30:00Z"
  },
  "summary": "Lead converted to Contact: Jane Smith at Account: Acme Corp",
  "is_system_generated": false
}
```

## Usage Examples

### Basic Conversion
```python
from crm.leads.services import LeadConversionService

# Convert lead with all defaults
result = LeadConversionService.convert_lead(
    lead_id=lead.id,
    user=request.user
)

if result.status == 'success':
    print(f"Created contact: {result.contact_id}")
    print(f"Created account: {result.account_id}")
```

### Convert Without Creating Account
```python
# Contact only, no account
result = LeadConversionService.convert_lead(
    lead_id=lead.id,
    create_account=False,
    user=request.user
)
```

### With Error Handling
```python
from crm.leads.services import LeadConversionService, AlreadyConvertedError

try:
    result = LeadConversionService.convert_lead(
        lead_id=lead.id,
        user=request.user
    )
    print(f"Success: {result.message}")
    
except AlreadyConvertedError as e:
    print(f"Already converted: {e}")
    
except Lead.DoesNotExist:
    print("Lead not found")
    
except ValidationError as e:
    print(f"Validation failed: {e}")
```

### Pre-flight Check
```python
# Check before showing convert button
can_convert, reason = LeadConversionService.can_convert_lead(lead.id)

if can_convert:
    # Show convert button
    return render(template, {'show_convert': True})
else:
    # Show reason why conversion is disabled
    return render(template, {
        'show_convert': False,
        'convert_disabled_reason': reason
    })
```

## API Endpoint (Future)

### POST /api/v1/leads/{id}/convert/

```python
# Request
POST /api/v1/leads/123e4567-e89b-12d3-a456-426614174000/convert/
Content-Type: application/json

{
  "create_account": true,
  "create_deal": false,
  "deal_amount": null
}

# Response (Success)
HTTP 200 OK
{
  "status": "success",
  "message": "Lead successfully converted",
  "data": {
    "lead_id": "123e4567-e89b-12d3-a456-426614174000",
    "contact_id": "contact-uuid",
    "account_id": "account-uuid",
    "deal_id": null
  }
}

# Response (Error)
HTTP 400 Bad Request
{
  "status": "error",
  "message": "Lead is already converted",
  "code": "ALREADY_CONVERTED"
}
```

## Testing

### Test Cases
1. ✅ Convert qualified lead successfully
2. ✅ Prevent converting already-converted lead
3. ✅ Create account when requested
4. ✅ Skip account creation when requested
5. ✅ Link to existing account if duplicate found
6. ✅ Link to existing contact if duplicate found
7. ✅ Copy custom fields correctly
8. ✅ Record timeline event
9. ✅ Handle concurrent conversion attempts
10. ✅ Validate lead status before conversion

## Best Practices

1. **Always check** if lead can be converted before showing convert option
2. **Show preview** of what will be created before converting
3. **Allow review** of duplicate matches before proceeding
4. **Provide feedback** on what was created after conversion
5. **Log all conversions** for audit trail
6. **Handle errors gracefully** with user-friendly messages

## Future Enhancements

### Phase 3
- [ ] Deal creation during conversion
- [ ] Bulk lead conversion
- [ ] Conversion templates (preset field mappings)
- [ ] Conversion approval workflow
- [ ] Undo conversion (within time window)

### Phase 4
- [ ] Smart duplicate detection (fuzzy matching)
- [ ] Merge duplicate accounts/contacts
- [ ] Conversion analytics dashboard
- [ ] AI-suggested conversions
- [ ] Custom conversion rules per organization
