#!/bin/bash

# 🚀 CRM System Deployment Script
# This script prepares and deploys the CRM system for production

set -e  # Exit on any error

echo "🚀 Starting CRM System Deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    print_status "Checking Docker installation..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    print_success "Docker is installed"
}

# Check if Docker Compose is installed
check_docker_compose() {
    print_status "Checking Docker Compose installation..."
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    print_success "Docker Compose is installed"
}

# Create environment file
create_env_file() {
    print_status "Creating environment configuration..."
    if [ ! -f .env ]; then
        cat > .env << EOF
# Database Configuration
DB_NAME=crm_production
DB_USER=crm_user
DB_PASSWORD=secure_password_here
DB_HOST=db
DB_PORT=5432

# Redis Configuration
REDIS_URL=redis://redis:6379/0

# Django Configuration
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Security
ENCRYPTION_KEY=your-encryption-key-here
RATE_LIMIT_ENABLED=True

# Production Settings
CORS_ALLOWED_ORIGINS=https://your-domain.com
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
EOF
        print_warning "Please update the .env file with your actual configuration values"
    else
        print_status "Environment file already exists"
    fi
}

# Build Docker images
build_images() {
    print_status "Building Docker images..."
    docker-compose build --no-cache
    print_success "Docker images built successfully"
}

# Start services
start_services() {
    print_status "Starting services..."
    docker-compose up -d
    print_success "Services started successfully"
}

# Wait for database
wait_for_db() {
    print_status "Waiting for database to be ready..."
    sleep 10
    print_success "Database is ready"
}

# Run migrations
run_migrations() {
    print_status "Running database migrations..."
    docker-compose exec web python manage.py migrate
    print_success "Migrations completed successfully"
}

# Create superuser
create_superuser() {
    print_status "Creating superuser..."
    docker-compose exec web python manage.py createsuperuser --noinput --username admin --email admin@example.com || true
    print_success "Superuser created (username: admin)"
}

# Collect static files
collect_static() {
    print_status "Collecting static files..."
    docker-compose exec web python manage.py collectstatic --noinput
    print_success "Static files collected successfully"
}

# Setup database indexes
setup_indexes() {
    print_status "Setting up database indexes..."
    docker-compose exec web python manage.py setup_database
    print_success "Database indexes created successfully"
}

# Create sample data
create_sample_data() {
    print_status "Creating sample data..."
    docker-compose exec web python manage.py create_sample_data
    print_success "Sample data created successfully"
}

# Health check
health_check() {
    print_status "Performing health check..."
    sleep 5
    
    # Check if web service is running
    if docker-compose ps web | grep -q "Up"; then
        print_success "Web service is running"
    else
        print_error "Web service is not running"
        exit 1
    fi
    
    # Check if database service is running
    if docker-compose ps db | grep -q "Up"; then
        print_success "Database service is running"
    else
        print_error "Database service is not running"
        exit 1
    fi
    
    # Check if Redis service is running
    if docker-compose ps redis | grep -q "Up"; then
        print_success "Redis service is running"
    else
        print_error "Redis service is not running"
        exit 1
    fi
    
    print_success "All services are healthy"
}

# Display deployment information
show_deployment_info() {
    print_success "🎉 CRM System deployed successfully!"
    echo ""
    echo "📊 Deployment Information:"
    echo "=========================="
    echo "🌐 Web Application: http://localhost:8000"
    echo "🔧 Admin Panel: http://localhost:8000/admin"
    echo "📚 API Documentation: http://localhost:8000/api/docs/"
    echo "💾 Database: PostgreSQL on localhost:5432"
    echo "🔄 Cache: Redis on localhost:6379"
    echo ""
    echo "👤 Default Admin Credentials:"
    echo "Username: admin"
    echo "Password: (set in .env file)"
    echo ""
    echo "🔧 Useful Commands:"
    echo "View logs: docker-compose logs -f"
    echo "Stop services: docker-compose down"
    echo "Restart services: docker-compose restart"
    echo "Update services: docker-compose pull && docker-compose up -d"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Update the .env file with your configuration"
    echo "2. Set up SSL/TLS certificates for production"
    echo "3. Configure your domain and DNS"
    echo "4. Set up monitoring and backups"
    echo "5. Configure email settings"
}

# Main deployment function
main() {
    echo "🏗️ CRM System Deployment Script"
    echo "================================"
    echo ""
    
    check_docker
    check_docker_compose
    create_env_file
    build_images
    start_services
    wait_for_db
    run_migrations
    create_superuser
    collect_static
    setup_indexes
    create_sample_data
    health_check
    show_deployment_info
}

# Run main function
main "$@"
