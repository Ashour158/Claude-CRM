# 📝 Quick Reference Card - Digital Ocean Deployment

## Essential Commands

### Local Machine

```bash
# Prepare deployment
./prepare-deployment.sh

# Validate configuration
./validate-deployment.sh

# Copy .env to server
scp .env.production root@YOUR_IP:/root/Claude-CRM/
```

### On DigitalOcean Server

```bash
# Initial setup
apt update && apt upgrade -y
curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Deploy
git clone https://github.com/Ashour158/Claude-CRM.git
cd Claude-CRM
docker-compose -f docker-compose.prod.yml up -d --build
sleep 30
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Firewall
ufw allow 22/tcp && ufw allow 80/tcp && ufw allow 443/tcp && ufw --force enable
```

## Required Environment Variables

```bash
SECRET_KEY=<generated-by-script>
DEBUG=False
ALLOWED_HOSTS=your-domain.com,YOUR_IP
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DB_PASSWORD=<strong-password>
REDIS_URL=redis://redis:6379/0
```

## Docker Commands

```bash
# View all services
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f web

# Restart service
docker-compose -f docker-compose.prod.yml restart web

# Stop all
docker-compose -f docker-compose.prod.yml down

# Start all
docker-compose -f docker-compose.prod.yml up -d

# Update app
git pull && docker-compose -f docker-compose.prod.yml up -d --build
```

## Database Commands

```bash
# Backup
docker-compose -f docker-compose.prod.yml exec db pg_dump -U crm_user crm_production > backup_$(date +%Y%m%d).sql

# Restore
docker-compose -f docker-compose.prod.yml exec -T db psql -U crm_user crm_production < backup.sql

# Shell access
docker-compose -f docker-compose.prod.yml exec db psql -U crm_user -d crm_production
```

## Monitoring Commands

```bash
# Resource usage
docker stats

# Disk space
df -h

# Memory
free -h

# System logs
journalctl -u docker -f
```

## Testing Endpoints

```bash
# Health check
curl http://YOUR_IP/health/

# Admin panel
http://YOUR_IP/admin/

# API docs
http://YOUR_IP/api/docs/
```

## Troubleshooting

### App won't start
```bash
docker-compose -f docker-compose.prod.yml logs web
docker-compose -f docker-compose.prod.yml exec web python manage.py check --deploy
```

### Database issues
```bash
docker-compose -f docker-compose.prod.yml ps db
docker-compose -f docker-compose.prod.yml logs db
```

### Redis issues
```bash
docker-compose -f docker-compose.prod.yml ps redis
docker-compose -f docker-compose.prod.yml exec redis redis-cli ping
```

## SSL/TLS Setup

```bash
# Install Certbot
apt install -y certbot python3-certbot-nginx

# Get certificate
certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal
certbot renew --dry-run
```

## Backup Strategy

```bash
# Create backup script
cat > /root/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cd /root/Claude-CRM
docker-compose -f docker-compose.prod.yml exec -T db pg_dump -U crm_user crm_production > /root/backups/backup_${DATE}.sql
find /root/backups -type f -mtime +30 -delete
EOF

chmod +x /root/backup.sh

# Add to crontab (daily at 2 AM)
echo "0 2 * * * /root/backup.sh" | crontab -
```

## Security Checklist

- [ ] SECRET_KEY is unique and secure
- [ ] DEBUG=False
- [ ] ALLOWED_HOSTS configured
- [ ] Firewall enabled (UFW)
- [ ] SSL/TLS configured
- [ ] Strong database password
- [ ] SSH key authentication (no passwords)
- [ ] Regular backups scheduled
- [ ] Monitoring enabled
- [ ] Logs reviewed regularly

## Documentation Quick Links

- **Quick Start:** DIGITALOCEAN_QUICK_START.md
- **Staging:** STAGING_DEPLOYMENT_GUIDE.md
- **Security:** DEPLOYMENT_READINESS.md
- **Status:** DEPLOYMENT_STATUS_REPORT.md
- **Workflow:** DEPLOYMENT_WORKFLOW.md

## Support

**Email:** Check repository for contact information
**Issues:** https://github.com/Ashour158/Claude-CRM/issues
**Documentation:** See README.md

---

**Print this card for quick reference during deployment!**

**Version:** 1.0  
**Last Updated:** 2025-10-10
