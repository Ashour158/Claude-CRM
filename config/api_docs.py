# config/api_docs.py
# API Documentation Configuration

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from drf_yasg.generators import OpenAPISchemaGenerator
from rest_framework import status
from rest_framework.response import Response

# API Documentation Configuration
API_INFO = openapi.Info(
    title="CRM System API",
    default_version="v1",
    description="""
    # 🚀 Enterprise CRM System API
    
    A comprehensive, multi-tenant CRM system with advanced features including:
    
    ## 🔐 Authentication
    - JWT-based authentication with refresh tokens
    - Multi-tenant company isolation
    - Role-based access control
    
    ## 📊 Core CRM Features
    - **Accounts**: Company/organization management
    - **Contacts**: Individual person management
    - **Leads**: Potential customer tracking
    - **Deals**: Sales opportunity management
    - **Activities**: Task and event tracking
    - **Products**: Product catalog management
    
    ## 🏢 Business Features
    - **Sales Pipeline**: Deal stages and forecasting
    - **Territory Management**: Geographic and industry-based territories
    - **Marketing**: Campaign and email template management
    - **Analytics**: Reports and dashboard widgets
    - **Workflow**: Business process automation
    
    ## 🔧 Advanced Features
    - **Multi-tenancy**: Company data isolation
    - **Audit Logging**: Comprehensive activity tracking
    - **Custom Fields**: Flexible data structure
    - **Integrations**: Third-party system connections
    - **Master Data**: Data quality and governance
    
    ## 📈 Performance Features
    - **Caching**: Redis-based response caching
    - **Pagination**: Efficient data loading
    - **Filtering**: Advanced search capabilities
    - **Rate Limiting**: API abuse prevention
    
    ## 🔒 Security Features
    - **Data Encryption**: Sensitive field encryption
    - **Input Validation**: Comprehensive data validation
    - **Audit Trails**: Complete activity logging
    - **Permission Control**: Granular access management
    
    ## 📱 Frontend Integration
    - **React Components**: Modern UI components
    - **Real-time Updates**: WebSocket connections
    - **Mobile Responsive**: Cross-device compatibility
    - **Performance Optimized**: Virtual scrolling and lazy loading
    
    ## 🚀 Deployment
    - **Docker Ready**: Containerized deployment
    - **Cloud Native**: Kubernetes compatible
    - **Monitoring**: Prometheus and Grafana integration
    - **Scaling**: Horizontal and vertical scaling support
    
    ---
    
    ## 📋 API Usage Examples
    
    ### Authentication
    ```bash
    # Register new user
    POST /api/core/register/
    {
        "email": "user@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "password": "securepassword",
        "password2": "securepassword",
        "company_name": "My Company"
    }
    
    # Login
    POST /api/core/login/
    {
        "email": "user@example.com",
        "password": "securepassword"
    }
    ```
    
    ### CRM Operations
    ```bash
    # Create Account
    POST /api/crm/accounts/
    {
        "name": "Acme Corporation",
        "type": "customer",
        "industry": "Technology",
        "email": "info@acme.com",
        "phone": "+1-555-0123"
    }
    
    # Create Contact
    POST /api/crm/contacts/
    {
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane@acme.com",
        "phone": "+1-555-0124",
        "account": "account-uuid",
        "title": "CEO"
    }
    ```
    
    ### Advanced Features
    ```bash
    # Create Deal
    POST /api/deals/deals/
    {
        "name": "Enterprise Software License",
        "account": "account-uuid",
        "contact": "contact-uuid",
        "amount": 50000.00,
        "stage": "proposal",
        "expected_close_date": "2024-03-01"
    }
    
    # Create Activity
    POST /api/activities/activities/
    {
        "activity_type": "meeting",
        "subject": "Product Demo",
        "description": "Demo of our CRM system",
        "activity_date": "2024-01-15T14:00:00Z",
        "duration_minutes": 60
    }
    ```
    
    ---
    
    ## 🔧 Technical Details
    
    ### Base URL
    ```
    https://your-domain.com/api/
    ```
    
    ### Authentication
    All API requests require JWT token in the Authorization header:
    ```
    Authorization: Bearer <access_token>
    ```
    
    ### Response Format
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
    
    **Error Response (400, 404, 500):**
    ```json
    {
        "error": "Error message",
        "details": {
            "field": ["Field-specific error"]
        }
    }
    ```
    
    ### Rate Limiting
    - **API Endpoints**: 100 requests per minute
    - **Authentication**: 10 requests per minute
    - **Bulk Operations**: 50 requests per minute
    
    ### Pagination
    - **Default Page Size**: 20 items
    - **Maximum Page Size**: 100 items
    - **Page Parameter**: `?page=1&page_size=20`
    
    ### Filtering
    - **Field Filtering**: `?field=value`
    - **Date Range**: `?created_after=2024-01-01&created_before=2024-12-31`
    - **Search**: `?search=query`
    - **Ordering**: `?ordering=field_name` or `?ordering=-field_name`
    
    ---
    
    ## 📞 Support
    
    For API support and questions:
    - **Documentation**: [API Docs](https://your-domain.com/api/docs/)
    - **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
    - **Contact**: support@your-domain.com
    
    ---
    
    **Version**: 1.0.0  
    **Last Updated**: 2024-01-01  
    **License**: MIT
    """,
    terms_of_service="https://your-domain.com/terms/",
    contact=openapi.Contact(
        name="CRM System Support",
        email="support@your-domain.com",
        url="https://your-domain.com/support/"
    ),
    license=openapi.License(
        name="MIT License",
        url="https://opensource.org/licenses/MIT"
    ),
)

