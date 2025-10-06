# Activities Timeline

## Overview
Unified timeline system for tracking all activities and system events across CRM entities.

## Event Types

### User-Generated Events
- `note` - User added a note/comment
- `call` - Phone call logged
- `email` - Email sent/received
- `meeting` - Meeting scheduled/completed
- `task_completed` - Task marked as complete

### System Events
- `lead_converted` - Lead converted to contact/account
- `status_change` - Record status updated
- `field_updated` - Field value changed
- `record_created` - New record created
- `record_deleted` - Record deleted
- `assignment_changed` - Owner/assignee changed

### Custom Events
- `custom` - Application-specific events

## Data Model

### TimelineEvent
```python
class TimelineEvent(TenantOwnedModel):
    event_type = CharField(choices=EVENT_TYPE_CHOICES)
    actor = ForeignKey(User, null=True)  # Who did it
    target_content_type = ForeignKey(ContentType)  # What type
    target_object_id = IntegerField()  # Which instance
    data = JSONField()  # Event-specific data
    description = TextField()  # Human-readable summary
    created_at = DateTimeField(auto_now_add=True)
```

### Generic Foreign Key
The `target` uses Django's GenericForeignKey to link to any model:
- Account
- Contact
- Lead
- Deal
- Product
- etc.

## Event Taxonomy

### Lead Conversion Event
```json
{
    "event_type": "lead_converted",
    "actor": {
        "id": 123,
        "name": "John Sales",
        "email": "john@company.com"
    },
    "target": {
        "type": "lead",
        "id": 456,
        "name": "Acme Corp Lead"
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

### Status Change Event
```json
{
    "event_type": "status_change",
    "actor": {
        "id": 123,
        "name": "John Sales"
    },
    "target": {
        "type": "lead",
        "id": 456
    },
    "data": {
        "old_status": "new",
        "new_status": "contacted"
    },
    "description": "Status changed from new to contacted",
    "created_at": "2025-01-06T09:15:00Z"
}
```

### Note Event
```json
{
    "event_type": "note",
    "actor": {
        "id": 123,
        "name": "John Sales"
    },
    "target": {
        "type": "account",
        "id": 101
    },
    "data": {
        "note": "Discussed pricing options. Client interested in Enterprise plan."
    },
    "description": "Discussed pricing options...",
    "created_at": "2025-01-06T14:20:00Z"
}
```

## API Endpoints

### Fetch Timeline for Object

```http
GET /api/v1/activities/timeline/?object_type=account&object_id=101&limit=50
```

Response:
```json
{
    "object_type": "account",
    "object_id": 101,
    "events": [
        {
            "id": 1,
            "event_type": "note",
            "event_type_display": "Note",
            "actor": {
                "id": 123,
                "name": "John Sales",
                "email": "john@company.com"
            },
            "target_type": "account",
            "target_id": 101,
            "data": {...},
            "summary": "John Sales added a note",
            "created_at": "2025-01-06T14:20:00Z"
        }
    ],
    "next_cursor": 12345,
    "has_more": true
}
```

### Cursor-Based Pagination

```http
GET /api/v1/activities/timeline/?object_type=account&object_id=101&cursor=12345
```

The cursor is the ID of the last event from the previous page.

### Filter by Event Type

```http
GET /api/v1/activities/timeline/?object_type=lead&object_id=456&event_type=note
```

### Recent Timeline (Organization-Wide)

```http
GET /api/v1/activities/timeline/?limit=20
```

Returns recent events across all entities in the organization.

## Recording Events

### Using Timeline Service

```python
from crm.activities.services.timeline_service import record_event

# Record generic event
record_event(
    event_type='note',
    target=account,
    actor=current_user,
    data={'note': 'Follow-up scheduled for next week'},
    description='Follow-up scheduled'
)

# Record status change
from crm.activities.services.timeline_service import record_status_change

record_status_change(
    target=lead,
    old_status='new',
    new_status='contacted',
    actor=current_user
)

# Record assignment change
from crm.activities.services.timeline_service import record_assignment_change

record_assignment_change(
    target=account,
    old_owner=previous_owner,
    new_owner=new_owner,
    actor=current_user
)
```

### Automatic Event Recording

Events are automatically recorded in:
- Lead conversion (see `lead_service.convert_lead()`)
- Status changes (via model signal or service layer)
- Assignment changes (via service layer)

## Display Formatting

### Event Summary Generation

The `TimelineEvent.get_event_summary()` method generates human-readable summaries:

```python
def get_event_summary(self) -> str:
    actor_name = self.actor.get_full_name() if self.actor else 'System'
    
    if self.event_type == 'lead_converted':
        contact_name = self.data.get('contact_name', 'Unknown')
        return f"{actor_name} converted lead to {contact_name}"
    
    elif self.event_type == 'status_change':
        old = self.data.get('old_status', 'Unknown')
        new = self.data.get('new_status', 'Unknown')
        return f"{actor_name} changed status from {old} to {new}"
    
    # ... etc
```

### UI Rendering

Timeline events should be rendered as a vertical list:
- Most recent at top
- Actor avatar/icon
- Event summary
- Timestamp (relative: "2 hours ago")
- Expand to show full details/data

## Performance Considerations

### Indexes
```sql
CREATE INDEX timeline_org_type_created 
    ON crm_timeline_events(organization_id, event_type, created_at DESC);

CREATE INDEX timeline_target 
    ON crm_timeline_events(
        organization_id,
        target_content_type_id,
        target_object_id,
        created_at DESC
    );
```

### Pagination
- Use cursor-based pagination (not offset)
- Default limit: 50 events
- Maximum limit: 100 events

### Caching
- Consider caching recent timeline for frequently accessed objects
- Cache key: `timeline:{object_type}:{object_id}:recent`
- TTL: 5 minutes

## Future Enhancements

- [ ] Event aggregation (e.g., "3 fields updated")
- [ ] Event filtering by actor
- [ ] Export timeline to PDF/CSV
- [ ] Email notifications for timeline events
- [ ] Webhook triggers for timeline events
- [ ] Activity analytics and reporting
- [ ] Timeline event search
- [ ] Bulk event recording
- [ ] Event templates
- [ ] Rich text formatting for notes

## Best Practices

1. **Be Descriptive**: Use clear, actionable descriptions
2. **Include Context**: Store relevant data in `data` field
3. **Use Appropriate Types**: Don't overuse `custom` event type
4. **Keep Data Lean**: Don't duplicate entity data in events
5. **Index Properly**: Timeline queries are frequent
6. **Monitor Growth**: Archive old events if needed
7. **Test Ordering**: Ensure events display chronologically

## Security

- Events inherit target object permissions
- Users can only see timeline for objects they can view
- Event data should not expose sensitive information
- System events (no actor) visible to all with object access
