# CRM System

A comprehensive, multi-tenant Customer Relationship Management (CRM) system built with Django REST Framework and React.

## Features

### Core CRM Features
- **Account Management**: Complete account lifecycle management
- **Contact Management**: Individual contact tracking and management
- **Lead Management**: Lead scoring, qualification, and conversion
- **Deal Management**: Sales pipeline with customizable stages
- **Activity Tracking**: Calls, emails, meetings, notes, and tasks
- **Territory Management**: Hierarchical sales territories with assignment rules
- **Product Catalog**: Products, categories, and pricing management
- **Quote-to-Cash**: RFQs, quotes, sales orders, and invoicing
- **Vendor Management**: Supplier relationship management
- **Purchase Orders**: Complete procurement workflow

### Technical Features
- **Multi-Tenant Architecture**: Complete data isolation between companies
- **Row-Level Security**: Database-level security with PostgreSQL RLS
- **JWT Authentication**: Secure token-based authentication
- **RESTful API**: Comprehensive API with filtering, searching, and pagination
- **Real-time Updates**: WebSocket support for real-time notifications
- **Audit Logging**: Complete audit trail for compliance
- **Bulk Operations**: Efficient bulk data operations
- **CSV Import/Export**: Data migration and reporting
- **Custom Fields**: Flexible custom field system
- **Workflow Automation**: Rules engine for process automation

## Technology Stack

### Backend
- **Django 4.2**: Web framework
- **Django REST Framework**: API framework
- **PostgreSQL**: Primary database
- **Redis**: Caching and message broker
- **Celery**: Background task processing
- **JWT**: Authentication tokens

### Frontend
- **React 18**: User interface
- **TypeScript**: Type safety
- **Material-UI**: Component library
- **Redux Toolkit**: State management
- **React Query**: Data fetching and caching

### Infrastructure
- **Docker**: Containerization
- **Nginx**: Web server
- **Gunicorn**: WSGI server
- **Sentry**: Error monitoring
- **Redis**: Caching and sessions

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd crm-system
   ```

2. **Start the development environment**
   ```bash
   docker-compose up -d
   ```

3. **Run database migrations**
   ```bash
   docker-compose exec web python manage.py migrate
   ```

4. **Create a superuser**
   ```bash
   docker-compose exec web python manage.py createsuperuser
   ```

5. **Access the application**
   - API: http://localhost:8000/api/
   - Admin: http://localhost:8000/admin/
   - Frontend: http://localhost:3000

### Local Development

1. **Backend Setup**
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install dependencies
   pip install -r requirements.txt
   
   # Set environment variables
   export DEBUG=True
   export DB_HOST=localhost
   export DB_NAME=crm_db
   export DB_USER=crm_user
   export DB_PASSWORD=crm_password
   
   # Run migrations
   python manage.py migrate
   
   # Start development server
   python manage.py runserver
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm start
   ```

## API Documentation

### Authentication
All API endpoints require authentication using JWT tokens.

```bash
# Login
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'

# Use token in subsequent requests
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/crm/accounts/
```

### Core Endpoints

#### Accounts
- `GET /api/crm/accounts/` - List accounts
- `POST /api/crm/accounts/` - Create account
- `GET /api/crm/accounts/{id}/` - Get account details
- `PUT /api/crm/accounts/{id}/` - Update account
- `DELETE /api/crm/accounts/{id}/` - Delete account

#### Contacts
- `GET /api/crm/contacts/` - List contacts
- `POST /api/crm/contacts/` - Create contact
- `GET /api/crm/contacts/{id}/` - Get contact details
- `PUT /api/crm/contacts/{id}/` - Update contact
- `DELETE /api/crm/contacts/{id}/` - Delete contact

#### Leads
- `GET /api/crm/leads/` - List leads
- `POST /api/crm/leads/` - Create lead
- `GET /api/crm/leads/{id}/` - Get lead details
- `PUT /api/crm/leads/{id}/` - Update lead
- `POST /api/crm/leads/{id}/convert/` - Convert lead

