#!/bin/bash

# 🚀 Development Environment Setup Script
# This script sets up the development environment for the CRM system

set -e  # Exit on any error

echo "🚀 Setting up CRM Development Environment..."

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

# Check Python version
check_python() {
    print_status "Checking Python version..."
    
    if command -v python3.11 &> /dev/null; then
        PYTHON_CMD="python3.11"
        print_success "Python 3.11 found"
    elif command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        print_success "Python 3 found"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
        print_success "Python found"
    else
        print_error "Python not found. Please install Python 3.11 or later."
        exit 1
    fi
    
    # Check Python version
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    print_status "Python version: $PYTHON_VERSION"
}

# Create virtual environment
create_venv() {
    print_status "Creating virtual environment..."
    
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists. Removing..."
        rm -rf venv
    fi
    
    $PYTHON_CMD -m venv venv
    print_success "Virtual environment created"
}

# Activate virtual environment
activate_venv() {
    print_status "Activating virtual environment..."
    
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi
    
    print_success "Virtual environment activated"
}

# Install dependencies
install_dependencies() {
    print_status "Installing development dependencies..."
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install development requirements
    pip install -r requirements-dev.txt
    
    print_success "Dependencies installed"
}

# Create environment file
create_env() {
    print_status "Creating development environment file..."
    
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# Development Environment Variables
SECRET_KEY=django-insecure-dev-key-change-in-production
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0

# Database (SQLite for development)
DATABASE_URL=sqlite:///db.sqlite3

# Cache (Local memory for development)
CACHE_URL=locmem://

# Email (Console backend for development)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=logs/django.log

# Development Settings
CORS_ALLOW_ALL_ORIGINS=True
CORS_ALLOW_CREDENTIALS=True
EOF
        print_success "Environment file created"
    else
        print_warning "Environment file already exists"
    fi
}

# Create logs directory
create_logs_dir() {
    print_status "Creating logs directory..."
    
    mkdir -p logs
    print_success "Logs directory created"
}

# Run migrations
run_migrations() {
    print_status "Running database migrations..."
    
    python manage.py migrate
    print_success "Migrations completed"
}

# Create superuser
create_superuser() {
    print_status "Creating superuser..."
    
    echo "Creating superuser account..."
    python manage.py createsuperuser --noinput --username admin --email admin@example.com || {
        print_warning "Superuser creation failed or user already exists"
    }
    
    print_success "Superuser setup completed"
}

# Seed sample data
seed_data() {
    print_status "Seeding sample data..."
    
    python manage.py seed_data --companies 3 --users 10
    print_success "Sample data seeded"
}

# Run health check
health_check() {
    print_status "Running system health check..."
    
    python manage.py health_check --detailed
    print_success "Health check completed"
}

# Start development server
start_server() {
    print_status "Starting development server..."
    
    echo "🚀 Development server will start on http://localhost:8000"
    echo "Press Ctrl+C to stop the server"
    echo ""
    
    python manage.py runserver 0.0.0.0:8000
}

# Main setup function
main() {
    print_status "Starting CRM Development Environment Setup..."
    
    # Check Python
    check_python
    
    # Create virtual environment
    create_venv
    
    # Activate virtual environment
    activate_venv
    
    # Install dependencies
    install_dependencies
    
    # Create environment file
    create_env
    
    # Create logs directory
    create_logs_dir
    
    # Run migrations
    run_migrations
    
    # Create superuser
    create_superuser
    
    # Seed sample data
    seed_data
    
    # Run health check
    health_check
    
    print_success "Development environment setup completed!"
    print_status "You can now start the development server with: python manage.py runserver"
    print_status "Or run this script with --start-server to start the server immediately"
    
    # Check if --start-server flag is provided
    if [[ "$1" == "--start-server" ]]; then
        start_server
    fi
}

# Run main function
main "$@"
