# Architecture Index

## Overview
This document serves as a central index to all architectural documentation for the Claude CRM system.

## Core Architecture Documents

### 1. [Domain Migration Status](./DOMAIN_MIGRATION_STATUS.md)
**Purpose**: Tracks the migration from monolithic structure to domain-driven design  
**Topics**:
- New package structure (crm.accounts, crm.leads, etc.)
- Migration status and next steps
- Compatibility notes

### 2. [Custom Fields Design](./CUSTOM_FIELDS_DESIGN.md)
**Purpose**: Documents the flexible custom field system  
**Topics**:
- JSON-based storage strategy
- Field types and validation
- Usage examples and best practices

### 3. [Permissions Matrix](./PERMISSIONS_MATRIX.md)
**Purpose**: Complete guide to role-based access control  
**Topics**:
- Default roles (Admin, Sales Manager, Sales Rep, Viewer)
- Permission matrix by resource and action
- Role inheritance and conditions

### 4. [Activities Timeline](./ACTIVITIES_TIMELINE.md)
**Purpose**: Event tracking and timeline system  
**Topics**:
- TimelineEvent model
- Automatic and manual event recording
- Timeline display and querying

### 5. [Lead Conversion Flow](./LEAD_CONVERSION_FLOW.md)
**Purpose**: Lead to Account/Contact/Deal conversion process  
**Topics**:
- Conversion workflow
- Data mapping
- Idempotency and error handling

## API Documentation

### 6. [API Documentation](./API_DOCUMENTATION.md)
**Purpose**: RESTful API reference  
**Endpoints**:
- Accounts, Contacts, Leads, Deals
- Activities and Timeline
- Reports and Analytics

### 7. [API Reference](./API_REFERENCE.md)
**Purpose**: Detailed API specifications  
**Topics**:
- Authentication
- Request/Response formats
- Error codes

## Frontend Documentation

### 8. [Frontend Gap Analysis](./FRONTEND_GAP_ANALYSIS.md)
**Purpose**: Analysis of frontend vs Zoho CRM  
**Topics**:
- Feature comparison
- Missing features
- Implementation priorities

### 9. [UX Remediation Plan](./UX_REMEDIATION_PLAN.md)
**Purpose**: Plan to improve user experience  
**Topics**:
- UI/UX issues
- Enhancement roadmap
- Design system

## System Architecture

### Multi-Tenancy
- **Strategy**: Organization-level isolation
- **Implementation**: TenantOwnedModel mixin with organization FK
- **Enforcement**: TenantQuerySet and TenantManager
- **Documents**: [Domain Migration Status](./DOMAIN_MIGRATION_STATUS.md)

### Service Layer Pattern
- **Purpose**: Separate business logic from views
- **Structure**: Services (write) + Selectors (read)
- **Benefits**: Testability, reusability, maintainability
- **Location**: `crm/*/services/` and `crm/*/selectors/`

### Permission System
- **Type**: Role-Based Access Control (RBAC)
- **Granularity**: Resource + Action
- **Features**: Inheritance, conditions, ownership
- **Documents**: [Permissions Matrix](./PERMISSIONS_MATRIX.md)

### Data Storage
- **Primary**: PostgreSQL
- **Cache**: Redis
- **Files**: S3 or local storage
- **Custom Fields**: JSON in entity tables

## Design Patterns

### 1. Repository Pattern
Used via Selectors for data retrieval:
```python
AccountSelector.get_account(account_id, organization)
AccountSelector.list_accounts(organization, filters)
```

### 2. Service Pattern
Used for business logic:
```python
AccountService.create_account(organization, data, user)
ConversionService.convert_lead(lead, user)
```

### 3. Generic Relations
For timeline events:
```python
TimelineEvent.target  # Points to any model
```

### 4. Mixins
For cross-cutting concerns:
```python
TenantOwnedModel  # Adds organization, audit fields
```

## Code Organization

```
claude-crm/
├── config/              # Django settings
├── core/                # Core auth and tenancy
├── crm/                 # New domain structure
│   ├── core/
│   │   └── tenancy/    # Tenancy mixins/managers
│   ├── accounts/       # Account domain
│   ├── contacts/       # Contact domain
│   ├── leads/          # Lead domain
│   ├── activities/     # Activities domain
│   ├── system/         # System config
│   ├── permissions/    # Permission evaluator
│   └── api/            # API endpoints
├── deals/               # Legacy deals app
├── territories/         # Territory management
├── activities/          # Legacy activities
├── products/            # Product catalog
├── sales/               # Sales management
├── vendors/             # Vendor management
├── marketing/           # Marketing campaigns
├── analytics/           # Analytics and reporting
├── system_config/       # Legacy system config
├── integrations/        # External integrations
├── tests/               # Test suite
├── docs/                # Documentation
└── frontend/            # React frontend
```

