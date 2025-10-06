# Lead Conversion Flow

## Overview
Lead conversion transforms a Lead into Contact (and optionally Account), preserving data and creating audit trail.

## Conversion Rules

### Prerequisites
- Lead must have either:
  - `primary_email` (preferred), OR
  - Both `first_name` AND `last_name`
- Lead status must NOT be `'converted'`

### Deduplication Strategy

#### Contact Deduplication
1. Search for existing Contact by `primary_email` in same organization
2. If found: Reuse existing contact
3. If not found: Create new contact

#### Account Deduplication
1. If `create_account=True` and `company_name` exists:
   - Search for existing Account by exact `name` match
   - If found: Reuse existing account
   - If not found: Create new account
2. If `create_account=False` or no `company_name`:
   - No account created
   - Contact remains unlinked to account

### Field Mapping

#### Lead → Contact
```
first_name     → first_name
last_name      → last_name
primary_email  → primary_email
phone          → phone
mobile         → mobile
title          → title
owner          → owner (or conversion user)
```

#### Lead → Account
```
company_name      → name
primary_email     → primary_email
phone             → phone
industry          → industry
annual_revenue    → annual_revenue
employee_count    → employee_count
address_line1     → billing_address_line1
address_line2     → billing_address_line2
city              → billing_city
state             → billing_state
postal_code       → billing_postal_code
country           → billing_country
owner             → owner (or conversion user)
```

## Conversion Flow Diagram

```
┌─────────────────┐
│   Lead Ready    │
│  for Conversion │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│ Check if already        │
│ converted               │
└────────┬─────┬──────────┘
         │     │ Already converted
         │     └──────────► Error
         │ Not converted
         ▼
┌─────────────────────────┐
│ Validate prerequisites  │
│ (email or name)         │
└────────┬─────┬──────────┘
         │     │ Invalid
         │     └──────────► Error
         │ Valid
         ▼
┌─────────────────────────┐
│ Search for existing     │
│ Contact by email        │
└────────┬─────┬──────────┘
         │     │ Found
         │     │
         │     ▼
         │   ┌─────────────────┐
         │   │ Reuse Contact   │
         │   └────────┬────────┘
         │            │
         │ Not found  │
         ▼            │
┌─────────────────┐   │
│ Create Contact  │   │
└────────┬────────┘   │
         │            │
         └────────┬───┘
                  │
                  ▼
┌─────────────────────────┐
│ create_account=True?    │
└────────┬─────┬──────────┘
         │     │ False
         │     └──────────► Skip Account
         │ True
         ▼
┌─────────────────────────┐
│ Search for existing     │
│ Account by name         │
└────────┬─────┬──────────┘
         │     │ Found
         │     │
         │     ▼
         │   ┌─────────────────┐
         │   │ Reuse Account   │
         │   └────────┬────────┘
         │            │
         │ Not found  │
         ▼            │
┌─────────────────┐   │
│ Create Account  │   │
└────────┬────────┘   │
         │            │
         └────────┬───┘
                  │
                  ▼
┌─────────────────────────┐
│ Link Contact to Account │
│ (if not already)        │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Update Lead:            │
│ - status = 'converted'  │
│ - converted_at = now    │
│ - converted_account     │
│ - converted_contact     │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Create Timeline Event   │
│ 'lead_converted'        │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│ Return ConversionResult │
└─────────────────────────┘
```

## API Usage

### Endpoint
```http
POST /api/v1/leads/{id}/convert/
```

### Request Body
```json
{
    "create_account": true
}
```

### Response
```json
{
    "message": "Lead converted successfully",
    "lead_id": 456,
    "contact": {
        "id": 789,
        "name": "Jane Smith",
        "email": "jane@acme.com",
        "was_created": false
    },
    "account": {
        "id": 101,
        "name": "Acme Corporation",
        "was_created": true
    },
    "timeline_event_id": 1234
}
```

## Service Layer Usage

