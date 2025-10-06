# API Pagination and Serializer Patterns

## Overview

This document describes the pagination and serializer patterns used in the CRM API.

## Pagination

### Timeline Pagination

The timeline endpoint uses custom pagination with the following characteristics:

- **Class**: `TimelinePagination` (in `activities/api/pagination.py`)
- **Default page size**: 50 items
- **Maximum page size**: 100 items
- **Query parameters**:
  - `page`: Page number (e.g., `?page=2`)
  - `page_size`: Custom page size (e.g., `?page_size=25`)

#### Example Usage

```bash
# Get first page (default 50 items)
GET /api/activities/timeline/

# Get specific page
GET /api/activities/timeline/?page=2

# Custom page size
GET /api/activities/timeline/?page_size=25

# Combined
GET /api/activities/timeline/?page=3&page_size=10
```

#### Response Structure

```json
{
  "count": 150,
  "next": "http://api.example.com/api/activities/timeline/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "event_type": "created",
      "created_at": "2024-01-01T12:00:00Z",
      "data": {},
      "title": "Event Title",
      "description": "Event description",
      "user": 1,
      "is_system_event": false
    }
    // ... more events
  ]
}
```

## Serializers

### TimelineEventSerializer

Located in `activities/api/serializers.py`, this serializer handles timeline events.

**Fields**:
- `id` (read-only): Event ID
- `event_type`: Type of event (created, updated, deleted, etc.)
- `created_at` (read-only): Timestamp
- `data`: JSON data associated with the event
- `title`: Event title
- `description`: Event description
- `user`: User who triggered the event
- `is_system_event`: Whether it's a system-generated event

### LeadConversionResultSerializer

Located in `crm/leads/api/serializers.py`, this serializer represents the result of lead conversion.

**Fields**:
- `lead_id`: ID of the converted lead
- `contact_id`: ID of the created contact
- `account_id` (nullable): ID of the created/associated account
- `created_account`: Boolean indicating if a new account was created
- `status`: Conversion status (e.g., "converted")
- `message` (optional): Additional message about the conversion

#### Example Response

```json
{
  "lead_id": 123,
  "contact_id": 456,
  "account_id": 789,
  "created_account": true,
  "status": "converted",
  "message": "Lead successfully converted to contact and account"
}
```

### SavedViewSerializer (Stub)

Located in `crm/leads/api/serializers.py`, this is a stub serializer for future saved view functionality.

**Fields**:
- `id` (read-only): View ID
- `name`: View name
- `filters`: JSON filter configuration
- `created_at` (read-only): Creation timestamp
- `updated_at` (read-only): Update timestamp

## Logging

### Lead Conversion Logging

Lead conversion operations are logged at INFO level using Django's logging framework.

**Logger**: `crm.views` (module-level logger)

**Log Events**:
- Successful conversion with created entity IDs
- Already converted attempts
- Duplicate account detection

**Example Log Entry**:
```
INFO Lead conversion successful: lead_id=123, contact_id=456, account_id=789, created_account=True, status=converted
```

## Testing

### Test Coverage

New tests have been added for:
- Timeline pagination (5 tests)
- Lead conversion with serializer validation (7 tests)
- Cross-organization isolation (5 tests)
- Management command for seeding roles/permissions (3 tests)
- Stub endpoints for future features (8 tests)

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api_timeline_pagination.py

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test class
pytest tests/test_api_timeline_pagination.py::TestTimelineAPIPagination
```

## Future Enhancements

- Cursor-based pagination for timeline (performance optimization)
- Real saved view persistence
- Role-based API permission enforcement
- Search backend integration
- Kanban board drag/drop persistence
