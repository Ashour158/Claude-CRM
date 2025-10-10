# 🚀 Digital Ocean Deployment - Quick Start Guide

This guide provides a streamlined process for deploying the CRM system to DigitalOcean following security best practices outlined in DEPLOYMENT_READINESS.md.

## 📋 Overview

This repository includes automated scripts to prepare and validate your deployment:

- **prepare-deployment.sh** - Generates SECRET_KEY, creates .env.production, and sets up deployment
- **validate-deployment.sh** - Validates that all required environment variables are properly configured
- **DEPLOYMENT_CHECKLIST_DO.md** - Complete deployment checklist (auto-generated)

## 🎯 Quick Start (5 Steps)

### Step 1: Prepare Local Environment

Run the preparation script:

```bash
./prepare-deployment.sh
```

This script will:
- ✅ Generate a secure SECRET_KEY
- ✅ Create .env.production file
- ✅ Install dependencies
- ✅ Generate deployment checklist

**Important:** Save the generated SECRET_KEY securely!

### Step 2: Configure Environment Variables

Edit the `.env.production` file and update these critical values:

```bash
# Edit the file
nano .env.production

# Update these values:
SECRET_KEY=<generated-key-from-step-1>
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,YOUR_DROPLET_IP

# Email configuration
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
DEFAULT_FROM_EMAIL=noreply@your-domain.com

# Database
DB_PASSWORD=<create-strong-password>

# CORS
CORS_ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com
```

**How to get Gmail App Password:**
1. Go to Google Account → Security
2. Enable 2-Factor Authentication
3. Generate App Password
4. Use that password in EMAIL_HOST_PASSWORD

### Step 3: Validate Configuration

Run the validation script to ensure everything is configured correctly:

```bash
./validate-deployment.sh
```

Fix any errors or warnings before proceeding to deployment.

### Step 4: Create DigitalOcean Droplet

1. **Sign up/Login to DigitalOcean**
   - Go to [digitalocean.com](https://digitalocean.com)
   
2. **Create Droplet**
   - Click "Create" → "Droplets"
   - **Image:** Ubuntu 22.04 LTS
   - **Size:** Basic plan, 4GB RAM / 2 vCPUs (minimum)
   - **Region:** Choose closest to your users
   - **Authentication:** SSH Key (recommended)
   - **Hostname:** crm-production
   
3. **Note your Droplet's IP address**

### Step 5: Deploy to DigitalOcean

SSH into your droplet:

```bash
ssh root@YOUR_DROPLET_IP
```

Run the deployment commands:

```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Clone repository
git clone https://github.com/Ashour158/Claude-CRM.git
cd Claude-CRM

# Copy your .env.production file (either scp it or create manually)
# Option 1: Copy from local machine
# From your local machine: scp .env.production root@YOUR_DROPLET_IP:/root/Claude-CRM/

# Option 2: Create manually on server
nano .env.production
# Paste the content from your local .env.production

# Build and start services
docker-compose -f docker-compose.prod.yml up -d --build

# Wait for services to start (30 seconds)
sleep 30

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Create superuser (interactive)
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Configure firewall
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
```

## ✅ Verify Deployment

### Check Services

```bash
# Check all containers are running
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f web

# Check application health
curl http://YOUR_DROPLET_IP/health/
```

### Test the Application

1. **Admin Panel:** `http://YOUR_DROPLET_IP/admin/`
2. **API Docs:** `http://YOUR_DROPLET_IP/api/docs/`
3. **Login with your superuser credentials**

## 🔒 Security Checklist

After deployment, verify these security features are working:

- [ ] SECRET_KEY is set and unique
- [ ] DEBUG is False
- [ ] ALLOWED_HOSTS is properly configured
- [ ] Email verification is working (register a test user)
- [ ] 2FA is available (enable for admin user)
- [ ] Rate limiting is active (try 6+ login attempts)
- [ ] HTTPS is configured (if using domain)
- [ ] Firewall is enabled and configured
- [ ] Backups are scheduled

## 📊 Monitoring

### View Logs

```bash
# Application logs
docker-compose -f docker-compose.prod.yml logs -f web

# Database logs
docker-compose -f docker-compose.prod.yml logs -f db

# All services
docker-compose -f docker-compose.prod.yml logs -f
```

### System Resources

```bash
# Container stats
docker stats

# Disk usage
df -h

# Memory usage
free -h
```

## 🔧 Common Operations

### Restart Application

```bash
docker-compose -f docker-compose.prod.yml restart web
```

### Update Application

```bash
cd /root/Claude-CRM
git pull
docker-compose -f docker-compose.prod.yml up -d --build
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### Backup Database

```bash
docker-compose -f docker-compose.prod.yml exec db pg_dump -U crm_user crm_production > backup_$(date +%Y%m%d_%H%M%S).sql
```

### Restore Database

```bash
docker-compose -f docker-compose.prod.yml exec -T db psql -U crm_user crm_production < backup.sql
```

## 🆘 Troubleshooting

### Application Won't Start

```bash
# Check logs for errors
docker-compose -f docker-compose.prod.yml logs web

# Verify environment variables
docker-compose -f docker-compose.prod.yml exec web env | grep SECRET_KEY

# Check Django configuration
docker-compose -f docker-compose.prod.yml exec web python manage.py check --deploy
```

### Database Connection Issues

```bash
# Check database is running
docker-compose -f docker-compose.prod.yml ps db

# Test database connection
docker-compose -f docker-compose.prod.yml exec db psql -U crm_user -d crm_production -c "SELECT version();"
```

### Email Not Sending

```bash
# Test email configuration
docker-compose -f docker-compose.prod.yml exec web python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
```

### Rate Limiting Not Working

```bash
# Check Redis is running
docker-compose -f docker-compose.prod.yml ps redis

# Test Redis connection
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping
```

## 📚 Additional Resources

- **Security Fixes:** See SECURITY_FIXES_README.md
- **Deployment Readiness:** See DEPLOYMENT_READINESS.md
- **Detailed Guide:** See DIGITALOCEAN_DEPLOYMENT_STEP_BY_STEP.md
- **Configuration:** See DIGITALOCEAN_DEPLOYMENT_GUIDE.md

## 🎯 Staging Environment (Optional)

For testing before production:

1. Create a separate droplet for staging
2. Use the same process but with staging configuration
3. Set `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS` for staging domain
4. Test thoroughly before deploying to production

## 📞 Support

If you encounter issues:
1. Check the logs first
2. Review the troubleshooting section
3. Consult the detailed documentation
4. Check GitHub issues

---

**Last Updated:** 2025-10-10  
**Version:** 1.0  
**Status:** Production Ready ✅