# API Schema Generator
class CustomSchemaGenerator(OpenAPISchemaGenerator):
    """Custom schema generator with enhanced documentation"""
    
    def get_schema(self, request=None, public=False):
        schema = super().get_schema(request, public)
        
        # Add custom tags for better organization
        schema.tags = [
            {
                "name": "Authentication",
                "description": "User authentication and authorization"
            },
            {
                "name": "Core",
                "description": "Core system functionality"
            },
            {
                "name": "CRM",
                "description": "Customer relationship management"
            },
            {
                "name": "Activities",
                "description": "Activity and task management"
            },
            {
                "name": "Deals",
                "description": "Sales pipeline and deal management"
            },
            {
                "name": "Products",
                "description": "Product catalog management"
            },
            {
                "name": "Sales",
                "description": "Sales documents and processes"
            },
            {
                "name": "Vendors",
                "description": "Vendor and procurement management"
            },
            {
                "name": "Analytics",
                "description": "Reports and analytics"
            },
            {
                "name": "Marketing",
                "description": "Marketing campaigns and automation"
            },
            {
                "name": "System",
                "description": "System configuration and settings"
            },
            {
                "name": "Integrations",
                "description": "Third-party integrations"
            },
            {
                "name": "Workflow",
                "description": "Business process automation"
            }
        ]
        
        return schema

# Common Response Schemas
COMMON_RESPONSES = {
    '200': openapi.Response(
        description="Success",
        examples={
            "application/json": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "Example Resource",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }
    ),
    '201': openapi.Response(
        description="Created",
        examples={
            "application/json": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "New Resource",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }
    ),
    '400': openapi.Response(
        description="Bad Request",
        examples={
            "application/json": {
                "error": "Validation error",
                "details": {
                    "field": ["This field is required."]
                }
            }
        }
    ),
    '401': openapi.Response(
        description="Unauthorized",
        examples={
            "application/json": {
                "error": "Authentication credentials were not provided.",
                "details": "JWT token required"
            }
        }
    ),
    '403': openapi.Response(
        description="Forbidden",
        examples={
            "application/json": {
                "error": "You do not have permission to perform this action.",
                "details": "Insufficient permissions"
            }
        }
    ),
    '404': openapi.Response(
        description="Not Found",
        examples={
            "application/json": {
                "error": "Resource not found",
                "details": "The requested resource does not exist"
            }
        }
    ),
    '500': openapi.Response(
        description="Internal Server Error",
        examples={
            "application/json": {
                "error": "Internal server error",
                "details": "An unexpected error occurred"
            }
        }
    )
}

# Common Request Schemas
COMMON_REQUEST_SCHEMAS = {
    'PaginationQuery': openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'page': openapi.Schema(
                type=openapi.TYPE_INTEGER,
                description='Page number',
                example=1,
                minimum=1
            ),
            'page_size': openapi.Schema(
                type=openapi.TYPE_INTEGER,
                description='Number of items per page',
                example=20,
                minimum=1,
                maximum=100
            )
        }
    ),
    'SearchQuery': openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'search': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Search query',
                example='john doe'
            ),
            'ordering': openapi.Schema(
                type=openapi.TYPE_STRING,
                description='Order by field',
                example='-created_at'
            )
        }
    ),
    'DateRangeQuery': openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'created_after': openapi.Schema(
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
                description='Filter records created after this date',
                example='2024-01-01'
            ),
            'created_before': openapi.Schema(
                type=openapi.TYPE_STRING,
                format=openapi.FORMAT_DATE,
                description='Filter records created before this date',
                example='2024-12-31'
            )
        }
    )
}

# API Documentation Decorators
def api_doc_summary(summary, description=None):
    """Decorator for API endpoint documentation"""
    def decorator(func):
        func.__doc__ = f"{summary}\n\n{description or ''}"
        return func
    return decorator

def api_response_examples(examples):
    """Decorator for API response examples"""
    def decorator(func):
        func._swagger_response_examples = examples
        return func
    return decorator

# API Documentation Utilities
def get_api_schema():
    """Get the complete API schema"""
    return {
        'info': API_INFO,
        'generator_class': CustomSchemaGenerator,
        'responses': COMMON_RESPONSES,
        'request_schemas': COMMON_REQUEST_SCHEMAS
    }

def generate_api_docs():
    """Generate comprehensive API documentation"""
    return {
        'title': 'CRM System API Documentation',
        'version': '1.0.0',
        'description': 'Comprehensive API documentation for the CRM system',
        'endpoints': {
            'authentication': {
                'register': 'POST /api/core/register/',
                'login': 'POST /api/core/login/',
                'logout': 'POST /api/core/logout/',
                'refresh': 'POST /api/core/token/refresh/',
                'profile': 'GET /api/core/profile/'
            },
            'crm': {
                'accounts': 'GET /api/crm/accounts/',
                'contacts': 'GET /api/crm/contacts/',
                'leads': 'GET /api/crm/leads/',
                'deals': 'GET /api/deals/deals/',
                'activities': 'GET /api/activities/activities/',
                'products': 'GET /api/products/products/'
            },
            'analytics': {
                'dashboards': 'GET /api/analytics/dashboards/',
                'reports': 'GET /api/analytics/reports/',
                'kpis': 'GET /api/analytics/kpis/'
            }
        }
    }
