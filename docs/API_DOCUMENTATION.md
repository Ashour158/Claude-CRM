# 📚 CRM System API Documentation

## 🎯 Overview

This document provides comprehensive API documentation for the CRM system. The API follows RESTful principles and provides endpoints for all CRM functionality including accounts, contacts, leads, deals, activities, products, territories, and more.

## 🔐 Authentication

### JWT Token Authentication

The API uses JWT (JSON Web Token) for authentication. Include the token in the Authorization header:

```http
Authorization: Bearer <your-jwt-token>
```

### Token Endpoints

#### Login
```http
POST /api/auth/login/
```

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "password123"
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": 1,
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe"
    }
}
```

#### Refresh Token
```http
POST /api/auth/refresh/
```

**Request Body:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Register
```http
POST /api/auth/register/
```

**Request Body:**
```json
{
    "email": "newuser@example.com",
    "first_name": "Jane",
    "last_name": "Smith",
    "password": "password123",
    "password2": "password123",
    "company_name": "New Company"
}
```

## 🏢 Core Endpoints

### Health Check
```http
GET /api/core/health/
```

**Response:**
```json
{
    "status": "healthy",
    "timestamp": "2024-01-01T00:00:00Z",
    "version": "1.0.0"
}
```

### User Profile
```http
GET /api/core/profile/
```

**Response:**
```json
{
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "companies": [
        {
            "id": 1,
            "name": "Company Name",
            "role": "admin"
        }
    ]
}
```

### Company Management
```http
GET /api/core/companies/
POST /api/core/companies/
GET /api/core/companies/{id}/
PUT /api/core/companies/{id}/
DELETE /api/core/companies/{id}/
```

## 👥 CRM Endpoints

### Accounts

#### List Accounts
```http
GET /api/crm/accounts/
```

**Query Parameters:**
- `search`: Search by name, email, or phone
- `account_type`: Filter by account type
- `industry`: Filter by industry
- `territory`: Filter by territory
- `page`: Page number
- `page_size`: Number of results per page

**Response:**
```json
{
    "count": 100,
    "next": "http://api.example.com/api/crm/accounts/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Acme Corporation",
            "account_type": "Customer",
            "industry": "Technology",
            "phone": "+1-555-123-4567",
            "email": "info@acme.com",
            "website": "https://acme.com",
            "territory": {
                "id": 1,
                "name": "North Territory"
            },
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

#### Create Account
```http
POST /api/crm/accounts/
```

**Request Body:**
```json
{
    "name": "New Company",
    "account_type": "Prospect",
    "industry": "Healthcare",
    "phone": "+1-555-987-6543",
    "email": "info@newcompany.com",
    "website": "https://newcompany.com",
    "territory": 1,
    "custom_fields": {
        "annual_revenue": 1000000,
        "employee_count": 50
    }
}
```

#### Update Account
```http
PUT /api/crm/accounts/{id}/
PATCH /api/crm/accounts/{id}/
```

#### Delete Account
```http
DELETE /api/crm/accounts/{id}/
```

### Contacts

#### List Contacts
```http
GET /api/crm/contacts/
```

**Query Parameters:**
- `search`: Search by name, email, or phone
- `account`: Filter by account ID
- `title`: Filter by job title
- `page`: Page number
- `page_size`: Number of results per page

**Response:**
```json
{
    "count": 50,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@acme.com",
            "phone": "+1-555-123-4567",
            "title": "CEO",
            "account": {
                "id": 1,
                "name": "Acme Corporation"
            },
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

#### Create Contact
```http
POST /api/crm/contacts/
```

**Request Body:**
```json
{
    "first_name": "Jane",
    "last_name": "Smith",
    "email": "jane.smith@newcompany.com",
    "phone": "+1-555-987-6543",
    "title": "CTO",
    "account": 1,
    "custom_fields": {
        "department": "Engineering",
        "reports_to": "John Doe"
    }
}
```

### Leads

#### List Leads
```http
GET /api/crm/leads/
```

**Query Parameters:**
- `search`: Search by name, email, or company
- `lead_source`: Filter by lead source
- `status`: Filter by lead status
- `territory`: Filter by territory
- `page`: Page number
- `page_size`: Number of results per page

**Response:**
```json
{
    "count": 25,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "first_name": "Lead",
            "last_name": "Prospect",
            "email": "lead@prospect.com",
            "phone": "+1-555-111-2222",
            "company_name": "Prospect Company",
            "lead_source": "Website",
            "status": "New",
            "territory": {
                "id": 1,
                "name": "North Territory"
            },
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

#### Convert Lead
```http
POST /api/crm/leads/{id}/convert/
```

**Request Body:**
```json
{
    "account_id": 1,
    "contact_id": 1,
    "deal_id": 1
}
```

## 💼 Sales Endpoints

### Deals

#### List Deals
```http
GET /api/deals/deals/
```

**Query Parameters:**
- `search`: Search by deal name
- `stage`: Filter by pipeline stage
- `status`: Filter by deal status
- `account`: Filter by account ID
- `owner`: Filter by owner ID
- `page`: Page number
- `page_size`: Number of results per page

**Response:**
```json
{
    "count": 30,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Software License Deal",
            "account": {
                "id": 1,
                "name": "Acme Corporation"
            },
            "contact": {
                "id": 1,
                "name": "John Doe"
            },
            "amount": 50000.00,
            "stage": {
                "id": 1,
                "name": "Proposal"
            },
            "expected_close_date": "2024-03-01",
            "close_date": null,
            "status": "Open",
            "probability": 75,
            "owner": {
                "id": 1,
                "name": "Sales Rep"
            },
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

#### Create Deal
```http
POST /api/deals/deals/
```

**Request Body:**
```json
{
    "name": "New Deal",
    "account": 1,
    "contact": 1,
    "amount": 25000.00,
    "stage": 1,
    "expected_close_date": "2024-04-01",
    "probability": 50,
    "description": "Deal description"
}
```

#### Change Deal Stage
```http
POST /api/deals/deals/{id}/change-stage/
```

**Request Body:**
```json
{
    "stage": 2,
    "notes": "Stage change notes"
}
```

#### Mark Deal Won
```http
POST /api/deals/deals/{id}/mark-won/
```

**Request Body:**
```json
{
    "close_date": "2024-01-15",
    "notes": "Deal won notes"
}
```

#### Mark Deal Lost
```http
POST /api/deals/deals/{id}/mark-lost/
```

**Request Body:**
```json
{
    "close_date": "2024-01-15",
    "notes": "Deal lost notes"
}
```

### Pipeline Stages

#### List Pipeline Stages
```http
GET /api/deals/pipeline-stages/
```

**Response:**
```json
{
    "count": 6,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Lead",
            "description": "Initial lead stage",
            "order": 0,
            "is_active": true,
            "created_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

## 📋 Activities Endpoints

### Activities

#### List Activities
```http
GET /api/activities/activities/
```

**Query Parameters:**
- `search`: Search by subject or description
- `activity_type`: Filter by activity type
- `status`: Filter by activity status
- `owner`: Filter by owner ID
- `account`: Filter by account ID
- `contact`: Filter by contact ID
- `lead`: Filter by lead ID
- `deal`: Filter by deal ID
- `page`: Page number
- `page_size`: Number of results per page

**Response:**
```json
{
    "count": 40,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "subject": "Client Meeting",
            "activity_type": "Meeting",
            "description": "Meeting with client to discuss requirements",
            "due_date": "2024-01-15T10:00:00Z",
            "status": "Completed",
            "owner": {
                "id": 1,
                "name": "Sales Rep"
            },
            "account": {
                "id": 1,
                "name": "Acme Corporation"
            },
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

#### Create Activity
```http
POST /api/activities/activities/
```

**Request Body:**
```json
{
    "subject": "Follow-up Call",
    "activity_type": "Call",
    "description": "Follow up with client about proposal",
    "due_date": "2024-01-20T14:00:00Z",
    "status": "Not Started",
    "owner": 1,
    "account": 1,
    "contact": 1
}
```

### Tasks

#### List Tasks
```http
GET /api/activities/tasks/
```

**Query Parameters:**
- `search`: Search by title or description
- `status`: Filter by task status
- `priority`: Filter by priority level
- `owner`: Filter by owner ID
- `page`: Page number
- `page_size`: Number of results per page

**Response:**
```json
{
    "count": 20,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "title": "Prepare Proposal",
            "description": "Prepare proposal for client",
            "due_date": "2024-01-18T17:00:00Z",
            "status": "In Progress",
            "priority": "High",
            "owner": {
                "id": 1,
                "name": "Sales Rep"
            },
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

#### Create Task
```http
POST /api/activities/tasks/
```

**Request Body:**
```json
{
    "title": "Update CRM",
    "description": "Update CRM with latest client information",
    "due_date": "2024-01-25T12:00:00Z",
    "status": "Not Started",
    "priority": "Medium",
    "owner": 1
}
```

#### Complete Task
```http
POST /api/activities/tasks/{id}/complete/
```

**Request Body:**
```json
{
    "notes": "Task completed successfully"
}
```

### Events

#### List Events
```http
GET /api/activities/events/
```

**Query Parameters:**
- `search`: Search by title or description
- `start_date`: Filter by start date
- `end_date`: Filter by end date
- `owner`: Filter by owner ID
- `page`: Page number
- `page_size`: Number of results per page

**Response:**
```json
{
    "count": 15,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "title": "Product Demo",
            "description": "Product demonstration for client",
            "start_date": "2024-01-20T10:00:00Z",
            "end_date": "2024-01-20T11:00:00Z",
            "location": "Client Office",
            "owner": {
                "id": 1,
                "name": "Sales Rep"
            },
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

#### Create Event
```http
POST /api/activities/events/
```

**Request Body:**
```json
{
    "title": "Team Meeting",
    "description": "Weekly team meeting",
    "start_date": "2024-01-22T09:00:00Z",
    "end_date": "2024-01-22T10:00:00Z",
    "location": "Conference Room A",
    "owner": 1
}
```

## 🛍️ Products Endpoints

### Products

#### List Products
```http
GET /api/products/products/
```

**Query Parameters:**
- `search`: Search by name, description, or SKU
- `category`: Filter by product category
- `is_active`: Filter by active status
- `page`: Page number
- `page_size`: Number of results per page

**Response:**
```json
{
    "count": 50,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "CRM Software",
            "description": "Customer relationship management software",
            "sku": "CRM-001",
            "unit_price": 99.99,
            "category": {
                "id": 1,
                "name": "Software"
            },
            "is_active": true,
            "owner": {
                "id": 1,
                "name": "Product Manager"
            },
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

#### Create Product
```http
POST /api/products/products/
```

**Request Body:**
```json
{
    "name": "New Product",
    "description": "Product description",
    "sku": "PROD-001",
    "unit_price": 199.99,
    "category": 1,
    "is_active": true,
    "custom_fields": {
        "weight": "1.5kg",
        "dimensions": "10x10x5cm"
    }
}
```

### Product Categories

#### List Product Categories
```http
GET /api/products/categories/
```

**Response:**
```json
{
    "count": 4,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Software",
            "description": "Software products and services",
            "parent_category": null,
            "is_active": true,
            "created_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

## 🗺️ Territories Endpoints

### Territories

#### List Territories
```http
GET /api/territories/territories/
```

**Query Parameters:**
- `search`: Search by name or description
- `is_active`: Filter by active status
- `page`: Page number
- `page_size`: Number of results per page

**Response:**
```json
{
    "count": 5,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "North Territory",
            "description": "North sales territory",
            "is_active": true,
            "created_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

#### Create Territory
```http
POST /api/territories/territories/
```

**Request Body:**
```json
{
    "name": "New Territory",
    "description": "New sales territory",
    "is_active": true
}
```

#### Assign Accounts to Territory
```http
POST /api/territories/territories/{id}/assign-accounts/
```

**Request Body:**
```json
{
    "account_ids": [1, 2, 3]
}
```

## 📊 Analytics Endpoints

### Dashboard Data
```http
GET /api/analytics/dashboard/
```

**Response:**
```json
{
    "total_accounts": 100,
    "total_contacts": 250,
    "total_leads": 75,
    "total_deals": 30,
    "total_revenue": 500000.00,
    "deals_by_stage": [
        {
            "stage": "Lead",
            "count": 10
        },
        {
            "stage": "Proposal",
            "count": 15
        }
    ],
    "revenue_by_month": [
        {
            "month": "2024-01",
            "revenue": 100000.00
        }
    ]
}
```

### Reports
```http
GET /api/analytics/reports/
```

**Query Parameters:**
- `report_type`: Type of report
- `start_date`: Report start date
- `end_date`: Report end date
- `format`: Report format (json, csv, pdf)

## 🔧 System Configuration Endpoints

### System Settings
```http
GET /api/system-config/settings/
POST /api/system-config/settings/
GET /api/system-config/settings/{id}/
PUT /api/system-config/settings/{id}/
DELETE /api/system-config/settings/{id}/
```

### User Management
```http
GET /api/system-config/users/
POST /api/system-config/users/
GET /api/system-config/users/{id}/
PUT /api/system-config/users/{id}/
DELETE /api/system-config/users/{id}/
```

## 🔌 Integration Endpoints

### Integrations
```http
GET /api/integrations/integrations/
POST /api/integrations/integrations/
GET /api/integrations/integrations/{id}/
PUT /api/integrations/integrations/{id}/
DELETE /api/integrations/integrations/{id}/
```

### Webhooks
```http
GET /api/integrations/webhooks/
POST /api/integrations/webhooks/
GET /api/integrations/webhooks/{id}/
PUT /api/integrations/webhooks/{id}/
DELETE /api/integrations/webhooks/{id}/
```

## 📝 Error Handling

### Error Response Format
```json
{
    "error": {
        "type": "ValidationError",
        "message": "Validation failed",
        "timestamp": "2024-01-01T00:00:00Z",
        "status_code": 400,
        "details": {
            "field_name": ["This field is required."]
        }
    }
}
```

### Common Error Codes
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Permission denied
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

## 🔍 Filtering and Search

### Global Search
Most list endpoints support a `search` parameter that searches across relevant fields:

```http
GET /api/crm/accounts/?search=acme
```

### Field Filtering
Filter by specific fields:

```http
GET /api/crm/accounts/?account_type=Customer&industry=Technology
```

### Date Filtering
Filter by date ranges:

```http
GET /api/crm/accounts/?created_after=2024-01-01&created_before=2024-12-31
```

### Ordering
Order results by specific fields:

```http
GET /api/crm/accounts/?ordering=name
GET /api/crm/accounts/?ordering=-created_at
```

## 📄 Pagination

All list endpoints support pagination:

```http
GET /api/crm/accounts/?page=2&page_size=20
```

**Response:**
```json
{
    "count": 100,
    "next": "http://api.example.com/api/crm/accounts/?page=3",
    "previous": "http://api.example.com/api/crm/accounts/?page=1",
    "results": [...]
}
```

## 🔐 Rate Limiting

The API implements rate limiting to prevent abuse:

- **Authenticated users**: 1000 requests per hour
- **Unauthenticated users**: 100 requests per hour
- **Admin endpoints**: 500 requests per hour

Rate limit headers are included in responses:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## 📚 SDKs and Examples

### Python Example
```python
import requests

# Authentication
response = requests.post('https://api.example.com/api/auth/login/', {
    'email': 'user@example.com',
    'password': 'password123'
})
token = response.json()['access']

# API calls
headers = {'Authorization': f'Bearer {token}'}
response = requests.get('https://api.example.com/api/crm/accounts/', headers=headers)
accounts = response.json()
```

### JavaScript Example
```javascript
// Authentication
const response = await fetch('https://api.example.com/api/auth/login/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        email: 'user@example.com',
        password: 'password123'
    })
});
const { access } = await response.json();

// API calls
const accountsResponse = await fetch('https://api.example.com/api/crm/accounts/', {
    headers: {
        'Authorization': `Bearer ${access}`
    }
});
const accounts = await accountsResponse.json();
```

## 🚀 Getting Started

1. **Register**: Create an account using the register endpoint
2. **Login**: Authenticate to get your JWT token
3. **Explore**: Use the API endpoints to manage your CRM data
4. **Integrate**: Build applications using the comprehensive API

## 📞 Support

For API support and questions:
- **Documentation**: [API Documentation](https://docs.example.com)
- **Support**: [support@example.com](mailto:support@example.com)
- **Status**: [API Status](https://status.example.com)

---

*Last updated: January 2024*
*API Version: 1.0.0*
