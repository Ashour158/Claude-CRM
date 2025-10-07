# 🚀 **DIGITALOCEAN DEPLOYMENT - STEP BY STEP GUIDE**

## 📋 **DEPLOYMENT OPTIONS**

### **Option 1: Clean New Droplet (Recommended)**
- **Pros**: Fresh environment, no conflicts, clean setup
- **Cons**: Need to configure everything from scratch
- **Best for**: Production deployment, clean start

### **Option 2: Reuse Existing Droplet**
- **Pros**: Faster deployment, existing configuration
- **Cons**: Potential conflicts, need to clean up
- **Best for**: Updates, testing

## 🎯 **RECOMMENDED: CREATE NEW DROPLET**

I recommend creating a **new droplet** for a clean deployment. Here's the complete step-by-step process:

---

## 🚀 **STEP-BY-STEP DEPLOYMENT GUIDE**

### **STEP 1: Create New DigitalOcean Droplet**

#### **1.1 Create Droplet**
1. **Login to DigitalOcean**: Go to [digitalocean.com](https://digitalocean.com)
2. **Navigate to Droplets**: Click "Droplets" in the sidebar
3. **Create New Droplet**: Click "Create" → "Droplets"
4. **Choose Image**: Select "Ubuntu 22.04 LTS"
5. **Choose Size**: Select "Basic" → "Regular Intel" → **4GB RAM, 2 vCPUs** (minimum)
6. **Authentication**: Choose "SSH Key" (recommended) or "Password"
7. **Hostname**: Set to `crm-production` or your preferred name
8. **Create Droplet**: Click "Create Droplet"

#### **1.2 Note Important Information**
- **Droplet IP**: Copy the public IP address
- **Root Password**: If using password authentication
- **SSH Key**: If using SSH key authentication

### **STEP 2: Connect to Your Droplet**

#### **2.1 Connect via SSH**
```bash
# Using SSH Key (recommended)
ssh root@YOUR_DROPLET_IP

# Using Password
ssh root@YOUR_DROPLET_IP
# Enter password when prompted
```

#### **2.2 Update System**
```bash
# Update package list
apt update

# Upgrade system packages
apt upgrade -y

# Install essential packages
apt install -y curl wget git vim htop
```

### **STEP 3: Install Docker and Docker Compose**

#### **3.1 Install Docker**
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Add current user to docker group
usermod -aG docker $USER

# Start and enable Docker
systemctl start docker
systemctl enable docker

# Verify Docker installation
docker --version
```

#### **3.2 Install Docker Compose**
```bash
# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Make it executable
chmod +x /usr/local/bin/docker-compose

# Verify installation
docker-compose --version
```

### **STEP 4: Clone Your Repository**

#### **4.1 Clone the Repository**
```bash
# Navigate to home directory
cd /root

# Clone your repository
git clone https://github.com/Ashour158/Claude-CRM.git

# Navigate to project directory
cd Claude-CRM

# Verify files are present
ls -la
```

### **STEP 5: Configure Environment**

#### **5.1 Create Production Environment File**
```bash
# Copy the example environment file
cp env.production.example .env.production

# Edit the environment file
nano .env.production
```

#### **5.2 Update Environment Variables**
```bash
# Update the following critical variables in .env.production:

# Django Configuration
SECRET_KEY=your-super-secret-key-here-change-this-in-production
DEBUG=False
ALLOWED_HOSTS=YOUR_DROPLET_IP,your-domain.com,www.your-domain.com
DJANGO_SETTINGS_MODULE=config.settings

# Database Configuration
DB_NAME=crm_production
DB_USER=crm_user
DB_PASSWORD=your-secure-database-password-here
DB_HOST=db
DB_PORT=5432

# Redis Configuration
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Email Configuration (Update with your email settings)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# Security Configuration
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://YOUR_DROPLET_IP,https://your-domain.com
CORS_ALLOW_CREDENTIALS=True

# Generate a secure secret key
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### **STEP 6: Deploy the Application**

#### **6.1 Run the Deployment Script**
```bash
# Make the deployment script executable
chmod +x deploy-do.sh

# Run the deployment script
./deploy-do.sh
```

#### **6.2 Alternative: Manual Deployment**
```bash
# Build and start services
docker-compose -f docker-compose.prod.yml up --build -d

# Wait for services to start
sleep 30

# Run database migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Create superuser
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Seed sample data
docker-compose -f docker-compose.prod.yml exec web python manage.py seed_data --companies 3 --users 10

# Collect static files
docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
```

### **STEP 7: Configure Firewall**

#### **7.1 Configure UFW Firewall**
```bash
# Enable UFW
ufw enable

# Allow SSH
ufw allow ssh

# Allow HTTP
ufw allow 80

# Allow HTTPS
ufw allow 443

# Check status
ufw status
```

### **STEP 8: Verify Deployment**

#### **8.1 Check Service Status**
```bash
# Check Docker containers
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs web
docker-compose -f docker-compose.prod.yml logs nginx
```

#### **8.2 Test Application**
```bash
# Test health endpoint
curl http://YOUR_DROPLET_IP/health/

# Test API endpoint
curl http://YOUR_DROPLET_IP/api/core/health/

# Check if application is running
curl -I http://YOUR_DROPLET_IP
```

### **STEP 9: Access Your Application**

#### **9.1 Access URLs**
- **Main Application**: `http://YOUR_DROPLET_IP`
- **API Health**: `http://YOUR_DROPLET_IP/api/core/health/`
- **Admin Panel**: `http://YOUR_DROPLET_IP/admin/`
- **API Documentation**: `http://YOUR_DROPLET_IP/api/docs/`

#### **9.2 Create Admin User**
```bash
# Create superuser if not done already
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser
```

### **STEP 10: Optional - Domain Configuration**

#### **10.1 Configure Domain (if you have one)**
1. **Update DNS**: Point your domain to the droplet IP
2. **Update Environment**: Update `ALLOWED_HOSTS` in `.env.production`
3. **Restart Services**: `docker-compose -f docker-compose.prod.yml restart`

#### **10.2 SSL Certificate (Optional)**
```bash
# Install Certbot
apt install -y certbot

# Get SSL certificate
certbot certonly --standalone -d your-domain.com

# Update Nginx configuration for SSL
# (This requires additional configuration)
```

---

## 🔧 **TROUBLESHOOTING**

### **Common Issues and Solutions**

#### **Issue 1: Docker Compose Not Found**
```bash
# Solution: Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
```

#### **Issue 2: Permission Denied**
```bash
# Solution: Fix permissions
chmod +x deploy-do.sh
chmod +x quick-deploy-do.sh
```

#### **Issue 3: Database Connection Error**
```bash
# Solution: Check database service
docker-compose -f docker-compose.prod.yml logs db
docker-compose -f docker-compose.prod.yml restart db
```

#### **Issue 4: Port Already in Use**
```bash
# Solution: Check what's using the port
netstat -tulpn | grep :80
netstat -tulpn | grep :443

# Kill the process or change ports
```

#### **Issue 5: Environment Variables Not Loaded**
```bash
# Solution: Check environment file
cat .env.production
# Ensure file exists and has correct format
```

---

## 📊 **DEPLOYMENT VERIFICATION**

### **Checklist for Successful Deployment**

- ✅ **Droplet Created**: New Ubuntu 22.04 droplet
- ✅ **Docker Installed**: Docker and Docker Compose working
- ✅ **Repository Cloned**: Latest code from GitHub
- ✅ **Environment Configured**: `.env.production` file created
- ✅ **Services Running**: All Docker containers running
- ✅ **Database Migrated**: Database migrations completed
- ✅ **Superuser Created**: Admin user created
- ✅ **Sample Data**: Sample data seeded
- ✅ **Firewall Configured**: UFW firewall enabled
- ✅ **Application Accessible**: Application responding on port 80
- ✅ **Health Checks**: All health checks passing

### **Performance Verification**
```bash
# Check system resources
htop

# Check Docker resource usage
docker stats

# Check disk space
df -h

# Check memory usage
free -h
```

---

## 🎯 **NEXT STEPS AFTER DEPLOYMENT**

### **1. Initial Setup**
1. **Access Admin Panel**: Go to `http://YOUR_DROPLET_IP/admin/`
2. **Login**: Use the superuser credentials you created
3. **Explore System**: Check all modules and functionality
4. **Create Companies**: Set up your companies
5. **Add Users**: Create additional users

### **2. Production Optimization**
1. **Monitor Performance**: Use `htop` and `docker stats`
2. **Check Logs**: Monitor application logs
3. **Backup Setup**: Configure automated backups
4. **SSL Certificate**: Set up SSL for production
5. **Domain Configuration**: Configure your domain

### **3. Maintenance**
1. **Regular Updates**: Keep system updated
2. **Backup Verification**: Test backup and recovery
3. **Security Updates**: Apply security patches
4. **Performance Monitoring**: Monitor system performance
5. **Log Rotation**: Set up log rotation

---

## 🚀 **QUICK DEPLOYMENT COMMANDS**

### **One-Command Deployment**
```bash
# Quick deployment (if you want to skip manual steps)
chmod +x quick-deploy-do.sh
./quick-deploy-do.sh
```

### **Manual Deployment Commands**
```bash
# Build and start
docker-compose -f docker-compose.prod.yml up --build -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec web python manage.py migrate

# Create superuser
docker-compose -f docker-compose.prod.yml exec web python manage.py createsuperuser

# Seed data
docker-compose -f docker-compose.prod.yml exec web python manage.py seed_data
```

---

## 📞 **SUPPORT**

### **If You Need Help**
1. **Check Logs**: `docker-compose -f docker-compose.prod.yml logs`
2. **Restart Services**: `docker-compose -f docker-compose.prod.yml restart`
3. **Health Check**: `docker-compose -f docker-compose.prod.yml exec web python manage.py health_check`
4. **System Status**: `docker-compose -f docker-compose.prod.yml ps`

### **Emergency Commands**
```bash
# Stop all services
docker-compose -f docker-compose.prod.yml down

# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Rebuild everything
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up --build -d
```

---

**Status: 🎯 READY FOR DIGITALOCEAN DEPLOYMENT**

*Follow these steps carefully, and your CRM system will be successfully deployed on DigitalOcean!*
