# 📚 CRM System API Reference

## 🔗 Base URL
```
https://your-domain.com/api/
```

## 🔐 Authentication

All API requests require JWT authentication. Include the access token in the Authorization header:

```http
Authorization: Bearer <access_token>
```

### Authentication Endpoints

#### Register User
```http
POST /api/core/register/
```

**Request Body:**
```json
{
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "password": "securepassword",
    "password2": "securepassword",
    "company_name": "My Company"
}
```

**Response:**
```json
{
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "date_joined": "2024-01-01T00:00:00Z"
}
```

#### Login
```http
POST /api/core/login/
```

**Request Body:**
```json
{
    "email": "user@example.com",
    "password": "securepassword"
}
```

**Response:**
```json
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
    "user": {
        "id": "uuid",
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe"
    },
    "company": {
        "id": "uuid",
        "name": "My Company",
        "role": "admin"
    }
}
```

#### Refresh Token
```http
POST /api/core/token/refresh/
```

**Request Body:**
```json
{
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### User Profile
```http
GET /api/core/profile/
```

**Response:**
```json
{
    "id": "uuid",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "is_active": true,
    "date_joined": "2024-01-01T00:00:00Z"
}
```

## 🏢 CRM Endpoints

### Accounts

#### List Accounts
```http
GET /api/crm/accounts/
```

**Query Parameters:**
- `page` (int): Page number (default: 1)
- `page_size` (int): Items per page (default: 20, max: 100)
- `search` (string): Search query
- `type` (string): Account type filter
- `industry` (string): Industry filter
- `owner` (uuid): Owner filter
- `is_active` (boolean): Active status filter
- `ordering` (string): Sort order (e.g., `name`, `-created_at`)

**Response:**
```json
{
    "count": 100,
    "next": "https://api/accounts/?page=2",
    "previous": null,
    "results": [
        {
            "id": "uuid",
            "name": "Acme Corporation",
            "type": "customer",
            "industry": "Technology",
            "email": "info@acme.com",
            "phone": "+1-555-0123",
            "website": "https://acme.com",
            "annual_revenue": 1000000.00,
            "employee_count": 50,
            "owner": {
                "id": "uuid",
                "first_name": "John",
                "last_name": "Doe"
            },
            "territory": {
                "id": "uuid",
                "name": "North America"
            },
            "is_active": true,
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
    "type": "customer",
    "industry": "Technology",
    "email": "info@newcompany.com",
    "phone": "+1-555-0123",
    "website": "https://newcompany.com",
    "annual_revenue": 500000.00,
    "employee_count": 25,
    "billing_address_line1": "123 Main St",
    "billing_city": "New York",
    "billing_state": "NY",
    "billing_postal_code": "10001",
    "billing_country": "US"
}
```

#### Get Account
```http
GET /api/crm/accounts/{id}/
```

#### Update Account
```http
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
- `page` (int): Page number
- `page_size` (int): Items per page
- `search` (string): Search query
- `account` (uuid): Account filter
- `owner` (uuid): Owner filter
- `is_active` (boolean): Active status filter
- `ordering` (string): Sort order

**Response:**
```json
{
    "count": 50,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": "uuid",
            "first_name": "Jane",
            "last_name": "Smith",
            "full_name": "Jane Smith",
            "title": "CEO",
            "email": "jane@acme.com",
            "phone": "+1-555-0124",
            "mobile": "+1-555-0125",
            "account": {
                "id": "uuid",
                "name": "Acme Corporation"
            },
            "owner": {
                "id": "uuid",
                "first_name": "John",
                "last_name": "Doe"
            },
            "is_active": true,
            "is_primary": true,
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
    "first_name": "John",
    "last_name": "Doe",
    "title": "Manager",
    "email": "john@example.com",
    "phone": "+1-555-0123",
    "account": "account-uuid",
    "is_primary": true
}
```

### Leads

#### List Leads
```http
GET /api/crm/leads/
```

**Query Parameters:**
- `page` (int): Page number
- `page_size` (int): Items per page
- `search` (string): Search query
- `status` (string): Status filter
- `rating` (string): Rating filter
- `source` (string): Source filter
- `owner` (uuid): Owner filter
- `is_active` (boolean): Active status filter
- `ordering` (string): Sort order

**Response:**
```json
{
    "count": 25,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": "uuid",
            "first_name": "Lead",
            "last_name": "Person",
            "full_name": "Lead Person",
            "company_name": "Lead Company",
            "email": "lead@example.com",
            "phone": "+1-555-0123",
            "source": "website",
            "status": "new",
            "rating": "hot",
            "lead_score": 85,
            "industry": "Technology",
            "owner": {
                "id": "uuid",
                "first_name": "John",
                "last_name": "Doe"
            },
            "is_active": true,
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
    "create_deal": true,
    "deal_amount": 10000.00
}
```

**Response:**
```json
{
    "account": {
        "id": "uuid",
        "name": "Lead Company"
    },
    "contact": {
        "id": "uuid",
        "first_name": "Lead",
        "last_name": "Person"
    },
    "deal": {
        "id": "uuid",
        "name": "Deal with Lead Company",
        "amount": 10000.00
    }
}
```

## 📊 Activities

### List Activities
```http
GET /api/activities/activities/
```

**Query Parameters:**
- `page` (int): Page number
- `page_size` (int): Items per page
- `activity_type` (string): Activity type filter
- `status` (string): Status filter
- `priority` (string): Priority filter
- `assigned_to` (uuid): Assigned user filter
- `date_from` (date): Start date filter
- `date_to` (date): End date filter
- `ordering` (string): Sort order

**Response:**
```json
{
    "count": 100,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": "uuid",
            "activity_type": "call",
            "subject": "Follow-up call",
            "description": "Follow-up on proposal",
            "activity_date": "2024-01-15T14:00:00Z",
            "duration_minutes": 30,
            "status": "completed",
            "priority": "high",
            "assigned_to": {
                "id": "uuid",
                "first_name": "John",
                "last_name": "Doe"
            },
            "outcome": "Positive response",
            "next_action": "Send proposal",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

### Create Activity
```http
POST /api/activities/activities/
```

**Request Body:**
```json
{
    "activity_type": "meeting",
    "subject": "Product Demo",
    "description": "Demo of our CRM system",
    "activity_date": "2024-01-15T14:00:00Z",
    "duration_minutes": 60,
    "priority": "high",
    "location": "Conference Room A",
    "is_online": false
}
```

## 💼 Deals

### List Deals
```http
GET /api/deals/deals/
```

**Query Parameters:**
- `page` (int): Page number
- `page_size` (int): Items per page
- `search` (string): Search query
- `stage` (string): Stage filter
- `status` (string): Status filter
- `owner` (uuid): Owner filter
- `account` (uuid): Account filter
- `contact` (uuid): Contact filter
- `amount_min` (decimal): Minimum amount filter
- `amount_max` (decimal): Maximum amount filter
- `close_date_from` (date): Close date from filter
- `close_date_to` (date): Close date to filter
- `ordering` (string): Sort order

**Response:**
```json
{
    "count": 50,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": "uuid",
            "name": "Enterprise Software License",
            "account": {
                "id": "uuid",
                "name": "Acme Corporation"
            },
            "contact": {
                "id": "uuid",
                "first_name": "Jane",
                "last_name": "Smith"
            },
            "amount": 50000.00,
            "stage": "proposal",
            "status": "open",
            "probability": 75,
            "expected_close_date": "2024-03-01",
            "owner": {
                "id": "uuid",
                "first_name": "John",
                "last_name": "Doe"
            },
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

### Deal Pipeline
```http
GET /api/deals/deals/pipeline/
```

**Response:**
```json
{
    "stages": [
        {
            "name": "Prospecting",
            "deals": [
                {
                    "id": "uuid",
                    "name": "Deal 1",
                    "amount": 10000.00,
                    "probability": 25
                }
            ],
            "total_amount": 10000.00,
            "weighted_amount": 2500.00
        },
        {
            "name": "Qualification",
            "deals": [
                {
                    "id": "uuid",
                    "name": "Deal 2",
                    "amount": 20000.00,
                    "probability": 50
                }
            ],
            "total_amount": 20000.00,
            "weighted_amount": 10000.00
        }
    ],
    "summary": {
        "total_deals": 2,
        "total_amount": 30000.00,
        "weighted_amount": 12500.00
    }
}
```

## 📦 Products

### List Products
```http
GET /api/products/products/
```

**Query Parameters:**
- `page` (int): Page number
- `page_size` (int): Items per page
- `search` (string): Search query
- `category` (uuid): Category filter
- `is_active` (boolean): Active status filter
- `ordering` (string): Sort order

**Response:**
```json
{
    "count": 25,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": "uuid",
            "name": "CRM Software",
            "sku": "CRM-001",
            "description": "Customer relationship management software",
            "unit_price": 1000.00,
            "category": {
                "id": "uuid",
                "name": "Software"
            },
            "is_active": true,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    ]
}
```

## 📊 Analytics

### Dashboard Data
```http
GET /api/analytics/dashboards/
```

**Response:**
```json
{
    "kpis": {
        "total_accounts": 100,
        "total_contacts": 500,
        "total_leads": 200,
        "total_deals": 50,
        "total_revenue": 1000000.00
    },
    "charts": {
        "deals_by_stage": [
            {"stage": "Prospecting", "count": 10, "amount": 100000.00},
            {"stage": "Qualification", "count": 15, "amount": 200000.00},
            {"stage": "Proposal", "count": 20, "amount": 300000.00}
        ],
        "revenue_by_month": [
            {"month": "2024-01", "revenue": 100000.00},
            {"month": "2024-02", "revenue": 150000.00},
            {"month": "2024-03", "revenue": 200000.00}
        ]
    }
}
```

## 🔍 Search

### Global Search
```http
GET /api/search/?q={query}&entity_type={type}
```

**Query Parameters:**
- `q` (string): Search query
- `entity_type` (string): Entity type filter (accounts, contacts, leads, deals)
- `page` (int): Page number
- `page_size` (int): Items per page

**Response:**
```json
{
    "query": "acme",
    "results": {
        "accounts": [
            {
                "id": "uuid",
                "name": "Acme Corporation",
                "type": "customer"
            }
        ],
        "contacts": [
            {
                "id": "uuid",
                "first_name": "John",
                "last_name": "Acme",
                "email": "john@acme.com"
            }
        ]
    },
    "total_results": 2
}
```

## 📁 File Upload

### Upload File
```http
POST /api/files/upload/
```

**Request Body:**
```
Content-Type: multipart/form-data

file: [binary file data]
```

**Response:**
```json
{
    "id": "uuid",
    "filename": "document.pdf",
    "file_size": 1024000,
    "content_type": "application/pdf",
    "url": "https://api/files/uuid/",
    "created_at": "2024-01-01T00:00:00Z"
}
```

## 📋 Error Responses

### Validation Error (400)
```json
{
    "error": "Validation failed",
    "details": {
        "name": ["This field is required."],
        "email": ["Enter a valid email address."]
    }
}
```

### Authentication Error (401)
```json
{
    "error": "Authentication failed",
    "details": "Invalid credentials or token"
}
```

### Permission Error (403)
```json
{
    "error": "Permission denied",
    "details": "Insufficient permissions for this action"
}
```

### Not Found Error (404)
```json
{
    "error": "Resource not found",
    "details": "The requested resource does not exist"
}
```

### Rate Limit Error (429)
```json
{
    "error": "Rate limit exceeded",
    "details": "Too many requests. Please try again later.",
    "retry_after": 60
}
```

### Server Error (500)
```json
{
    "error": "Internal server error",
    "details": "An unexpected error occurred"
}
```

## 🔧 Rate Limiting

- **API Endpoints**: 100 requests per minute
- **Authentication**: 10 requests per minute
- **File Upload**: 20 requests per minute
- **Search**: 50 requests per minute

## 📄 Pagination

All list endpoints support pagination:

- **Default Page Size**: 20 items
- **Maximum Page Size**: 100 items
- **Page Parameter**: `?page=1&page_size=20`

## 🔍 Filtering

Most list endpoints support filtering:

- **Field Filtering**: `?field=value`
- **Date Range**: `?created_after=2024-01-01&created_before=2024-12-31`
- **Search**: `?search=query`
- **Ordering**: `?ordering=field_name` or `?ordering=-field_name`

## 📱 Response Format

All responses are in JSON format with consistent structure:

**Success Response (200, 201):**
```json
{
    "id": "uuid",
    "field1": "value1",
    "field2": "value2",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
}
```

**List Response (200):**
```json
{
    "count": 100,
    "next": "https://api/next-page/",
    "previous": null,
    "results": [
        {...},
        {...}
    ]
}
```

## 🔐 Security

- All API requests require JWT authentication
- Multi-tenant data isolation
- Rate limiting to prevent abuse
- Input validation and sanitization
- Audit logging for all actions
- HTTPS required in production

## 📞 Support

For API support and questions:
- **Documentation**: [API Docs](https://your-domain.com/api/docs/)
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Contact**: support@your-domain.com

---

**Version**: 1.0.0  
**Last Updated**: 2024-01-01  
**License**: MIT
