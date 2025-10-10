# 🧪 Staging Environment Deployment Guide

## Overview

This guide explains how to set up a staging environment on DigitalOcean to test your application before deploying to production.

## Why Staging?

- ✅ Test changes in production-like environment
- ✅ Validate configurations and integrations
- ✅ Perform QA testing
- ✅ Run security tests
- ✅ Minimize production risks

## Staging vs Production

| Aspect | Staging | Production |
|--------|---------|------------|
| **Purpose** | Testing | Live users |
| **Resources** | Smaller droplet (2GB) | Larger droplet (4GB+) |
| **Domain** | staging.yourdomain.com | yourdomain.com |
| **Database** | Test data | Real data |
| **Monitoring** | Basic | Comprehensive |
| **Backups** | Optional | Required |
| **SSL** | Let's Encrypt | Let's Encrypt |

## Step-by-Step Setup

### 1. Create Staging Droplet

Create a droplet similar to production but with smaller resources:

```bash
# Recommended specs for staging:
- Size: 2GB RAM / 1 vCPU
- Image: Ubuntu 22.04 LTS
- Region: Same as production
- Hostname: crm-staging
```

### 2. Prepare Staging Environment File

Create `.env.staging`:

```bash
# Copy production template
cp .env.production .env.staging

# Update for staging
nano .env.staging
```

Update these values:

```bash
# Staging-specific configuration
DEBUG=False
ALLOWED_HOSTS=staging.yourdomain.com,YOUR_STAGING_IP

# Use staging email for testing
EMAIL_HOST_USER=staging@yourdomain.com
DEFAULT_FROM_EMAIL=noreply-staging@yourdomain.com

# Staging database
DB_NAME=crm_staging
DB_PASSWORD=<staging-secure-password>

# CORS for staging
CORS_ALLOWED_ORIGINS=https://staging.yourdomain.com

# Staging-specific secret key
SECRET_KEY=<generate-new-staging-secret-key>

# Add staging indicator
ENVIRONMENT=staging
```

### 3. Deploy to Staging

SSH into your staging droplet:

```bash
ssh root@YOUR_STAGING_IP
```

Run deployment:

```bash
# Update system
apt update && apt upgrade -y

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Clone repository
git clone https://github.com/Ashour158/Claude-CRM.git
cd Claude-CRM

# Copy staging environment file
# From local: scp .env.staging root@YOUR_STAGING_IP:/root/Claude-CRM/.env.production

# Deploy with staging configuration
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for services
sleep 30

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Create staging superuser
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Configure firewall
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
```

### 4. Configure DNS (Optional)

If using a subdomain for staging:

1. Go to your DNS provider
2. Add an A record:
   - **Name:** staging
   - **Value:** YOUR_STAGING_IP
   - **TTL:** 300
3. Wait for DNS propagation (5-30 minutes)

### 5. Set Up SSL for Staging

```bash
# Install Certbot
apt install -y certbot python3-certbot-nginx

# Get certificate
certbot --nginx -d staging.yourdomain.com

# Auto-renewal is configured automatically
```

## Staging Validation Checklist

### ✅ Pre-Deployment Tests

Run these tests before deploying to staging:

```bash
# Validate configuration
./validate-deployment.sh

# Run security tests locally
pytest tests/security/test_critical_security_fixes.py -v

# Check for code issues
flake8 .
```

### ✅ Post-Deployment Tests

After deploying to staging, verify:

- [ ] Application is accessible
- [ ] Admin panel works
- [ ] User registration works
- [ ] Email verification works
- [ ] Login with 2FA works
- [ ] Rate limiting works
- [ ] API endpoints respond correctly
- [ ] Database operations work
- [ ] File uploads work
- [ ] All critical features functional

### ✅ Security Tests

