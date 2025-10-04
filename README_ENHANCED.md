# 🚀 Enhanced CRM System

A comprehensive, enterprise-grade Customer Relationship Management (CRM) system built with Django REST Framework and React, featuring multi-tenancy, advanced security, and modern UI/UX.

## ✨ Enhanced Features

### 🏗️ **Architecture Improvements**
- **Modular Django Apps**: Properly structured with separate apps for core, CRM, territories, activities, deals, and products
- **Enhanced Admin Interface**: Comprehensive Django admin with custom interfaces for all models
- **Management Commands**: Automated setup, sample data creation, and database management
- **Row-Level Security**: PostgreSQL RLS policies for complete data isolation
- **Docker Support**: Full containerization with docker-compose for development and production

### 🎨 **Frontend Enhancements**
- **Modern React Architecture**: Redux Toolkit for state management, React Query for data fetching
- **Material-UI Components**: Professional, responsive design with custom theming
- **TypeScript Support**: Type safety and better development experience
- **Responsive Design**: Mobile-first approach with adaptive layouts
- **Real-time Updates**: WebSocket support for live data updates

### 🔐 **Security Enhancements**
- **JWT Authentication**: Secure token-based authentication with refresh tokens
- **Multi-tenant Architecture**: Complete data isolation between companies
- **Permission System**: Role-based access control with granular permissions
- **Audit Logging**: Comprehensive audit trail for compliance
- **Rate Limiting**: API rate limiting to prevent abuse
- **Input Validation**: Comprehensive validation on all inputs

### 📊 **Business Features**
- **Advanced Lead Management**: Lead scoring, qualification, and conversion tracking
- **Sales Pipeline**: Customizable pipeline stages with probability tracking
- **Territory Management**: Hierarchical territories with automated assignment rules
- **Product Catalog**: Complete product management with pricing and inventory
- **Activity Tracking**: Comprehensive activity logging with multiple types
- **Reporting & Analytics**: Built-in reporting with charts and dashboards

## 🛠️ **Technology Stack**

### Backend
- **Django 4.2**: Web framework with REST API
- **PostgreSQL**: Primary database with RLS
- **Redis**: Caching and session storage
- **Celery**: Background task processing
- **JWT**: Authentication tokens
- **Docker**: Containerization

### Frontend
- **React 18**: Modern UI framework
- **Redux Toolkit**: State management
- **Material-UI**: Component library
- **React Query**: Data fetching and caching
- **TypeScript**: Type safety
- **Axios**: HTTP client

### Infrastructure
- **Docker Compose**: Multi-service orchestration
- **Nginx**: Web server and reverse proxy
- **Gunicorn**: WSGI server
- **Sentry**: Error monitoring
- **Redis**: Caching and message broker

## 🚀 **Quick Start**

### Prerequisites
- Python 3.8+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 13+

### 1. Clone and Setup
```bash
git clone <repository-url>
cd crm-system
```

### 2. Backend Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database and other settings

# Run setup script
python setup.py
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm start
```

### 4. Access the System
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000/api/
- **Admin Panel**: http://localhost:8000/admin/

## 🐳 **Docker Setup**

### Development
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production
```bash
# Build and start
docker-compose -f docker-compose.prod.yml up -d

# Scale services
docker-compose up -d --scale web=3
```

## 📁 **Project Structure**

```
crm-system/
├── config/                 # Django settings and configuration
├── core/                   # Core authentication and multi-tenancy
├── crm/                    # CRM models (accounts, contacts, leads)
├── territories/            # Territory management
├── activities/             # Activities, tasks, and events
├── deals/                  # Sales pipeline and deals
├── products/               # Product catalog and pricing
├── frontend/               # React frontend application
├── requirements.txt        # Python dependencies
├── docker-compose.yml      # Docker orchestration
├── Dockerfile             # Docker configuration
└── README.md              # This file
```

## 🔧 **Configuration**

### Environment Variables
```bash
# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=crm_db
DB_USER=crm_user
DB_PASSWORD=crm_password

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-password

# Security
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Django Settings
The system includes comprehensive Django settings with:
- Multi-tenant configuration
- Security settings
- Caching configuration
- Email settings
- Logging configuration
- Celery configuration

## 📊 **API Documentation**

### Authentication Endpoints
- `POST /api/auth/login/` - User login
- `POST /api/auth/register/` - User registration
- `POST /api/auth/logout/` - User logout
- `GET /api/auth/me/` - Current user
- `POST /api/auth/refresh/` - Refresh token

### CRM Endpoints
- `GET /api/crm/accounts/` - List accounts
- `POST /api/crm/accounts/` - Create account
- `GET /api/crm/contacts/` - List contacts
- `POST /api/crm/contacts/` - Create contact
- `GET /api/crm/leads/` - List leads
- `POST /api/crm/leads/` - Create lead

### Deals Endpoints
- `GET /api/deals/deals/` - List deals
- `POST /api/deals/deals/` - Create deal
- `GET /api/deals/deals/pipeline/` - Pipeline view
- `POST /api/deals/deals/{id}/win/` - Mark deal as won

### Activities Endpoints
- `GET /api/activities/activities/` - List activities
- `POST /api/activities/activities/` - Create activity
- `GET /api/activities/tasks/` - List tasks
- `POST /api/activities/tasks/` - Create task

## 🧪 **Testing**

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

## 🚀 **Deployment**

### Production Deployment
1. **Set up production environment**
2. **Configure environment variables**
3. **Set up database and Redis**
4. **Deploy with Docker**
5. **Configure Nginx**
6. **Set up SSL certificates**

### Scaling
- **Horizontal scaling**: Multiple web servers
- **Database optimization**: Connection pooling, read replicas
- **Caching**: Redis clustering
- **CDN**: Static file delivery

## 📈 **Performance**

### Optimizations
- **Database indexing**: Optimized queries
- **Caching**: Redis for frequently accessed data
- **Pagination**: Efficient data loading
- **Lazy loading**: On-demand data fetching
- **Compression**: Gzip compression for API responses

### Monitoring
- **Application metrics**: Performance monitoring
- **Error tracking**: Sentry integration
- **Logging**: Comprehensive logging
- **Health checks**: Service monitoring

## 🔒 **Security**

### Features
- **Authentication**: JWT tokens with refresh
- **Authorization**: Role-based access control
- **Data isolation**: Multi-tenant architecture
- **Input validation**: Comprehensive validation
- **Rate limiting**: API protection
- **Audit logging**: Complete audit trail

### Best Practices
- **HTTPS**: SSL/TLS encryption
- **Secure headers**: Security headers
- **Input sanitization**: XSS protection
- **SQL injection**: Parameterized queries
- **CSRF protection**: Cross-site request forgery protection

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 **License**

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 **Support**

For support and questions:
- Create an issue on GitHub
- Contact the development team
- Check the documentation wiki

## 🗺️ **Roadmap**

### Upcoming Features
- [ ] Advanced reporting and analytics
- [ ] Mobile applications (iOS/Android)
- [ ] Third-party integrations
- [ ] AI-powered lead scoring
- [ ] Advanced workflow automation
- [ ] Multi-language support
- [ ] Advanced security features
- [ ] Performance optimizations

---

**Built with ❤️ for modern businesses**
