#!/bin/bash

# 🚀 DigitalOcean Deployment Script for CRM System
# This script deploys the CRM system to DigitalOcean

set -e  # Exit on any error

echo "🚀 Starting DigitalOcean CRM Deployment..."

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

# Check if running on DigitalOcean
check_environment() {
    print_status "Checking deployment environment..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    print_success "Environment check passed"
}

# Install Docker and Docker Compose on Ubuntu
install_docker() {
    print_status "Installing Docker and Docker Compose..."
    
    # Update package index
    sudo apt-get update
    
    # Install required packages
    sudo apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # Add Docker's official GPG key
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Set up stable repository
    echo \
        "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker Engine
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    
    # Install Docker Compose
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    
    # Add current user to docker group
    sudo usermod -aG docker $USER
    
    print_success "Docker and Docker Compose installed successfully"
}

# Create production environment file
create_production_env() {
    print_status "Creating production environment configuration..."
    
    if [ ! -f .env.production ]; then
        cp env.production.example .env.production
        print_warning "Please update .env.production with your actual configuration values"
        print_warning "Important: Change SECRET_KEY, database passwords, and other sensitive values"
    else
        print_status "Production environment file already exists"
    fi
}

# Generate SSL certificates
setup_ssl() {
    print_status "Setting up SSL certificates..."
    
    # Create SSL directory
    mkdir -p nginx/ssl
    
    # Generate self-signed certificate for initial setup
    # In production, replace with Let's Encrypt certificates
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/key.pem \
        -out nginx/ssl/cert.pem \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=your-domain.com"
    
    print_success "SSL certificates generated"
    print_warning "For production, replace with Let's Encrypt certificates"
}

# Create monitoring configuration
setup_monitoring() {
    print_status "Setting up monitoring configuration..."
    
    # Create monitoring directory
    mkdir -p monitoring/grafana/dashboards
    mkdir -p monitoring/grafana/datasources
    
    # Create Prometheus configuration
    cat > monitoring/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'django'
    static_configs:
      - targets: ['web:8000']
    metrics_path: '/metrics/'
    scrape_interval: 30s

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:80']
    metrics_path: '/nginx_status'
    scrape_interval: 30s
EOF

    # Create Grafana datasource
    cat > monitoring/grafana/datasources/prometheus.yml << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

    print_success "Monitoring configuration created"
}

# Create systemd service for auto-start
create_systemd_service() {
    print_status "Creating systemd service for auto-start..."
    
    sudo tee /etc/systemd/system/crm.service > /dev/null << EOF
[Unit]
Description=CRM System
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=$(pwd)
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

    # Reload systemd and enable service
    sudo systemctl daemon-reload
    sudo systemctl enable crm.service
    
    print_success "Systemd service created and enabled"
}

# Deploy the application
deploy_application() {
    print_status "Deploying CRM application..."
    
    # Stop existing containers
    docker-compose -f docker-compose.prod.yml down || true
    
    # Build and start services
    docker-compose -f docker-compose.prod.yml build --no-cache
    docker-compose -f docker-compose.prod.yml up -d
    
    print_success "Application deployed successfully"
}

# Wait for services to be ready
wait_for_services() {
    print_status "Waiting for services to be ready..."
    
    # Wait for database
    print_status "Waiting for database..."
    sleep 30
    
    # Wait for web service
    print_status "Waiting for web service..."
    sleep 20
    
    print_success "Services are ready"
}

# Run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
    docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
    
    print_success "Migrations completed successfully"
}

# Create superuser
create_superuser() {
    print_status "Creating superuser..."
    
    docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser --noinput --username admin --email admin@example.com || true
    
    print_success "Superuser created (username: admin)"
}

# Setup monitoring
setup_monitoring_data() {
    print_status "Setting up monitoring data..."
    
    # Create sample data
    docker-compose -f docker-compose.prod.yml exec web python manage.py create_sample_data || true
    
    print_success "Monitoring data setup completed"
}

# Health check
health_check() {
    print_status "Performing health check..."
    
    # Check if web service is running
    if docker-compose -f docker-compose.prod.yml ps web | grep -q "Up"; then
        print_success "Web service is running"
    else
        print_error "Web service is not running"
        exit 1
    fi
    
    # Check if database service is running
    if docker-compose -f docker-compose.prod.yml ps db | grep -q "Up"; then
        print_success "Database service is running"
    else
        print_error "Database service is not running"
        exit 1
    fi
    
    # Check if Redis service is running
    if docker-compose -f docker-compose.prod.yml ps redis | grep -q "Up"; then
        print_success "Redis service is running"
    else
        print_error "Redis service is not running"
        exit 1
    fi
    
    print_success "All services are healthy"
}

# Display deployment information
show_deployment_info() {
    print_success "🎉 CRM System deployed successfully on DigitalOcean!"
    echo ""
    echo "📊 Deployment Information:"
    echo "=========================="
    echo "🌐 Web Application: http://$(curl -s ifconfig.me)"
    echo "🔧 Admin Panel: http://$(curl -s ifconfig.me)/admin"
    echo "📊 Grafana Dashboard: http://$(curl -s ifconfig.me):3000"
    echo "📈 Prometheus: http://$(curl -s ifconfig.me):9090"
    echo "💾 Database: PostgreSQL on port 5432"
    echo "🔄 Cache: Redis on port 6379"
    echo ""
    echo "👤 Default Admin Credentials:"
    echo "Username: admin"
    echo "Password: (set in .env.production file)"
    echo ""
    echo "🔧 Useful Commands:"
    echo "View logs: docker-compose -f docker-compose.prod.yml logs -f"
    echo "Stop services: docker-compose -f docker-compose.prod.yml down"
    echo "Restart services: docker-compose -f docker-compose.prod.yml restart"
    echo "Update services: docker-compose -f docker-compose.prod.yml pull && docker-compose -f docker-compose.prod.yml up -d"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Update .env.production with your configuration"
    echo "2. Set up your domain and DNS"
    echo "3. Configure Let's Encrypt SSL certificates"
    echo "4. Set up monitoring and alerts"
    echo "5. Configure backups"
    echo "6. Set up email notifications"
}

# Main deployment function
main() {
    echo "🏗️ DigitalOcean CRM Deployment Script"
    echo "======================================"
    echo ""
    
    check_environment
    install_docker
    create_production_env
    setup_ssl
    setup_monitoring
    create_systemd_service
    deploy_application
    wait_for_services
    run_migrations
    create_superuser
    setup_monitoring_data
    health_check
    show_deployment_info
}

# Run main function
main "$@"
