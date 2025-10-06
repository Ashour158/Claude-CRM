# Lead Conversion Flow

## Overview
Lead conversion is the process of converting a qualified lead into an Account, Contact, and optionally a Deal. This is a critical workflow in the CRM system.

## Conversion Process

### Flow Diagram
```
Lead (Qualified)
    ↓
Validation Check
    ↓
Create/Match Account
    ↓
Create Contact
    ↓
Create Deal (optional)
    ↓
Update Lead Status
    ↓
Record Timeline Event
```

## Implementation

### API Endpoint
```http
POST /api/v1/leads/convert/
{
  "lead_id": "uuid",
  "create_deal": true,
  "deal_data": {
    "name": "Q4 Enterprise Deal",
    "amount": 50000.00
  }
}
```

### Service Layer
```python
from crm.leads.services.conversion_service import ConversionService

account, contact, deal = ConversionService.convert_lead(
    lead=lead,
    create_deal=True,
    deal_data={'amount': 50000.00},
    user=request.user
)
```

## Conversion Logic

### 1. Validation
Before conversion, the system checks:
- Lead is not already converted
- Required fields are present (email, first_name, last_name)
- User has permission to convert leads

```python
can_convert, reason = ConversionService.can_convert_lead(lead)
if not can_convert:
    raise ValueError(reason)
```

### 2. Account Creation
The system either:
- **Creates new account** if no match found
- **Uses existing account** if found by name + email

```python
account_data = {
    'name': lead.company_name or f"{lead.first_name} {lead.last_name}",
    'email': lead.email,
    'phone': lead.phone,
    'industry': lead.industry,
    'annual_revenue': lead.annual_revenue,
    'employee_count': lead.employee_count,
    # ... address fields
    'territory': lead.territory,
    'owner': lead.owner,
    'account_type': 'customer',
}

# Try to find existing account
account = Account.objects.for_organization(org).filter(
    name=account_data['name'],
    email=lead.email
).first()

if not account:
    account = AccountService.create_account(org, account_data, user)
```

### 3. Contact Creation
Always creates a new contact from lead data:

```python
contact = ContactService.create_from_lead(org, lead, user)
contact.account = account
contact.save()
```

### 4. Deal Creation (Optional)
If `create_deal=True`:

```python
deal = Deal.objects.create(
    company=org,
    name=deal_data.get('name', f"Deal - {account.name}"),
    account=account,
    contact=contact,
    amount=deal_data.get('amount', lead.budget or 0),
    owner=lead.owner,
    description=lead.description,
)
```

### 5. Lead Status Update
```python
lead.lead_status = 'converted'
lead.converted_at = timezone.now()
lead.converted_account = account
lead.converted_contact = contact
lead.converted_deal = deal
lead.updated_by = user
lead.save()
```

### 6. Timeline Event
```python
TimelineService.record_event(
    organization=org,
    target=lead,
    event_type='conversion',
    title=f"Lead converted to Account: {account.name}",
    description=f"Lead {lead.get_full_name()} converted",
    actor=user,
    metadata={
        'account_id': str(account.id),
        'contact_id': str(contact.id),
        'deal_id': str(deal.id) if deal else None,
    }
)
```

## Idempotency

The conversion process is idempotent:

```python
if lead.is_converted():
    raise ValueError("Lead has already been converted")
```

This prevents:
- Duplicate accounts/contacts
- Multiple conversions of same lead
- Data inconsistency

## Data Mapping

### Lead → Account
| Lead Field | Account Field |
|------------|---------------|
| company_name | name |
| email | email |
| phone | phone |
| website | website |
| industry | industry |
| annual_revenue | annual_revenue |
| employee_count | employee_count |
| address_line1 | billing_address_line1 |
| address_line2 | billing_address_line2 |
| city | billing_city |
| state | billing_state |
| postal_code | billing_postal_code |
| country | billing_country |
| territory | territory |
| owner | owner |
| custom_fields | custom_fields |

