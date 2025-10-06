# Activities Timeline

## Overview
The timeline system provides a unified view of all activities and events related to CRM objects (Leads, Accounts, Contacts, Deals).

## TimelineEvent Model

### Architecture
Uses GenericForeignKey to relate events to any model type.

```python
class TimelineEvent(TenantOwnedModel):
    event_type              # Type of event (note, email, call, etc.)
    actor                   # User who triggered the event
    target_content_type     # Type of related object
    target_object_id        # ID of related object
    target_object           # GenericForeignKey
    data                    # JSON data for event details
    summary                 # Human-readable summary
    is_system_generated     # Auto-generated vs manual
```

## Event Types

| Event Type | Description | Typical Data |
|------------|-------------|--------------|
| `note` | General note/comment | `{text, mentions}` |
| `email` | Email sent/received | `{subject, from, to, body_preview}` |
| `call` | Phone call | `{duration, outcome, notes}` |
| `meeting` | Meeting held | `{attendees, duration, location}` |
| `task_completed` | Task completed | `{task_name, assigned_to}` |
| `status_change` | Status changed | `{from_status, to_status, reason}` |
| `lead_converted` | Lead converted | `{contact_id, account_id}` |
| `deal_won` | Deal won | `{amount, close_date}` |
| `deal_lost` | Deal lost | `{reason, competitor}` |
| `field_updated` | Field value changed | `{field_name, old_value, new_value}` |
| `file_attached` | File attached | `{filename, file_size, file_type}` |
| `custom` | Custom event | `{...custom_data}` |

## API Endpoint

### Timeline Endpoint
**GET** `/api/v1/activities/timeline/`

#### Query Parameters
- `object_type` (required): Type of object (e.g., 'lead', 'account', 'contact')
- `object_id` (required): ID of the object
- `event_type` (optional): Filter by event type
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Results per page (default: 50, max: 100)

#### Response Format
```json
{
  "object": {
    "type": "lead",
    "id": "123e4567-e89b-12d3-a456-426614174000"
  },
  "events": [
    {
      "id": "uuid-here",
      "event_type": "note",
      "actor": {
        "id": "user-uuid",
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe"
      },
      "object_type": "lead",
      "object_id": "123e4567-e89b-12d3-a456-426614174000",
      "data": {
        "text": "Follow up call scheduled",
        "mentions": ["@jane"]
      },
      "summary": "Added note: Follow up call scheduled",
      "is_system_generated": false,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": "uuid-here",
      "event_type": "lead_converted",
      "actor": {
        "id": "user-uuid",
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe"
      },
      "object_type": "lead",
      "object_id": "123e4567-e89b-12d3-a456-426614174000",
      "data": {
        "contact_id": "contact-uuid",
        "account_id": "account-uuid",
        "converted_at": "2024-01-14T15:20:00Z"
      },
      "summary": "Lead converted to Contact: Jane Smith at Account: Acme Corp",
      "is_system_generated": true,
      "created_at": "2024-01-14T15:20:00Z",
      "updated_at": "2024-01-14T15:20:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 50,
    "total": 100
  }
}
```

## Recording Events

### Using TimelineEvent.record()
```python
from crm.activities.models import TimelineEvent

# Record a note
TimelineEvent.record(
    event_type='note',
    target_object=lead_instance,
    actor=current_user,
    data={'text': 'Called customer, very interested'},
    summary='Added note about customer call'
)

# Record lead conversion
TimelineEvent.record(
    event_type='lead_converted',
    target_object=lead,
    actor=user,
    data={
        'contact_id': str(contact.id),
        'account_id': str(account.id),
        'converted_at': timezone.now().isoformat()
    },
    summary=f"Lead converted to Contact: {contact.full_name}"
)

# System-generated event (no actor)
TimelineEvent.record(
    event_type='status_change',
    target_object=deal,
    data={
        'from_status': 'negotiation',
        'to_status': 'closed_won',
        'automated': True
    },
    summary='Status automatically changed to Closed Won'
)
```

## Event Data Schemas

### Note Event
```json
{
  "text": "Note content",
  "mentions": ["@user1", "@user2"],
  "attachments": ["file-id-1", "file-id-2"]
}
```

### Email Event
```json
{
  "subject": "Email subject",
  "from": "sender@example.com",
  "to": ["recipient@example.com"],
  "cc": ["cc@example.com"],
  "body_preview": "First 200 chars...",
  "message_id": "email-msg-id",
  "thread_id": "email-thread-id",
  "sent_at": "2024-01-15T10:30:00Z"
}
```

