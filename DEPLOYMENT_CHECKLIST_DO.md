# 🚀 Digital Ocean Deployment Checklist

## Pre-Deployment Tasks

### ✅ Local Preparation (Complete these first)
- [x] Generate SECRET_KEY
- [x] Create .env.production file
- [ ] Update .env.production with actual values:
  - [ ] EMAIL_HOST_USER
  - [ ] EMAIL_HOST_PASSWORD
  - [ ] DEFAULT_FROM_EMAIL
  - [ ] DB_PASSWORD
  - [ ] ALLOWED_HOSTS
  - [ ] CORS_ALLOWED_ORIGINS
- [ ] Test configuration locally
- [ ] Commit and push code to repository

### 📦 DigitalOcean Setup
- [ ] Create DigitalOcean account
- [ ] Create Droplet (Ubuntu 22.04, 4GB RAM, 2 vCPUs minimum)
- [ ] Configure SSH access
- [ ] Note Droplet IP address
- [ ] Configure DNS (optional but recommended)

### 🔧 Server Configuration
- [ ] SSH into droplet
- [ ] Update system packages: `apt update && apt upgrade -y`
- [ ] Install Docker: `curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh`
- [ ] Install Docker Compose
- [ ] Clone repository
- [ ] Copy .env.production to server
- [ ] Review and update .env.production on server

### 🚀 Deployment
- [ ] Build Docker images: `docker-compose -f docker-compose.prod.yml build`
- [ ] Start services: `docker-compose -f docker-compose.prod.yml up -d`
- [ ] Run migrations: `docker-compose -f docker-compose.prod.yml exec web python manage.py migrate`
- [ ] Collect static files: `docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput`
- [ ] Create superuser: `docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser`

### ✅ Validation
- [ ] Check services are running: `docker-compose -f docker-compose.prod.yml ps`
- [ ] Test health endpoint: `curl http://YOUR_IP/health/`
- [ ] Test admin login: `http://YOUR_IP/admin/`
- [ ] Test API endpoints
- [ ] Verify email sending
- [ ] Test rate limiting
- [ ] Review logs: `docker-compose -f docker-compose.prod.yml logs`

### 🔒 Security
- [ ] Configure firewall (UFW)
- [ ] Set up SSL/TLS certificates (Let's Encrypt)
- [ ] Configure backup strategy
- [ ] Set up monitoring
- [ ] Review security headers
- [ ] Test 2FA functionality

### 📊 Post-Deployment
- [ ] Monitor application logs
- [ ] Monitor system resources
- [ ] Set up alerts
- [ ] Document any issues
- [ ] Create backup schedule

## Quick Commands Reference

### Docker Commands
```bash
# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Stop services
docker-compose -f docker-compose.prod.yml down

# Update application
git pull
docker-compose -f docker-compose.prod.yml up -d --build
```

### Database Commands
```bash
# Backup database
docker-compose -f docker-compose.prod.yml exec db pg_dump -U crm_user crm_production > backup.sql

# Restore database
docker-compose -f docker-compose.prod.yml exec -T db psql -U crm_user crm_production < backup.sql
```

### Monitoring Commands
```bash
# Check system resources
docker stats

# Check disk usage
df -h

# Check memory usage
free -h
```

## Troubleshooting

### Application won't start
- Check logs: `docker-compose -f docker-compose.prod.yml logs web`
- Verify environment variables
- Check database connection
- Verify SECRET_KEY is set

### Database connection errors
- Ensure PostgreSQL container is running
- Check database credentials in .env.production
- Verify network connectivity between containers

### Email not sending
- Verify EMAIL_* environment variables
- Check SMTP credentials
- Test with: `python manage.py shell` and try sending test email
- Check email service logs

### Rate limiting not working
- Verify Redis is running: `docker-compose -f docker-compose.prod.yml ps redis`
- Check REDIS_URL in .env.production
- Test Redis connection: `docker-compose -f docker-compose.prod.yml exec redis redis-cli ping`

## Support

For detailed documentation, see:
- DEPLOYMENT_READINESS.md
- DIGITALOCEAN_DEPLOYMENT_GUIDE.md
- SECURITY_FIXES_README.md