### Lead → Contact
| Lead Field | Contact Field |
|------------|---------------|
| first_name | first_name |
| last_name | last_name |
| title | title |
| email | email |
| phone | phone |
| mobile | mobile |
| address_line1 | mailing_address_line1 |
| address_line2 | mailing_address_line2 |
| city | mailing_city |
| state | mailing_state |
| postal_code | mailing_postal_code |
| country | mailing_country |
| owner | owner |
| description | description |
| custom_fields | custom_fields |

## Error Handling

### Common Errors
1. **Lead Already Converted**
   ```json
   {
     "error": "Lead has already been converted",
     "converted_account_id": "uuid",
     "converted_contact_id": "uuid"
   }
   ```

2. **Missing Required Fields**
   ```json
   {
     "error": "Email is required for conversion"
   }
   ```

3. **Permission Denied**
   ```json
   {
     "error": "You don't have permission to convert leads"
   }
   ```

### Transaction Safety
All operations are wrapped in a database transaction:
```python
@transaction.atomic
def convert_lead(lead, create_deal=True, deal_data=None, user=None):
    # All operations here are atomic
    # If any fails, all are rolled back
```

## Testing Lead Conversion

### Unit Test
```python
def test_lead_conversion_idempotent(org, lead, user):
    # First conversion
    account1, contact1, deal1 = ConversionService.convert_lead(lead, user=user)
    
    # Second attempt should fail
    with pytest.raises(ValueError, match="already been converted"):
        ConversionService.convert_lead(lead, user=user)
    
    # Verify original data unchanged
    lead.refresh_from_db()
    assert lead.converted_account == account1
```

### Integration Test
```python
def test_lead_conversion_api(api_client, org, lead):
    response = api_client.post('/api/v1/leads/convert/', {
        'lead_id': str(lead.id),
        'create_deal': True,
        'deal_data': {'amount': 50000}
    })
    
    assert response.status_code == 201
    assert response.data['success'] is True
    assert 'account' in response.data
    assert 'contact' in response.data
    assert 'deal' in response.data
```

## Best Practices

1. **Validate Before Converting**
   - Ensure lead is qualified
   - Check required fields
   - Verify permissions

2. **Handle Duplicates**
   - Search for existing accounts
   - Prevent duplicate creation
   - Merge if necessary

3. **Preserve History**
   - Keep lead record
   - Link to converted entities
   - Record timeline event

4. **User Experience**
   - Show progress indicator
   - Confirm before converting
   - Navigate to account after conversion

5. **Error Recovery**
   - Use transactions
   - Provide clear error messages
   - Allow retry on failure

## Customization Options

### Custom Conversion Rules
```python
class CustomConversionService(ConversionService):
    @staticmethod
    def convert_lead(lead, **kwargs):
        # Custom validation
        if lead.lead_score < 70:
            raise ValueError("Lead score too low for conversion")
        
        # Custom account matching logic
        # Custom deal creation logic
        
        return super().convert_lead(lead, **kwargs)
```

### Conditional Deal Creation
```python
# Only create deal if budget > $10,000
create_deal = lead.budget and lead.budget > 10000

account, contact, deal = ConversionService.convert_lead(
    lead,
    create_deal=create_deal,
    user=user
)
```

## Workflow Integration

### Approval Workflow
```python
# Require manager approval for high-value leads
if lead.budget > 100000:
    # Create approval request
    ApprovalRequest.objects.create(
        lead=lead,
        requested_by=user,
        approver=user.manager,
        status='pending'
    )
else:
    # Convert directly
    ConversionService.convert_lead(lead, user=user)
```

### Notification Workflow
```python
# After conversion, notify team
account, contact, deal = ConversionService.convert_lead(lead, user=user)

# Send notifications
NotificationService.send(
    users=[lead.owner, lead.owner.manager],
    title=f"Lead Converted: {account.name}",
    message=f"{user.get_full_name()} converted lead to account",
    link=f"/accounts/{account.id}"
)
```

## Related Documentation

- [Domain Migration Status](./DOMAIN_MIGRATION_STATUS.md)
- [Activities Timeline](./ACTIVITIES_TIMELINE.md)
- [Permissions Matrix](./PERMISSIONS_MATRIX.md)
