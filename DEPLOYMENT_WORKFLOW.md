# 🗺️ Deployment Workflow

## Visual Deployment Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEPLOYMENT WORKFLOW                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 1: LOCAL PREPARATION                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Run Script:     │
                    │ prepare-        │
                    │ deployment.sh   │
                    └────────┬────────┘
                              │
                 ┌────────────┴────────────┐
                 │                         │
                 ▼                         ▼
        ┌────────────────┐      ┌────────────────┐
        │ Generate       │      │ Create         │
        │ SECRET_KEY     │      │ .env.production│
        └────────┬───────┘      └────────┬───────┘
                 │                       │
                 └───────────┬───────────┘
                             │
                             ▼
                   ┌─────────────────┐
                   │ Edit .env.      │
                   │ production      │
                   │ with actual     │
                   │ values          │
                   └────────┬────────┘
                             │
                             ▼
                   ┌─────────────────┐
                   │ Run Script:     │
                   │ validate-       │
                   │ deployment.sh   │
                   └────────┬────────┘
                             │
                    ┌────────┴────────┐
                    │ All Valid?      │
                    └────────┬────────┘
                             │
                  ┌──────────┴──────────┐
                  │                     │
            NO    ▼                     ▼    YES
        ┌─────────────┐          ┌─────────────┐
        │ Fix Issues  │          │ Continue to │
        │ and Retry   │          │ Phase 2     │
        └──────┬──────┘          └─────────────┘
               │                        │
               └────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 2: STAGING DEPLOYMENT (Optional but Recommended)          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Create Staging  │
                    │ Droplet on      │
                    │ DigitalOcean    │
                    └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ SSH to Staging  │
                    │ Server          │
                    └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Install Docker  │
                    │ & Dependencies  │
                    └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Deploy          │
                    │ Application     │
                    └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Run Tests &     │
                    │ Validation      │
                    └────────┬────────┘
                              │
                    ┌─────────┴────────┐
                    │ Tests Pass?      │
                    └─────────┬────────┘
                              │
                  ┌───────────┴───────────┐
                  │                       │
            NO    ▼                       ▼    YES
        ┌─────────────┐          ┌─────────────┐
        │ Debug &     │          │ Sign Off for│
        │ Fix Issues  │          │ Production  │
        └──────┬──────┘          └─────────────┘
               │                        │
               └────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 3: PRODUCTION DEPLOYMENT                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Create          │
                    │ Production      │
                    │ Droplet         │
                    │ (4GB+ RAM)      │
                    └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ SSH to          │
                    │ Production      │
                    │ Server          │
                    └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ System Update   │
                    │ & Security      │
                    └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Install Docker  │
                    │ Docker Compose  │
                    └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Clone Repo      │
                    │ Copy .env.prod  │
                    └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Build & Start   │
                    │ Containers      │
                    └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Run Migrations  │
                    │ Collect Static  │
                    └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Create          │
                    │ Superuser       │
                    └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Configure       │
                    │ Firewall (UFW)  │
                    └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Set Up SSL/TLS  │
                    │ (Let's Encrypt) │
                    └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Enable          │
                    │ Monitoring      │
                    └────────┬────────┘

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 4: VALIDATION                                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Test Health     │
                    │ Endpoint        │
                    └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Test Admin      │
                    │ Login           │
                    └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Test User       │
                    │ Registration    │
                    └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Test Email      │
                    │ Verification    │
                    └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Test 2FA        │
                    │ Login           │
                    └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Test Rate       │
                    │ Limiting        │
                    └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Review Logs     │
                    │ for Errors      │
                    └────────┬────────┘
                              │
                    ┌─────────┴────────┐
                    │ All Tests Pass?  │
                    └─────────┬────────┘
                              │
                  ┌───────────┴───────────┐
                  │                       │
            NO    ▼                       ▼    YES
        ┌─────────────┐          ┌─────────────┐
        │ Fix Issues  │          │ Deployment  │
        │ & Redeploy  │          │ COMPLETE! ✅│
        └──────┬──────┘          └─────────────┘
               │                        │
               └────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ PHASE 5: MONITORING & MAINTENANCE                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Monitor Logs    │
                    └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Monitor         │
                    │ Resources       │
                    └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Schedule        │
                    │ Backups         │
                    └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Set Up Alerts   │
                    └────────┬────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Regular         │
                    │ Updates         │
                    └─────────────────┘

═══════════════════════════════════════════════════════════════════

                        DEPLOYMENT COMPLETE! 🎉

═══════════════════════════════════════════════════════════════════
```

## Quick Reference Commands

### Phase 1: Local Preparation
```bash
# Step 1: Prepare deployment
./prepare-deployment.sh

# Step 2: Edit environment
nano .env.production

# Step 3: Validate
./validate-deployment.sh
```

### Phase 2: Staging (Optional)
```bash
# Create droplet, then SSH in
ssh root@STAGING_IP

# Run deployment commands
# (See STAGING_DEPLOYMENT_GUIDE.md)
```

### Phase 3: Production Deployment
```bash
# SSH to production server
ssh root@PRODUCTION_IP

# Quick deployment
curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh
git clone https://github.com/Ashour158/Claude-CRM.git
cd Claude-CRM
# Copy .env.production from local
docker-compose -f docker-compose.prod.yml up -d --build
```

### Phase 4: Validation
```bash
# Test health
curl http://YOUR_IP/health/

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Check services
docker-compose -f docker-compose.prod.yml ps
```

### Phase 5: Monitoring
```bash
# Watch logs
docker-compose -f docker-compose.prod.yml logs -f web

# Check resources
docker stats

# Backup database
docker-compose -f docker-compose.prod.yml exec db pg_dump -U crm_user crm_production > backup.sql
```

## Timeline Estimates

- **Phase 1:** 15-30 minutes (local preparation)
- **Phase 2:** 1-2 hours (staging deployment and testing)
- **Phase 3:** 30-60 minutes (production deployment)
- **Phase 4:** 30-45 minutes (validation)
- **Phase 5:** Ongoing (monitoring)

**Total Initial Deployment:** 2.5-4.5 hours

## Success Indicators

✅ Green indicators mean success:
- Services running: `docker-compose ps` shows all "Up"
- No errors in logs: `docker logs` shows no critical errors
- Application accessible: HTTP 200 responses
- Admin login works
- Email sending works
- 2FA functions correctly

❌ Red indicators need attention:
- Services not running
- Critical errors in logs
- 500 errors from application
- Database connection failures
- Redis connection failures

---

**Use this workflow to guide your deployment process!**
