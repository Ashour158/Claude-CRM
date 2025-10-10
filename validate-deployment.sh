#!/bin/bash

# 🔍 Deployment Validation Script
# Validates that production environment is properly configured

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

VALIDATION_PASSED=0
VALIDATION_FAILED=0
VALIDATION_WARNINGS=0

print_status() {
    echo -e "${BLUE}[CHECK]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓ PASS]${NC} $1"
    ((VALIDATION_PASSED++))
}

print_error() {
    echo -e "${RED}[✗ FAIL]${NC} $1"
    ((VALIDATION_FAILED++))
}

print_warning() {
    echo -e "${YELLOW}[! WARN]${NC} $1"
    ((VALIDATION_WARNINGS++))
}

echo "🔍 Production Environment Validation"
echo "====================================="
echo ""

# Check if .env.production exists
print_status "Checking if .env.production exists..."
if [ -f ".env.production" ]; then
    print_success ".env.production file exists"
else
    print_error ".env.production file not found"
    echo "Run ./prepare-deployment.sh first"
    exit 1
fi

# Load environment variables from .env.production
source .env.production

# Validate SECRET_KEY
print_status "Validating SECRET_KEY..."
if [ -z "$SECRET_KEY" ]; then
    print_error "SECRET_KEY is not set"
elif [ "$SECRET_KEY" == "your-super-secret-key-here-change-this-in-production" ]; then
    print_error "SECRET_KEY is using default value - must be changed"
elif [ ${#SECRET_KEY} -lt 50 ]; then
    print_warning "SECRET_KEY is less than 50 characters (recommended: 50+)"
else
    print_success "SECRET_KEY is properly configured"
fi

# Validate DEBUG setting
print_status "Validating DEBUG setting..."
if [ "$DEBUG" == "False" ] || [ "$DEBUG" == "false" ]; then
    print_success "DEBUG is disabled (production mode)"
elif [ "$DEBUG" == "True" ] || [ "$DEBUG" == "true" ]; then
    print_error "DEBUG is enabled - MUST be False in production"
else
    print_warning "DEBUG setting is unclear: $DEBUG"
fi

# Validate ALLOWED_HOSTS
print_status "Validating ALLOWED_HOSTS..."
if [ -z "$ALLOWED_HOSTS" ]; then
    print_error "ALLOWED_HOSTS is not set"
elif [[ "$ALLOWED_HOSTS" == *"your-domain.com"* ]] || [[ "$ALLOWED_HOSTS" == *"your-droplet-ip"* ]]; then
    print_error "ALLOWED_HOSTS contains placeholder values"
else
    print_success "ALLOWED_HOSTS is configured: $ALLOWED_HOSTS"
fi

# Validate Email Configuration
print_status "Validating email configuration..."
EMAIL_VALID=true

if [ -z "$EMAIL_HOST" ]; then
    print_error "EMAIL_HOST is not set"
    EMAIL_VALID=false
fi

if [ -z "$EMAIL_HOST_USER" ]; then
    print_error "EMAIL_HOST_USER is not set"
    EMAIL_VALID=false
elif [[ "$EMAIL_HOST_USER" == *"your-email"* ]]; then
    print_error "EMAIL_HOST_USER contains placeholder value"
    EMAIL_VALID=false
fi

if [ -z "$EMAIL_HOST_PASSWORD" ]; then
    print_error "EMAIL_HOST_PASSWORD is not set"
    EMAIL_VALID=false
elif [[ "$EMAIL_HOST_PASSWORD" == *"your-app-password"* ]] || [[ "$EMAIL_HOST_PASSWORD" == *"your-password"* ]]; then
    print_error "EMAIL_HOST_PASSWORD contains placeholder value"
    EMAIL_VALID=false
fi

if [ -z "$DEFAULT_FROM_EMAIL" ]; then
    print_error "DEFAULT_FROM_EMAIL is not set"
    EMAIL_VALID=false
elif [[ "$DEFAULT_FROM_EMAIL" == *"your-email"* ]]; then
    print_error "DEFAULT_FROM_EMAIL contains placeholder value"
    EMAIL_VALID=false
fi

if [ "$EMAIL_VALID" == "true" ]; then
    print_success "Email configuration is complete"
fi

# Validate Database Configuration
print_status "Validating database configuration..."
DB_VALID=true

if [ -z "$DB_NAME" ]; then
    print_error "DB_NAME is not set"
    DB_VALID=false
else
    print_success "DB_NAME is set: $DB_NAME"
fi

if [ -z "$DB_USER" ]; then
    print_error "DB_USER is not set"
    DB_VALID=false
else
    print_success "DB_USER is set: $DB_USER"
fi

if [ -z "$DB_PASSWORD" ]; then
    print_error "DB_PASSWORD is not set"
    DB_VALID=false
elif [[ "$DB_PASSWORD" == *"your-secure"* ]] || [[ "$DB_PASSWORD" == *"crm_password"* ]]; then
    print_error "DB_PASSWORD contains default/placeholder value"
    DB_VALID=false
elif [ ${#DB_PASSWORD} -lt 16 ]; then
    print_warning "DB_PASSWORD is less than 16 characters (recommended: 16+)"
else
    print_success "DB_PASSWORD is properly configured"
fi

# Validate Redis Configuration
print_status "Validating Redis configuration..."
if [ -z "$REDIS_URL" ]; then
    print_error "REDIS_URL is not set"
else
    print_success "REDIS_URL is configured"
fi

# Validate CORS Configuration
print_status "Validating CORS configuration..."
if [ -z "$CORS_ALLOWED_ORIGINS" ]; then
    print_warning "CORS_ALLOWED_ORIGINS is not set"
elif [[ "$CORS_ALLOWED_ORIGINS" == *"your-domain"* ]]; then
    print_error "CORS_ALLOWED_ORIGINS contains placeholder values"
else
    print_success "CORS_ALLOWED_ORIGINS is configured"
fi

# Validate Security Settings
print_status "Validating security settings..."
SECURITY_VALID=true

if [ "$SECURE_SSL_REDIRECT" != "True" ]; then
    print_warning "SECURE_SSL_REDIRECT is not enabled (should be True for production)"
    SECURITY_VALID=false
fi

if [ "$SECURE_HSTS_SECONDS" == "0" ]; then
    print_warning "SECURE_HSTS_SECONDS is 0 (should be 31536000 for production)"
    SECURITY_VALID=false
fi

if [ "$SECURITY_VALID" == "true" ]; then
    print_success "Security settings are properly configured"
fi

# Summary
echo ""
echo "======================================"
echo "Validation Summary"
echo "======================================"
echo -e "${GREEN}Passed: $VALIDATION_PASSED${NC}"
echo -e "${YELLOW}Warnings: $VALIDATION_WARNINGS${NC}"
echo -e "${RED}Failed: $VALIDATION_FAILED${NC}"
echo ""

if [ $VALIDATION_FAILED -gt 0 ]; then
    echo -e "${RED}❌ Validation FAILED${NC}"
    echo "Please fix the errors above before deploying to production"
    exit 1
elif [ $VALIDATION_WARNINGS -gt 0 ]; then
    echo -e "${YELLOW}⚠️  Validation completed with WARNINGS${NC}"
    echo "Review warnings above before deploying to production"
    exit 0
else
    echo -e "${GREEN}✅ Validation PASSED${NC}"
    echo "Environment is ready for deployment"
    exit 0
fi
