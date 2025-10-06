# Activities Timeline

## Overview
The Activities Timeline provides a chronological record of all events and interactions related to CRM entities (Accounts, Contacts, Leads, Deals).

## Architecture

### TimelineEvent Model
```python
class TimelineEvent(TenantOwnedModel):
    event_type = CharField()           # Type of event
    title = CharField()                # Event title/subject
    description = TextField()          # Detailed description
    target_content_type = ForeignKey() # Generic FK to any model
    target_object_id = CharField()     # Object ID
    event_date = DateTimeField()      # When event occurred
    actor = ForeignKey(User)           # Who triggered the event
    metadata = JSONField()             # Additional data
```

## Event Types

1. **call** - Phone call
2. **email** - Email communication
3. **meeting** - Meeting or appointment
4. **note** - Manual note/comment
5. **task** - Task created or completed
6. **status_change** - Status updated
7. **creation** - Record created
8. **update** - Record updated
9. **conversion** - Lead converted
10. **other** - Other activities

## Usage

### Recording Events

```python
from crm.activities.services.timeline_service import TimelineService

# Record a phone call
TimelineService.record_event(
    organization=org,
    target=account,
    event_type='call',
    title='Follow-up call with John',
    description='Discussed Q4 contract renewal',
    actor=request.user,
    metadata={'duration': 30, 'outcome': 'positive'}
)

# Convenience methods
TimelineService.record_creation(org, lead, actor=user)
TimelineService.record_update(org, contact, actor=user, changes={'phone': 'old->new'})
TimelineService.record_status_change(org, deal, 'qualified', 'proposal', actor=user)
```

### Fetching Timeline

```python
from crm.activities.selectors.timeline_selector import TimelineSelector

# Get timeline for specific entity
events = TimelineSelector.fetch_timeline(
    organization=org,
    target=account,
    event_types=['call', 'meeting', 'email'],
    limit=50
)

# Get recent activities across organization
recent = TimelineSelector.get_recent_activities(
    organization=org,
    days=7,
    limit=20
)

# Get user's activities
user_events = TimelineSelector.get_user_activities(
    organization=org,
    user=request.user,
    limit=20
)
```

### API Endpoint

```http
GET /api/v1/activities/timeline/?entity_type=account&entity_id=123&limit=50

Response:
{
  "count": 5,
  "events": [
    {
      "id": "uuid",
      "event_type": "call",
      "title": "Follow-up call with John",
      "description": "Discussed Q4 contract renewal",
      "event_date": "2024-10-06T10:30:00Z",
      "actor": {
        "id": "user-uuid",
        "name": "Jane Smith",
        "email": "jane@example.com"
      },
      "metadata": {
        "duration": 30,
        "outcome": "positive"
      }
    }
  ]
}
```

## Automatic Timeline Events

The system automatically records timeline events for certain actions:

### Lead Conversion
When a lead is converted:
```python
TimelineService.record_event(
    organization=lead.organization,
    target=lead,
    event_type='conversion',
    title=f"Lead converted to Account: {account.name}",
    description=f"Lead {lead.get_full_name()} converted to account, contact, and deal",
    actor=user,
    metadata={
        'account_id': str(account.id),
        'contact_id': str(contact.id),
        'deal_id': str(deal.id)
    }
)
```

### Record Creation
Can be triggered via signals:
```python
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Account)
def account_created(sender, instance, created, **kwargs):
    if created:
        TimelineService.record_creation(
            organization=instance.organization,
            target=instance,
            actor=instance.created_by
        )
```

## Timeline Display

### UI Components
- Chronological list view
- Filterable by event type
- Searchable by content
- Paginated results
- Real-time updates (WebSocket)

### Display Format
```
📞 [10:30 AM] Follow-up call with John
   by Jane Smith
   Discussed Q4 contract renewal
   Duration: 30 minutes
   
📧 [Yesterday 2:15 PM] Email sent
   by System
   Sent proposal document to john@example.com
   
✅ [Oct 5] Lead converted
   by Jane Smith
   Lead John Doe converted to Account: Acme Corp
```

## Performance Considerations

### Indexes
```python
indexes = [
    models.Index(fields=['organization', '-event_date']),
    models.Index(fields=['target_content_type', 'target_object_id', '-event_date']),
    models.Index(fields=['event_type', '-event_date']),
]
```

### Query Optimization
- Use `select_related('actor')` to avoid N+1 queries
- Implement pagination for large timelines
- Cache recent events
- Consider archiving old events (>1 year)

### Scalability
For high-volume systems:
- Use time-series database for events
- Implement event streaming (Kafka)
- Archive to cold storage after 6-12 months
- Implement event aggregation

## Best Practices

1. **Be Descriptive**: Write clear, actionable titles
2. **Include Context**: Use metadata for additional details
3. **Consistent Format**: Maintain consistent event naming
4. **Performance**: Batch create events when possible
5. **Privacy**: Respect data access permissions
6. **Cleanup**: Archive old events periodically

## Integration with Other Systems

### Email Integration
```python
# When email is sent/received
TimelineService.record_event(
    organization=org,
    target=contact,
    event_type='email',
    title=f'Email: {email_subject}',
    description=email_body,
    actor=user,
    metadata={
        'from': email_from,
        'to': email_to,
        'cc': email_cc,
        'message_id': email_message_id
    }
)
```

### Calendar Integration
```python
# When meeting is scheduled
TimelineService.record_event(
    organization=org,
    target=deal,
    event_type='meeting',
    title=f'Meeting: {meeting_title}',
    description=meeting_description,
    actor=user,
    metadata={
        'start_time': meeting_start,
        'end_time': meeting_end,
        'location': meeting_location,
        'attendees': attendee_list
    }
)
```

## Future Enhancements

- **Attachments**: Support file attachments on events
- **Comments**: Allow commenting on events
- **Reactions**: Like/emoji reactions
- **Mentions**: @mention users in descriptions
- **Templates**: Event templates for common activities
- **Analytics**: Timeline analytics and insights
- **Export**: Export timeline to PDF/CSV

## Related Documentation

- [Domain Migration Status](./DOMAIN_MIGRATION_STATUS.md)
- [Lead Conversion Flow](./LEAD_CONVERSION_FLOW.md)
- [Permissions Matrix](./PERMISSIONS_MATRIX.md)
