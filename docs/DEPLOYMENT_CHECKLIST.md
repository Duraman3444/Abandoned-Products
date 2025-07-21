# SchoolDriver Modern - Deployment Checklist

Use this checklist to ensure a successful production deployment of SchoolDriver Modern.

## Pre-Deployment Checklist

### 🔍 Code Quality & Testing
- [ ] All tests pass: `python manage.py test`
- [ ] Linting passes: `ruff check .`
- [ ] Code formatted: `ruff format .`
- [ ] No debug statements or print() calls in production code
- [ ] Version tagged in git: `git tag v1.0.0`

### 🛡️ Security Review
- [ ] SECRET_KEY is secure (50+ random characters)
- [ ] DEBUG=False in production settings
- [ ] ALLOWED_HOSTS configured for your domain
- [ ] No hardcoded passwords or API keys in code
- [ ] Database credentials secured
- [ ] SSL certificate obtained and configured
- [ ] CSRF and XSS protections enabled

### 📦 Dependencies & Environment
- [ ] All required packages in requirements.txt
- [ ] Python 3.12+ available on production server
- [ ] PostgreSQL 15+ installed and configured
- [ ] Redis 7+ installed and configured
- [ ] Docker and Docker Compose installed (if using containers)

### 🗄️ Database Preparation
- [ ] Production database created
- [ ] Database user created with appropriate permissions
- [ ] Database connection tested from app server
- [ ] Backup strategy planned and tested

## Deployment Steps

### 1. Server Setup
- [ ] Production server provisioned (2GB+ RAM, 20GB+ disk)
- [ ] SSH access configured with key-based authentication
- [ ] Firewall configured (ports 22, 80, 443 only)
- [ ] Non-root deployment user created
- [ ] Required system packages installed

### 2. Application Deployment

#### Option A: Docker Deployment
- [ ] Clone repository to production server
- [ ] Copy and customize `docker/docker-compose.yml`
- [ ] Set all required environment variables
- [ ] Build Docker images: `docker compose build`
- [ ] Start services: `docker compose up -d`
- [ ] Verify all containers healthy: `docker compose ps`

#### Option B: Manual Deployment
- [ ] Clone repository to production server
- [ ] Create Python virtual environment
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Configure gunicorn service
- [ ] Configure nginx reverse proxy
- [ ] Set up systemd services

### 3. Database Migration
- [ ] Run migrations: `python manage.py migrate`
- [ ] Create superuser: `python manage.py createsuperuser`
- [ ] Load initial data (if needed): `python manage.py populate_sample_data`
- [ ] Verify database tables created correctly

### 4. Static Files & Media
- [ ] Collect static files: `python manage.py collectstatic --noinput`
- [ ] Configure static file serving (nginx or whitenoise)
- [ ] Create media directory with correct permissions
- [ ] Test file uploads work correctly

### 5. Web Server Configuration
- [ ] Nginx/Apache virtual host configured
- [ ] SSL certificate installed and verified
- [ ] HTTP to HTTPS redirect enabled
- [ ] Proxy headers configured correctly
- [ ] Client max body size set appropriately

## Post-Deployment Verification

### 🧪 Smoke Tests
- [ ] Homepage loads without errors: `curl -I https://your-domain.com/`
- [ ] Admin interface accessible: `/admin/`
- [ ] Login functionality works
- [ ] Dashboard loads for authenticated users
- [ ] Static files loading (CSS, JS, images)
- [ ] File uploads work correctly

### 📊 Performance Tests
- [ ] Page load times under 2 seconds
- [ ] Database query count optimized
- [ ] Memory usage within acceptable limits
- [ ] No error logs during normal operation

### 🔧 System Integration
- [ ] Email sending works (if configured)
- [ ] Scheduled tasks running (if using Celery)
- [ ] Health check endpoint responding: `/health/`
- [ ] Error monitoring capturing issues (Sentry)
- [ ] Log files being written correctly

### 🔄 Backup Verification
- [ ] Database backup script tested
- [ ] Media files backup configured
- [ ] Backup restoration tested
- [ ] Backup retention policy configured

## Production Monitoring Setup

### 📈 Application Monitoring
- [ ] Error tracking configured (Sentry)
- [ ] Performance monitoring enabled
- [ ] Uptime monitoring configured
- [ ] Log aggregation setup (if using multiple servers)

### 🖥️ System Monitoring
- [ ] Server resource monitoring (CPU, RAM, disk)
- [ ] Database performance monitoring
- [ ] Web server access logs monitored
- [ ] SSL certificate expiration monitoring

### 🚨 Alerting
- [ ] Critical error alerts configured
- [ ] Performance degradation alerts setup
- [ ] Disk space alerts configured
- [ ] Database connection alerts enabled

## Maintenance Procedures

### 📅 Regular Tasks
- [ ] Weekly security updates scheduled
- [ ] Monthly dependency updates planned
- [ ] Quarterly backup restoration tests
- [ ] SSL certificate renewal automated

### 🔧 Emergency Procedures
- [ ] Rollback procedure documented and tested
- [ ] Emergency contact list updated
- [ ] Incident response plan documented
- [ ] Recovery time objectives defined

## Environment-Specific Configurations

### Development → Staging
- [ ] Staging environment mirrors production
- [ ] Automated deployment pipeline tested
- [ ] Integration tests pass in staging
- [ ] Performance tests completed

### Staging → Production
- [ ] Final code review completed
- [ ] Database migration plan reviewed
- [ ] Downtime window scheduled (if needed)
- [ ] Rollback plan prepared and tested

## Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| **Developer** | ________________ | __________ | ________________ |
| **DevOps** | ________________ | __________ | ________________ |
| **QA** | ________________ | __________ | ________________ |
| **Project Manager** | ________________ | __________ | ________________ |

---

## Troubleshooting Quick Reference

### Common Issues

**Service won't start**
```bash
# Check service status
systemctl status schooldriver
journalctl -u schooldriver -f

# Check application logs
tail -f /var/log/schooldriver/django.log
```

**Database connection errors**
```bash
# Test database connectivity
python manage.py dbshell
# or
psql -h localhost -U schooldriver_user -d schooldriver
```

**Static files not loading**
```bash
# Recollect static files
python manage.py collectstatic --noinput --clear

# Check nginx configuration
nginx -t
systemctl reload nginx
```

**SSL certificate issues**
```bash
# Check certificate validity
openssl x509 -in /path/to/cert.pem -text -noout

# Renew Let's Encrypt certificate
certbot renew --dry-run
```

### Emergency Contacts
- **DevOps Team**: devops@your-company.com
- **On-call Engineer**: +1-555-ON-CALL
- **Hosting Provider**: support@hosting-provider.com

---

*Save this checklist and update it based on your specific deployment experience and requirements.*
