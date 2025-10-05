# Security Hardening Roadmap

This document outlines the security hardening roadmap for the CRM system, detailing current state and planned improvements.

## Table of Contents
- [Current Security Posture](#current-security-posture)
- [Phase 1: Foundation](#phase-1-foundation)
- [Phase 2: Application Security](#phase-2-application-security)
- [Phase 3: Infrastructure Security](#phase-3-infrastructure-security)
- [Phase 4: Monitoring and Response](#phase-4-monitoring-and-response)
- [Security Checklist](#security-checklist)

## Current Security Posture

### ✅ Implemented
- JWT-based authentication (django-rest-framework-simplejwt)
- CORS protection (django-cors-headers)
- CSRF protection (Django middleware)
- XSS protection (Django templates auto-escape)
- SQL injection protection (Django ORM)
- Security headers (SecurityMiddleware)
- Rate limiting (django-ratelimit)
- Password hashing (Django defaults - PBKDF2)
- Multi-tenant data isolation (company-based filtering)
- Session security (secure cookies when not DEBUG)

### ⚠️ Needs Attention
- HTTPS enforcement (disabled in development)
- Strict Transport Security (HSTS) headers
- Content Security Policy (CSP)
- Subresource Integrity (SRI)
- Secret key rotation
- Comprehensive audit logging
- API rate limiting per user/endpoint
- Object-level permissions
- File upload validation
- Dependency vulnerability scanning (added to CI)

## Phase 1: Foundation

### Secure Configuration

**Priority**: Critical  
**Timeline**: Immediate

#### HTTPS Enforcement

```python
# config/settings.py (production)
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

**Action Items**:
- [ ] Enable HTTPS redirect in production
- [ ] Configure load balancer/proxy for SSL termination
- [ ] Obtain and install SSL certificates (Let's Encrypt recommended)
- [ ] Test SSL configuration with SSL Labs

#### HTTP Strict Transport Security (HSTS)

```python
# config/settings.py (production)
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

**Action Items**:
- [ ] Enable HSTS with short duration initially (300 seconds)
- [ ] Monitor for issues over 1 week
- [ ] Gradually increase to 31536000 seconds (1 year)
- [ ] Submit domain to HSTS preload list

#### Secure Cookie Configuration

```python
# config/settings.py
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'  # Or 'Strict' for more security
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
```

**Action Items**:
- [x] Configure HttpOnly cookies (already implemented)
- [ ] Evaluate SameSite policy (Lax vs Strict)
- [ ] Set secure cookie flags in production

#### Secret Management

**Action Items**:
- [ ] Rotate SECRET_KEY regularly (quarterly)
- [ ] Use environment variables for all secrets
- [ ] Consider using AWS Secrets Manager or HashiCorp Vault
- [ ] Never commit secrets to version control
- [ ] Audit .env.example to ensure no secrets

### Content Security Policy (CSP)

**Priority**: High  
**Timeline**: Within 2 weeks

#### Implementation

```python
# config/settings.py
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'")  # Gradually remove unsafe-inline
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'", "data:")
CSP_CONNECT_SRC = ("'self'",)
CSP_FRAME_ANCESTORS = ("'none'",)
```

**Action Items**:
- [ ] Install django-csp package
- [ ] Implement basic CSP headers
- [ ] Test with report-only mode first
- [ ] Gradually tighten policy
- [ ] Remove 'unsafe-inline' from script-src

### Security Headers

**Priority**: High  
**Timeline**: Within 1 week

#### Additional Headers

```python
# config/settings.py
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'same-origin'
```

**Action Items**:
- [x] Basic security headers (already implemented)
- [ ] Add Referrer-Policy header
- [ ] Add Permissions-Policy header
- [ ] Test with securityheaders.com

## Phase 2: Application Security

### Authentication & Authorization

**Priority**: Critical  
**Timeline**: 2-4 weeks

#### JWT Token Management

**Current**: Basic JWT with simplejwt

**Improvements**:
```python
# config/settings.py
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),  # Reduce from 60
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'RS256',  # Use asymmetric encryption
    'SIGNING_KEY': settings.PRIVATE_KEY,  # Load from secure location
    'VERIFYING_KEY': settings.PUBLIC_KEY,
}
```

**Action Items**:
- [ ] Reduce access token lifetime to 15 minutes
- [ ] Implement token refresh rotation
- [ ] Add token blacklisting (simplejwt.token_blacklist)
- [ ] Consider RS256 algorithm for asymmetric keys
- [ ] Implement token revocation on logout
- [ ] Add "remember me" functionality for longer sessions

#### Object-Level Permissions

**Priority**: High

**Action Items**:
- [ ] Implement django-guardian for object-level permissions
- [ ] Add row-level security checks in views
- [ ] Ensure multi-tenant isolation at query level
- [ ] Add permission decorators to all sensitive views
- [ ] Write tests for permission boundaries

#### Password Policy

**Priority**: Medium

```python
# config/settings.py
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 12}  # Increase from 8
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
```

**Action Items**:
- [ ] Increase minimum password length to 12 characters
- [ ] Add custom validator for password complexity
- [ ] Implement password expiration (90 days)
- [ ] Prevent password reuse (last 5 passwords)
- [ ] Add password strength meter in UI

### API Security

**Priority**: High  
**Timeline**: 2-3 weeks

#### Rate Limiting

**Current**: Basic rate limiting with django-ratelimit

**Improvements**:
```python
# Per-user rate limiting
@ratelimit(key='user', rate='100/h', method='POST')
@ratelimit(key='user', rate='1000/d', method='GET')

# Per-endpoint rate limiting
@ratelimit(key='ip', rate='10/m', method='POST', block=True)
```

**Action Items**:
- [ ] Implement per-user rate limits
- [ ] Add different limits for different endpoints
- [ ] More aggressive limits for auth endpoints
- [ ] Implement exponential backoff for repeated failures
- [ ] Add rate limit headers to responses

#### API Throttling (DRF)

```python
# config/settings.py
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}
```

**Action Items**:
- [ ] Enable DRF throttling
- [ ] Create custom throttle classes for different user tiers
- [ ] Add burst allowances
- [ ] Monitor and adjust rates based on usage

#### Input Validation

**Action Items**:
- [ ] Add comprehensive serializer validation
- [ ] Validate all file uploads (type, size, content)
- [ ] Sanitize HTML inputs (bleach library)
- [ ] Validate email formats
- [ ] Add max length validation for all text fields
- [ ] Implement schema validation for complex inputs

### File Upload Security

**Priority**: Medium  
**Timeline**: 1-2 weeks

**Action Items**:
- [ ] Validate file extensions (whitelist approach)
- [ ] Check file MIME types
- [ ] Scan uploaded files for malware (ClamAV)
- [ ] Limit file sizes (per file and total)
- [ ] Store uploads outside webroot
- [ ] Generate unique filenames (prevent overwrites)
- [ ] Serve files through Django (not direct access)
- [ ] Add virus scanning integration

### SQL Injection Prevention

**Priority**: Critical (Maintenance)

**Action Items**:
- [x] Use Django ORM (already implemented)
- [ ] Audit any raw SQL queries
- [ ] Use parameterized queries for all raw SQL
- [ ] Add SQL injection tests
- [ ] Enable SQL query logging in development

### XSS Prevention

**Priority**: Critical (Maintenance)

**Action Items**:
- [x] Django template auto-escaping (already enabled)
- [ ] Review all uses of `mark_safe` and `safe` filter
- [ ] Sanitize user-generated HTML content
- [ ] Implement CSP (see Phase 1)
- [ ] Add XSS tests to test suite

## Phase 3: Infrastructure Security

### Database Security

**Priority**: High  
**Timeline**: 1-2 weeks

**Action Items**:
- [ ] Use separate database credentials per environment
- [ ] Enable SSL for database connections
- [ ] Restrict database access to application servers only
- [ ] Enable database query logging
- [ ] Implement database encryption at rest
- [ ] Regular database backups (automated)
- [ ] Test backup restoration process
- [ ] Implement point-in-time recovery

### Redis Security

**Priority**: Medium

**Action Items**:
- [ ] Enable Redis authentication (requirepass)
- [ ] Use SSL/TLS for Redis connections
- [ ] Restrict Redis access to application servers
- [ ] Disable dangerous Redis commands
- [ ] Regular Redis backups if using persistence

### Server Hardening

**Priority**: High

**Action Items**:
- [ ] Keep OS and packages updated
- [ ] Configure firewall (allow only necessary ports)
- [ ] Disable unused services
- [ ] Enable automatic security updates
- [ ] Use fail2ban for brute-force protection
- [ ] Implement intrusion detection (OSSEC/Wazuh)
- [ ] Regular security audits

### Network Security

**Priority**: High

**Action Items**:
- [ ] Use VPC/private networks
- [ ] Implement network segmentation
- [ ] Use security groups/firewall rules
- [ ] Enable DDoS protection (CloudFlare/AWS Shield)
- [ ] Implement Web Application Firewall (WAF)
- [ ] Use VPN for administrative access

## Phase 4: Monitoring and Response

### Error Tracking

**Priority**: Critical  
**Timeline**: Immediate

**Action Items**:
- [ ] Integrate Sentry for error tracking
- [ ] Configure error notifications
- [ ] Set up error grouping and deduplication
- [ ] Create error severity levels
- [ ] Assign team members to error groups
- [ ] Weekly error review meetings

### Audit Logging

**Priority**: High  
**Timeline**: 2-3 weeks

**Current**: Basic logging with core/logging_config.py

**Improvements**:
```python
# Log all sensitive operations
@audit_log(action='user_login', resource_type='authentication')
def user_login(request):
    pass

@audit_log(action='data_export', resource_type='customer_data')
def export_customers(request):
    pass
```

**Action Items**:
- [ ] Log all authentication attempts
- [ ] Log all authorization failures
- [ ] Log all data modifications (CRUD)
- [ ] Log all data exports
- [ ] Log all admin actions
- [ ] Include user, IP, timestamp in all logs
- [ ] Implement log retention policy
- [ ] Set up log aggregation (ELK/Splunk)
- [ ] Create log alerting rules

### Security Monitoring

**Priority**: High  
**Timeline**: 3-4 weeks

**Action Items**:
- [ ] Set up real-time security alerts
- [ ] Monitor failed login attempts
- [ ] Detect unusual API usage patterns
- [ ] Alert on mass data exports
- [ ] Monitor for SQL injection attempts
- [ ] Track privilege escalation attempts
- [ ] Create security dashboard
- [ ] Weekly security report generation

### Incident Response

**Priority**: High  
**Timeline**: 2-3 weeks

**Action Items**:
- [ ] Create incident response plan
- [ ] Define incident severity levels
- [ ] Assign incident response team roles
- [ ] Create incident runbooks
- [ ] Set up incident communication channels
- [ ] Conduct incident response drills
- [ ] Document lessons learned

### Vulnerability Management

**Priority**: High (Ongoing)

**Action Items**:
- [x] Enable pip-audit in CI pipeline
- [ ] Set up automated dependency updates (Dependabot)
- [ ] Regular penetration testing (quarterly)
- [ ] Bug bounty program (optional)
- [ ] Subscribe to security mailing lists
- [ ] Regular code security reviews
- [ ] Third-party security audit (annually)

## Security Checklist

### Daily
- [ ] Monitor error logs
- [ ] Review security alerts
- [ ] Check for failed login attempts

### Weekly
- [ ] Review audit logs
- [ ] Check dependency vulnerabilities
- [ ] Review access logs
- [ ] Update security documentation

### Monthly
- [ ] Security scan all repositories
- [ ] Review user access permissions
- [ ] Update security policies
- [ ] Security team meeting

### Quarterly
- [ ] Rotate secrets and keys
- [ ] Penetration testing
- [ ] Security training for team
- [ ] Review and update incident response plan
- [ ] Disaster recovery drill

### Annually
- [ ] Third-party security audit
- [ ] Compliance review
- [ ] Security architecture review
- [ ] Update security roadmap

## Tools and Resources

### Recommended Tools
- **SAST**: Bandit, Semgrep
- **DAST**: OWASP ZAP
- **Dependency Scanning**: pip-audit, Safety
- **Secret Scanning**: detect-secrets, git-secrets
- **WAF**: CloudFlare, AWS WAF
- **Monitoring**: Sentry, Datadog, New Relic

### Security Standards
- OWASP Top 10
- OWASP API Security Top 10
- CWE Top 25
- NIST Cybersecurity Framework
- ISO 27001

### Training Resources
- OWASP WebGoat
- HackTheBox
- PortSwigger Web Security Academy
- Django Security Documentation

---

**Note**: This is a living document. Update as security measures are implemented and new threats emerge.

**Last Updated**: 2024-01-XX  
**Security Team Contact**: security@example.com
