#!/bin/bash

# 🚀 Quick DigitalOcean Deployment Script
# One-command deployment for DigitalOcean

set -e

echo "🚀 Quick DigitalOcean CRM Deployment"
echo "===================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    print_warning "Please run as root or with sudo"
    exit 1
fi

# Update system
print_status "Updating system packages..."
apt update && apt upgrade -y

# Install Docker
print_status "Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
rm get-docker.sh

# Install Docker Compose
print_status "Installing Docker Compose..."
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create production environment
print_status "Creating production environment..."
if [ ! -f .env.production ]; then
    cp env.production.example .env.production
    print_warning "Please update .env.production with your configuration"
fi

# Create SSL directory
print_status "Setting up SSL certificates..."
mkdir -p nginx/ssl

# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/key.pem \
    -out nginx/ssl/cert.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

# Create monitoring directories
print_status "Setting up monitoring..."
mkdir -p monitoring/grafana/dashboards
mkdir -p monitoring/grafana/datasources

# Deploy application
print_status "Deploying CRM application..."
docker-compose -f docker-compose.prod.yml up -d

# Wait for services
print_status "Waiting for services to start..."
sleep 30

# Run migrations
print_status "Running database migrations..."
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Create superuser
print_status "Creating superuser..."
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser --noinput --username admin --email admin@example.com || true

# Setup firewall
print_status "Configuring firewall..."
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

# Get server IP
SERVER_IP=$(curl -s ifconfig.me)

print_success "🎉 CRM System deployed successfully!"
echo ""
echo "📊 Access Information:"
echo "====================="
echo "🌐 Web Application: http://$SERVER_IP"
echo "🔧 Admin Panel: http://$SERVER_IP/admin"
echo "📊 Grafana: http://$SERVER_IP:3000"
echo "📈 Prometheus: http://$SERVER_IP:9090"
echo ""
echo "👤 Admin Credentials:"
echo "Username: admin"
echo "Password: (set in .env.production)"
echo ""
echo "🔧 Next Steps:"
echo "1. Update .env.production with your configuration"
echo "2. Set up your domain and DNS"
echo "3. Configure SSL certificates"
echo "4. Set up monitoring alerts"
echo ""
echo "📋 Useful Commands:"
echo "View logs: docker-compose -f docker-compose.prod.yml logs -f"
echo "Stop: docker-compose -f docker-compose.prod.yml down"
echo "Restart: docker-compose -f docker-compose.prod.yml restart"
