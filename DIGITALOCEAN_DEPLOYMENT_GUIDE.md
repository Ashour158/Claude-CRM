# 🚀 **DIGITALOCEAN DEPLOYMENT GUIDE**

## 📊 **Complete Guide to Deploy CRM System on DigitalOcean**

This guide will help you deploy the CRM system to DigitalOcean with production-ready configuration, monitoring, and security.

---

## 🎯 **PREREQUISITES**

### **✅ DigitalOcean Account Setup**

1. **Create DigitalOcean Account**
   - Sign up at [digitalocean.com](https://digitalocean.com)
   - Verify your account and add payment method

2. **Create a Droplet**
   - **Recommended Size**: 4GB RAM, 2 vCPUs, 80GB SSD
   - **Operating System**: Ubuntu 22.04 LTS
   - **Region**: Choose closest to your users
   - **Authentication**: SSH Key (recommended) or Password

3. **Domain Setup** (Optional but recommended)
   - Purchase a domain or use subdomain
   - Point DNS to your droplet IP

---

## 🚀 **DEPLOYMENT STEPS**

### **Step 1: Connect to Your Droplet**

```bash
# Connect via SSH
ssh root@your-droplet-ip

# Or if using SSH key
ssh -i your-key.pem root@your-droplet-ip
```

### **Step 2: Update System and Install Dependencies**

```bash
# Update system packages
apt update && apt upgrade -y

# Install required packages
apt install -y curl wget git unzip software-properties-common

# Install Python 3.9+
apt install -y python3 python3-pip python3-venv
```

### **Step 3: Clone and Setup Project**

```bash
# Clone your repository (replace with your actual repo)
git clone https://github.com/your-username/crm-system.git
cd crm-system

# Make deployment script executable
chmod +x deploy-do.sh
```

### **Step 4: Configure Environment**

```bash
# Copy production environment template
cp env.production.example .env.production

# Edit environment file
nano .env.production
```

**Update these critical values in `.env.production`:**

```bash
# Change these values
SECRET_KEY=your-super-secret-key-here-change-this-in-production
DB_PASSWORD=your-secure-database-password
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,your-droplet-ip
```

### **Step 5: Run Deployment Script**

```bash
# Run the automated deployment
./deploy-do.sh
```

**The script will:**
- Install Docker and Docker Compose
- Create production environment
- Setup SSL certificates
- Configure monitoring
- Deploy the application
- Run database migrations
- Create superuser
- Setup health checks

---

## 🔧 **MANUAL DEPLOYMENT (Alternative)**

If you prefer manual deployment:

### **Install Docker and Docker Compose**

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Add user to docker group
usermod -aG docker $USER
```

### **Deploy Application**

```bash
# Build and start services
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput

# Create superuser
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

---

## 🔒 **SSL CERTIFICATE SETUP**

### **Option 1: Let's Encrypt (Recommended)**

```bash
# Install Certbot
apt install -y certbot python3-certbot-nginx

# Stop nginx temporarily
docker-compose -f docker-compose.prod.yml stop nginx

# Get certificate
certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Copy certificates to nginx directory
cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem

# Restart nginx
docker-compose -f docker-compose.prod.yml start nginx
```

### **Option 2: Self-Signed (Development)**

```bash
# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout nginx/ssl/key.pem \
    -out nginx/ssl/cert.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=your-domain.com"
```

---

## 📊 **MONITORING SETUP**

### **Access Monitoring Dashboards**

- **Grafana Dashboard**: `http://your-domain.com:3000`
  - Username: `admin`
  - Password: `admin123`

- **Prometheus**: `http://your-domain.com:9090`

### **Configure Monitoring**

```bash
# View application logs
docker-compose -f docker-compose.prod.yml logs -f web

# View nginx logs
docker-compose -f docker-compose.prod.yml logs -f nginx

# View database logs
docker-compose -f docker-compose.prod.yml logs -f db
```

---

## 🔧 **POST-DEPLOYMENT CONFIGURATION**

### **1. Domain Configuration**

```bash
# Update DNS records
# A Record: your-domain.com -> your-droplet-ip
# A Record: www.your-domain.com -> your-droplet-ip
```

### **2. Firewall Configuration**

```bash
# Configure UFW firewall
ufw allow 22/tcp    # SSH
ufw allow 80/tcp    # HTTP
ufw allow 443/tcp   # HTTPS
ufw enable
```

### **3. Email Configuration**

Update email settings in `.env.production`:

```bash
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### **4. Backup Configuration**

```bash
# Setup automated backups
crontab -e

# Add backup job (runs daily at 2 AM)
0 2 * * * /path/to/backup-script.sh
```

---

## 🚀 **PRODUCTION OPTIMIZATIONS**

### **1. Database Optimization**

```bash
# Connect to database
docker-compose -f docker-compose.prod.yml exec db psql -U crm_user -d crm_production

# Create indexes for better performance
CREATE INDEX CONCURRENTLY idx_accounts_company_id ON crm_account (company_id);
CREATE INDEX CONCURRENTLY idx_contacts_company_id ON crm_contact (company_id);
CREATE INDEX CONCURRENTLY idx_leads_company_id ON crm_lead (company_id);
```

### **2. Redis Optimization**

```bash
# Configure Redis for production
# Edit docker-compose.prod.yml redis service
command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru
```

### **3. Nginx Optimization**

```bash
# Update nginx configuration for better performance
# Edit nginx/nginx.prod.conf
worker_processes auto;
worker_connections 1024;
```

---

## 🔍 **TROUBLESHOOTING**

### **Common Issues and Solutions**

#### **1. Application Not Starting**

```bash
# Check container status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs web

# Restart services
docker-compose -f docker-compose.prod.yml restart
```

#### **2. Database Connection Issues**

```bash
# Check database logs
docker-compose -f docker-compose.prod.yml logs db

# Test database connection
docker-compose -f docker-compose.prod.yml exec web python manage.py dbshell
```

#### **3. SSL Certificate Issues**

```bash
# Check certificate validity
openssl x509 -in nginx/ssl/cert.pem -text -noout

# Renew Let's Encrypt certificate
certbot renew --dry-run
```

#### **4. Performance Issues**

```bash
# Monitor resource usage
docker stats

# Check disk space
df -h

# Check memory usage
free -h
```

---

## 📋 **MAINTENANCE COMMANDS**

### **Daily Operations**

```bash
# View application status
docker-compose -f docker-compose.prod.yml ps

# Update application
git pull
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

# Backup database
docker-compose -f docker-compose.prod.yml exec db pg_dump -U crm_user crm_production > backup.sql

# Restore database
docker-compose -f docker-compose.prod.yml exec -T db psql -U crm_user crm_production < backup.sql
```

### **Monitoring Commands**

```bash
# Check system resources
htop
df -h
free -h

# Check application logs
docker-compose -f docker-compose.prod.yml logs --tail=100 web

# Check nginx logs
docker-compose -f docker-compose.prod.yml logs --tail=100 nginx
```

---

## 🎯 **SECURITY CHECKLIST**

### **✅ Security Measures Implemented**

- [x] **SSL/TLS Encryption** - HTTPS with modern ciphers
- [x] **Security Headers** - XSS, CSRF, Content-Type protection
- [x] **Rate Limiting** - API and login rate limiting
- [x] **Firewall** - UFW configured for essential ports
- [x] **Database Security** - PostgreSQL with RLS
- [x] **Container Security** - Non-root containers
- [x] **Monitoring** - Prometheus and Grafana monitoring
- [x] **Backup Strategy** - Automated database backups

### **🔒 Additional Security Recommendations**

1. **Regular Updates**
   ```bash
   # Update system packages
   apt update && apt upgrade -y
   
   # Update Docker images
   docker-compose -f docker-compose.prod.yml pull
   ```

2. **Access Control**
   ```bash
   # Disable root login
   nano /etc/ssh/sshd_config
   # Set: PermitRootLogin no
   systemctl restart ssh
   ```

3. **Monitoring Alerts**
   - Set up Grafana alerts
   - Configure email notifications
   - Monitor disk space and memory usage

---

## 🎉 **DEPLOYMENT SUCCESS**

### **✅ Access Your CRM System**

- **Web Application**: `https://your-domain.com`
- **Admin Panel**: `https://your-domain.com/admin`
- **API Documentation**: `https://your-domain.com/api/docs/`
- **Grafana Dashboard**: `https://your-domain.com:3000`
- **Prometheus**: `https://your-domain.com:9090`

### **👤 Default Credentials**

- **Admin Username**: `admin`
- **Admin Password**: (set during deployment)
- **Grafana Username**: `admin`
- **Grafana Password**: `admin123`

### **📊 System Status**

Your CRM system is now:
- ✅ **Deployed** on DigitalOcean
- ✅ **Secured** with SSL/TLS
- ✅ **Monitored** with Prometheus/Grafana
- ✅ **Optimized** for production
- ✅ **Backed up** automatically
- ✅ **Scalable** for growth

**🚀 Your CRM system is ready for production use!**