```bash
# On staging server
cd /root/Claude-CRM

# Test SECRET_KEY enforcement
docker-compose -f docker-compose.prod.yml exec web python manage.py check --deploy

# Test rate limiting
# Try 6+ failed login attempts - should see 429 error

# Test email verification
# Register new user, verify email is sent

# Test 2FA
# Enable 2FA for a user, verify it's required
```

### ✅ Performance Tests

```bash
# Test response times
curl -w "@curl-format.txt" -o /dev/null -s http://staging.yourdomain.com/api/health/

# Create curl-format.txt:
echo 'time_total: %{time_total}s\n' > curl-format.txt
```

## Testing Workflow

### 1. Deploy Changes to Staging

```bash
# On local machine
git push origin main

# On staging server
cd /root/Claude-CRM
git pull origin main
docker-compose -f docker-compose.prod.yml up -d --build
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### 2. Run Tests

```bash
# Manual testing via UI
# API testing
# Integration testing
```

### 3. Review Logs

```bash
# Check for errors
docker-compose -f docker-compose.prod.yml logs -f web
```

### 4. Sign Off

Once all tests pass, you're ready for production deployment.

## Staging to Production Promotion

### Pre-Production Checklist

- [ ] All staging tests passed
- [ ] Security validation passed
- [ ] Performance acceptable
- [ ] No critical errors in logs
- [ ] Database migrations tested
- [ ] Backup strategy verified
- [ ] Team approval obtained

### Production Deployment

1. **Create database backup** (production)
2. **Deploy to production** following DIGITALOCEAN_QUICK_START.md
3. **Verify production** is working
4. **Monitor for issues**

## Staging Maintenance

### Update Staging Data

```bash
# Option 1: Fresh test data
docker-compose -f docker-compose.prod.yml exec web python manage.py flush --noinput
docker-compose -f docker-compose.prod.yml exec web python manage.py loaddata fixtures/test_data.json

# Option 2: Copy from production (sanitized)
# 1. Backup production database
# 2. Sanitize sensitive data
# 3. Restore to staging
```

### Refresh Staging Environment

```bash
# Complete refresh
docker-compose -f docker-compose.prod.yml down -v
git pull origin main
docker-compose -f docker-compose.prod.yml up -d --build
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

## Monitoring Staging

### Basic Monitoring

```bash
# Check service health
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Check resources
docker stats
```

### Set Up Alerts (Optional)

```bash
# Install monitoring tools
# Configure alerts for staging
# Set up Slack/email notifications
```

## Cost Optimization

Staging environments can be optimized for cost:

1. **Smaller droplet** (2GB instead of 4GB)
2. **Shut down during off-hours** (if not testing)
3. **Reduce backup frequency**
4. **Use smaller database instance**

## Common Issues

### Staging and Production Confusion

**Prevention:**
- Add ENVIRONMENT variable to .env files
- Use different visual themes (if possible)
- Add "STAGING" banner to UI
- Use different email subjects "[STAGING]"

### Database Sync Issues

**Solution:**
- Keep staging and production schemas in sync
- Run migrations on staging first
- Test data migrations on staging

### SSL Certificate Issues

**Solution:**
- Use Let's Encrypt for both staging and production
- Ensure DNS is properly configured
- Allow time for certificate issuance

## Automation (Advanced)

### Automated Staging Deployment

Create `.github/workflows/deploy-staging.yml`:

```yaml
name: Deploy to Staging

on:
  push:
    branches: [ develop ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to staging
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.STAGING_HOST }}
          username: ${{ secrets.STAGING_USER }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /root/Claude-CRM
            git pull origin develop
            docker-compose -f docker-compose.prod.yml up -d --build
```

## Summary

A staging environment is crucial for:
- ✅ Risk-free testing
- ✅ Quality assurance
- ✅ Team collaboration
- ✅ Confident deployments

Follow this guide to maintain a healthy staging environment that mirrors production and catches issues before they reach users.

---

**Last Updated:** 2025-10-10  
**Version:** 1.0  
**Next:** See DIGITALOCEAN_QUICK_START.md for production deployment