### Call Event
```json
{
  "direction": "outbound",
  "duration_seconds": 300,
  "outcome": "successful",
  "notes": "Discussed pricing",
  "recording_url": "https://...",
  "phone_number": "+1-555-0123"
}
```

### Meeting Event
```json
{
  "title": "Product Demo",
  "attendees": ["user1-id", "user2-id"],
  "duration_minutes": 60,
  "location": "Conference Room A",
  "meeting_url": "https://zoom.us/...",
  "outcome": "positive"
}
```

### Status Change Event
```json
{
  "field_name": "status",
  "from_value": "qualified",
  "to_value": "converted",
  "reason": "Lead successfully converted",
  "automated": false
}
```

### Lead Converted Event
```json
{
  "contact_id": "uuid",
  "account_id": "uuid",
  "deal_id": "uuid",  // optional
  "converted_at": "2024-01-15T10:30:00Z"
}
```

## Querying Timeline

### Get All Events for a Lead
```python
from django.contrib.contenttypes.models import ContentType
from crm.activities.models import TimelineEvent

content_type = ContentType.objects.get(model='lead')
events = TimelineEvent.objects.filter(
    target_content_type=content_type,
    target_object_id=lead_id
).order_by('-created_at')
```

### Get Specific Event Types
```python
# Only notes and calls
events = TimelineEvent.objects.filter(
    target_content_type=content_type,
    target_object_id=lead_id,
    event_type__in=['note', 'call']
).order_by('-created_at')
```

### Get Events by Actor
```python
# Events by specific user
events = TimelineEvent.objects.filter(
    target_content_type=content_type,
    target_object_id=lead_id,
    actor=user
).order_by('-created_at')
```

## Future Events (Phase 3+)

### Planned Event Types
- `quote_sent` - Quote sent to customer
- `quote_accepted` - Quote accepted by customer
- `quote_rejected` - Quote rejected by customer
- `invoice_sent` - Invoice sent
- `payment_received` - Payment received
- `contract_signed` - Contract signed
- `support_ticket_created` - Support ticket created
- `feedback_received` - Customer feedback
- `campaign_response` - Marketing campaign response
- `social_mention` - Social media mention

### Event Aggregation
```json
{
  "event_type": "activity_summary",
  "data": {
    "period": "last_7_days",
    "call_count": 5,
    "email_count": 12,
    "meeting_count": 2,
    "note_count": 8
  }
}
```

### Event Notifications
- Real-time notifications via WebSocket
- Email digests
- Mobile push notifications

## UI Integration

### Timeline Display
Events should be displayed in reverse chronological order (newest first).

#### Grouping
- By date (Today, Yesterday, This Week, etc.)
- By type (All Notes, All Calls, etc.)
- By actor (All activities by John)

#### Filtering
- Date range picker
- Event type multi-select
- Actor filter
- Search in event content

#### Actions
- Add new note
- Log call
- Log meeting
- Attach file
- Edit/delete own events

### Event Icons
Suggested icons for event types:
- `note` - 📝 Comment icon
- `email` - 📧 Email icon
- `call` - 📞 Phone icon
- `meeting` - 📅 Calendar icon
- `task_completed` - ✅ Checkmark icon
- `status_change` - 🔄 Arrows icon
- `lead_converted` - 🎯 Target icon
- `deal_won` - 🏆 Trophy icon
- `deal_lost` - ❌ X icon
- `file_attached` - 📎 Paperclip icon

## Performance Optimization

### Indexing Strategy
```python
indexes = [
    models.Index(fields=['organization', '-created_at']),
    models.Index(fields=['organization', 'event_type', '-created_at']),
    models.Index(fields=['organization', 'target_content_type', 'target_object_id', '-created_at']),
    models.Index(fields=['organization', 'actor', '-created_at']),
]
```

### Pagination
- Default: 50 events per page
- Maximum: 100 events per page
- Use cursor-based pagination for large datasets

### Caching
- Cache recent events (last 24 hours) per object
- Invalidate on new event creation
- TTL: 5 minutes

## Event Retention

### Retention Policy
- All events: Retained indefinitely by default
- Organizations can configure retention periods
- Deleted events are soft-deleted (is_deleted=True)
- Hard delete after retention period + grace period

### Archive Strategy
- Events older than 2 years moved to archive table
- Archive table has same schema but different partition
- Archive queried only for historical reporting