```python
from crm.leads.services.lead_service import convert_lead

result = convert_lead(
    lead_id=456,
    create_account=True,
    user=current_user
)

print(f"Lead: {result.lead}")
print(f"Contact: {result.contact} (created: {result.was_contact_created})")
print(f"Account: {result.account} (created: {result.was_account_created})")
```

## ConversionResult Dataclass

```python
@dataclass
class ConversionResult:
    lead: Lead
    account: Optional[Account]
    contact: Contact
    was_account_created: bool
    was_contact_created: bool
```

## Timeline Event

Conversion automatically creates a timeline event:

```json
{
    "event_type": "lead_converted",
    "actor": {
        "id": 123,
        "name": "John Sales"
    },
    "target": {
        "type": "lead",
        "id": 456
    },
    "data": {
        "lead_id": 456,
        "lead_name": "Acme Corp Lead",
        "contact_id": 789,
        "contact_name": "Jane Smith",
        "account_id": 101,
        "account_name": "Acme Corporation",
        "was_account_created": true,
        "was_contact_created": false
    },
    "created_at": "2025-01-06T10:30:00Z"
}
```

## Error Handling

### Already Converted
```python
ValueError: "Lead 456 has already been converted"
```

### Missing Required Data
```python
ValueError: "Lead must have email or full name to be converted"
```

### Permission Denied
```python
PermissionError: "User does not have 'convert' permission on leads"
```

## Database Transaction

The entire conversion is wrapped in a transaction:
- If any step fails, all changes are rolled back
- Lead remains in original state
- No partial conversions

```python
@transaction.atomic
def convert_lead(...):
    # All operations here are atomic
    ...
```

## Validation Pre-Checks

Before conversion starts:
1. ✅ Lead exists
2. ✅ Lead not already converted
3. ✅ Lead has email OR full name
4. ✅ User has 'convert' permission
5. ✅ Lock lead record (SELECT FOR UPDATE)

## Post-Conversion State

### Lead
- `status` = 'converted'
- `converted_at` = current timestamp
- `converted_account` = FK to Account (if created)
- `converted_contact` = FK to Contact
- `is_active` = True (remains active for history)

### Contact
- New or existing record
- Linked to Account (if account was created/found)
- `owner` set to lead owner or conversion user
- `status` = 'active'

### Account
- New or existing record
- Contains business information from lead
- `type` = 'customer' (default)
- `status` = 'active'

## UI Considerations

### Convert Button
- Shown on lead detail page
- Disabled if already converted
- Shows modal/form with options:
  - ☑️ Create Account
  - Input: Deal name (optional)
  - Input: Deal amount (optional)

### Post-Conversion
- Redirect to contact detail page
- Show success notification
- Display "Converted from Lead #456" banner
- Link back to original lead

### Bulk Conversion
- Select multiple qualified leads
- Apply same conversion settings to all
- Show results summary (success/failed)

## Testing Scenarios

1. **Basic Conversion**: Lead → Contact + Account
2. **Reuse Existing Contact**: Lead with known email
3. **Reuse Existing Account**: Lead with known company
4. **Contact Only**: create_account=False
5. **Already Converted**: Should fail
6. **Missing Data**: Should fail
7. **Permission Check**: Non-privileged user blocked
8. **Transaction Rollback**: Partial failure rolls back

## Performance

- Conversion is fast (< 100ms typical)
- Uses SELECT FOR UPDATE to prevent concurrent conversions
- Minimal database queries (2-4 total)
- Timeline event creation is non-blocking (fails silently if error)

## Monitoring

Track conversion metrics:
- Conversion rate (leads → contacts)
- Average time from lead creation to conversion
- Duplicate detection rate
- Failed conversions and reasons

## Future Enhancements

- [ ] Bulk lead conversion API
- [ ] Conversion workflows (custom rules)
- [ ] Conditional field mappings
- [ ] Deal creation during conversion
- [ ] Email notification on conversion
- [ ] Lead merge before conversion
- [ ] Rollback/undo conversion
- [ ] Conversion templates