#### Deals
- `GET /api/deals/deals/` - List deals
- `POST /api/deals/deals/` - Create deal
- `GET /api/deals/deals/{id}/` - Get deal details
- `PUT /api/deals/deals/{id}/` - Update deal
- `POST /api/deals/deals/{id}/win/` - Mark deal as won
- `POST /api/deals/deals/{id}/lose/` - Mark deal as lost

## Configuration

### Environment Variables

#### Database
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=crm_db
DB_USER=crm_user
DB_PASSWORD=crm_password
```

#### Redis
```bash
REDIS_URL=redis://localhost:6379/0
```

#### Email
```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-password
```

#### Security
```bash
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Multi-Tenant Configuration

The system supports multiple companies with complete data isolation:

1. **Company Creation**: Each company gets its own data space
2. **User Access**: Users can belong to multiple companies
3. **Data Isolation**: Row-level security ensures data separation
4. **Territory Management**: Sales territories can be company-specific

## Deployment

### 🚀 Quick Start - DigitalOcean Deployment

For a streamlined deployment process to DigitalOcean:

1. **Prepare deployment:**
   ```bash
   ./prepare-deployment.sh
   ```

2. **Configure environment:**
   ```bash
   # Edit .env.production with your values
   nano .env.production
   ```

3. **Validate configuration:**
   ```bash
   ./validate-deployment.sh
   ```

4. **Deploy to DigitalOcean:**
   - Follow the step-by-step guide in [DIGITALOCEAN_QUICK_START.md](DIGITALOCEAN_QUICK_START.md)

### 📚 Comprehensive Deployment Guides

- **[DIGITALOCEAN_QUICK_START.md](DIGITALOCEAN_QUICK_START.md)** - Quick 5-step deployment guide
- **[DEPLOYMENT_READINESS.md](DEPLOYMENT_READINESS.md)** - Security checklist and requirements
- **[STAGING_DEPLOYMENT_GUIDE.md](STAGING_DEPLOYMENT_GUIDE.md)** - Set up staging environment
- **[DIGITALOCEAN_DEPLOYMENT_STEP_BY_STEP.md](DIGITALOCEAN_DEPLOYMENT_STEP_BY_STEP.md)** - Detailed deployment steps
- **[SECURITY_FIXES_README.md](SECURITY_FIXES_README.md)** - Security implementation details

### 🔧 Automated Scripts

- `prepare-deployment.sh` - Generate SECRET_KEY and prepare environment
- `validate-deployment.sh` - Validate production configuration
- `deploy-do.sh` - Automated DigitalOcean deployment
- `quick-deploy-do.sh` - One-command deployment

### 🧪 Staging Environment

Before deploying to production, set up a staging environment:
- See [STAGING_DEPLOYMENT_GUIDE.md](STAGING_DEPLOYMENT_GUIDE.md)
- Test all features in staging first
- Validate security configurations
- Run integration tests

### Production Deployment Checklist

- [ ] Run `./prepare-deployment.sh`
- [ ] Configure `.env.production`
- [ ] Run `./validate-deployment.sh`
- [ ] Create DigitalOcean droplet
- [ ] Deploy application
- [ ] Run security tests
- [ ] Configure SSL/TLS
- [ ] Set up monitoring
- [ ] Configure backups

## Testing

### Backend Tests
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test crm

# Run with coverage
coverage run --source='.' manage.py test
coverage report
```

### Frontend Tests
```bash
cd frontend
npm test
npm run test:coverage
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Contact the development team
- Check the documentation wiki

## Roadmap

### Upcoming Features
- [ ] Advanced reporting and analytics
- [ ] Mobile applications (iOS/Android)
- [ ] Third-party integrations
- [ ] AI-powered lead scoring
- [ ] Advanced workflow automation
- [ ] Multi-language support
- [ ] Advanced security features
- [ ] Performance optimizations