## Database Schema

### Core Tables
- `core_user` - Users
- `core_company` - Organizations/Companies
- `core_user_company_access` - User-Company relationships

### CRM Tables (New)
- `crm_account` - Accounts
- `crm_contact` - Contacts
- `crm_lead` - Leads
- `crm_timeline_event` - Timeline events
- `crm_custom_field_definition` - Custom field definitions
- `crm_role` - Roles
- `crm_role_permission` - Role permissions

### Legacy Tables
- `crm_account` (old) - Legacy accounts
- `crm_contact` (old) - Legacy contacts
- `crm_lead` (old) - Legacy leads

## Technology Stack

### Backend
- **Framework**: Django 4.2
- **API**: Django REST Framework
- **Database**: PostgreSQL 14+
- **Cache**: Redis
- **Task Queue**: Celery
- **Search**: PostgreSQL Full-Text

### Frontend
- **Framework**: React 18
- **State**: Redux Toolkit
- **UI**: Material-UI
- **Charts**: Recharts
- **Forms**: Formik + Yup

### Infrastructure
- **Deployment**: Docker + Docker Compose
- **Web Server**: Nginx
- **App Server**: Gunicorn
- **Monitoring**: Prometheus + Grafana
- **Logging**: ELK Stack

## Key Principles

### 1. Domain-Driven Design
Organize code by business domain, not technical layers.

### 2. Separation of Concerns
- Models: Data structure
- Services: Business logic
- Selectors: Data retrieval
- Views: HTTP handling
- Serializers: Data transformation

### 3. Test-Driven Development
Write tests first, then implementation.

### 4. API-First Design
Backend provides RESTful API, frontend consumes it.

### 5. Security by Default
- Authentication required
- Authorization checked
- Input validated
- Output sanitized

## Development Workflow

1. **Planning**: Document requirements and design
2. **Modeling**: Define data models
3. **Services**: Implement business logic
4. **Testing**: Write comprehensive tests
5. **API**: Create API endpoints
6. **Frontend**: Build UI components
7. **Integration**: Connect all pieces
8. **Review**: Code review and testing
9. **Deploy**: Release to production

## Testing Strategy

### Unit Tests
Test individual functions and methods in isolation.

### Integration Tests
Test interaction between components.

### API Tests
Test API endpoints end-to-end.

### E2E Tests
Test complete user workflows in browser.

## Deployment

### Environments
- **Development**: Local development
- **Staging**: Testing environment
- **Production**: Live system

### CI/CD Pipeline
1. Push code to GitHub
2. Run tests automatically
3. Build Docker images
4. Deploy to staging
5. Run smoke tests
6. Deploy to production

## Performance Optimization

### Database
- Indexes on frequently queried fields
- Query optimization with select_related/prefetch_related
- Connection pooling
- Read replicas for reporting

### Caching
- Redis for session and data caching
- Cache frequently accessed data
- Cache invalidation strategy

### API
- Pagination for list endpoints
- Field selection (sparse fieldsets)
- Rate limiting
- Response compression

## Security

### Authentication
- JWT tokens
- Session management
- Password requirements
- 2FA support

### Authorization
- Role-based access control
- Row-level security
- Permission checks on all endpoints

### Data Protection
- Encryption at rest
- Encryption in transit (HTTPS)
- Input validation
- SQL injection prevention
- XSS prevention

## Monitoring & Logging

### Metrics
- Request rate
- Response time
- Error rate
- Database performance

### Logs
- Application logs
- Access logs
- Error logs
- Audit logs

### Alerts
- Error rate threshold
- Performance degradation
- Security events
- System health

## Related Resources

- [GitHub Repository](https://github.com/Ashour158/Claude-CRM)
- [Issue Tracker](https://github.com/Ashour158/Claude-CRM/issues)
- [Wiki](https://github.com/Ashour158/Claude-CRM/wiki)
- [Changelog](../CHANGELOG.md)

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on contributing to the project.

## License

See [LICENSE](../LICENSE) for license information.
