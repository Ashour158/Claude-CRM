# Saved Views Specification

## Overview

Persistent saved views allow users to save custom list filters, column selections, and sorting preferences for reuse across sessions.

## Features

- **Personal Views**: Private views visible only to the owner
- **Global Views**: Shared views visible to all users in the company
- **Entity Types**: Support for accounts, contacts, leads, deals, activities, tasks, quotes, orders, invoices
- **Server-side Validation**: JSON schema validation for view definitions
- **Access Control**: Role-based permissions for view management

## Data Model

### SavedListView

```python
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "entity_type": "account|contact|lead|deal|...",
  "definition": {
    "filters": [...],
    "columns": [...],
    "sort": [...]
  },
  "owner": "user_id or null",
  "is_private": boolean,
  "is_default": boolean,
  "company": "company_id",
  "created_at": "timestamp",
  "updated_at": "timestamp"
}
```

## View Definition Schema

### Filters

```json
{
  "filters": [
    {
      "field": "status",
      "operator": "equals",
      "value": "active"
    },
    {
      "field": "amount",
      "operator": "gte",
      "value": 10000
    }
  ]
}
```

**Supported Operators:**

| Operator | Description | Example |
|----------|-------------|---------|
| `equals` | Exact match | `status equals "active"` |
| `not_equals` | Not equal | `status not_equals "closed"` |
| `contains` | Contains text (case-insensitive) | `name contains "acme"` |
| `not_contains` | Does not contain | `name not_contains "test"` |
| `starts_with` | Starts with text | `email starts_with "admin"` |
| `ends_with` | Ends with text | `domain ends_with ".com"` |
| `gt` | Greater than | `amount gt 1000` |
| `gte` | Greater than or equal | `amount gte 1000` |
| `lt` | Less than | `amount lt 5000` |
| `lte` | Less than or equal | `amount lte 5000` |
| `in` | In list | `status in ["active", "pending"]` |
| `not_in` | Not in list | `status not_in ["closed"]` |
| `is_null` | Is null/empty | `notes is_null true` |
| `is_not_null` | Is not null/empty | `owner is_not_null true` |

### Columns

```json
{
  "columns": [
    "name",
    "email",
    "status",
    "created_at",
    "amount"
  ]
}
```

### Sorting

```json
{
  "sort": [
    {
      "field": "created_at",
      "direction": "desc"
    },
    {
      "field": "name",
      "direction": "asc"
    }
  ]
}
```

## API Endpoints

### List Saved Views

```
GET /api/core/saved-views/?entity_type=deal
```

**Query Parameters:**
- `entity_type` (optional): Filter by entity type

**Response:**

```json
[
  {
    "id": "uuid",
    "name": "My Active Deals",
    "description": "All my active deals over $10k",
    "entity_type": "deal",
    "definition": {...},
    "owner": "user_id",
    "owner_email": "user@example.com",
    "is_private": true,
    "is_default": false,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

### Create Saved View

```
POST /api/core/saved-views/
```

**Request Body:**

```json
{
  "name": "High Value Deals",
  "description": "Deals over $50k in negotiation",
  "entity_type": "deal",
  "definition": {
    "filters": [
      {
        "field": "amount",
        "operator": "gte",
        "value": 50000
      },
      {
        "field": "stage",
        "operator": "equals",
        "value": "negotiation"
      }
    ],
    "columns": ["name", "account", "amount", "owner", "expected_close_date"],
    "sort": [
      {
        "field": "amount",
        "direction": "desc"
      }
    ]
  },
  "is_private": true,
  "is_default": false
}
```

### Update Saved View

```
PUT /api/core/saved-views/{id}/
```

**Permissions:**
- Private views: Owner only
- Global views: Admin or Manager only

### Delete Saved View

```
DELETE /api/core/saved-views/{id}/
```

**Permissions:**
- Private views: Owner only
- Global views: Admin only

### Apply View

```
POST /api/core/saved-views/{id}/apply/
```

Returns the view definition for use in entity list endpoints.

**Response:**

```json
{
  "view_id": "uuid",
  "name": "High Value Deals",
  "entity_type": "deal",
  "definition": {...},
  "message": "Apply these filters and sort in the entity list endpoint"
}
```

### Get Default Views

```
GET /api/core/saved-views/defaults/
```

Returns all default views for the current company.

## Usage in Entity Endpoints

To apply a saved view to an entity list:

1. **Retrieve the view** using the saved views API
2. **Extract filters and sort** from the definition
3. **Apply to queryset** using the entity's list endpoint

**Example:**

```python
# In your view
view = SavedListView.objects.get(id=view_id)
queryset = Deal.objects.filter(company=company)

# Apply filters
queryset = view.apply_filters(queryset)

# Apply sorting
queryset = view.apply_sorting(queryset)

# Get columns
columns = view.get_columns()
```

## Examples

### Example 1: Active Contacts View

```json
{
  "name": "Active Contacts",
  "entity_type": "contact",
  "definition": {
    "filters": [
      {
        "field": "is_active",
        "operator": "equals",
        "value": true
      },
      {
        "field": "email",
        "operator": "is_not_null",
        "value": true
      }
    ],
    "columns": ["first_name", "last_name", "email", "title", "account"],
    "sort": [
      {
        "field": "last_name",
        "direction": "asc"
      }
    ]
  },
  "is_private": false
}
```

### Example 2: Hot Leads View

```json
{
  "name": "Hot Leads",
  "entity_type": "lead",
  "definition": {
    "filters": [
      {
        "field": "status",
        "operator": "equals",
        "value": "qualified"
      },
      {
        "field": "score",
        "operator": "gte",
        "value": 80
      }
    ],
    "columns": ["name", "company", "email", "score", "source"],
    "sort": [
      {
        "field": "score",
        "direction": "desc"
      }
    ]
  },
  "is_private": true
}
```

## Best Practices

1. **Descriptive Names**: Use clear, descriptive names for views
2. **Default Views**: Set one default view per entity type for common use
3. **Private vs Global**: Use private views for personal preferences, global views for team standards
4. **Filter Complexity**: Keep filters simple for better performance
5. **Column Selection**: Only include necessary columns to improve load times
6. **Regular Review**: Periodically review and clean up unused views

## Limitations

- Maximum 100 filters per view
- Maximum 50 columns per view
- Maximum 10 sort fields per view
- View names must be unique within entity type and owner scope

## Future Enhancements

- View sharing with specific users/teams
- View templates for common patterns
- View scheduling for automated reports
- View performance metrics
- Conditional formatting rules
- Aggregate calculations in views
