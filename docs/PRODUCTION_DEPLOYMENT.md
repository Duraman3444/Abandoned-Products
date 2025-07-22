# SchoolDriver Modern - Production Deployment Guide

## Environment Variables

### Required Environment Variables

#### Security Configuration
```bash
# SECRET_KEY - Django secret key (50+ characters recommended)
DJANGO_SECRET_KEY="your-secure-50-character-secret-key-here"

# DEBUG - Set to False in production
DJANGO_DEBUG=False

# Allowed hosts - comma-separated list of allowed hostnames
DJANGO_ALLOWED_HOSTS="yourdomain.com,www.yourdomain.com"
```

#### Database Configuration
```bash
# PostgreSQL database configuration (recommended for production)
DATABASE_URL="postgresql://username:password@host:port/database_name"

# Alternative individual settings
DB_ENGINE="django.db.backends.postgresql"
DB_NAME="schooldriver_modern"
DB_USER="schooldriver_user"
DB_PASSWORD="secure_database_password"
DB_HOST="localhost"
DB_PORT="5432"
```

#### Email Configuration
```bash
# Email backend for production
EMAIL_BACKEND="django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST="smtp.your-email-provider.com"
EMAIL_PORT="587"
EMAIL_USE_TLS=True
EMAIL_HOST_USER="your-email@yourdomain.com"
EMAIL_HOST_PASSWORD="your-email-password"
EMAIL_DEFAULT_FROM="noreply@yourdomain.com"
```

#### Static File Storage
```bash
# For Google Cloud Storage (optional)
GCS_BUCKET_NAME="your-storage-bucket"
GOOGLE_APPLICATION_CREDENTIALS="/path/to/credentials.json"

# For AWS S3 (alternative)
AWS_ACCESS_KEY_ID="your-aws-access-key"
AWS_SECRET_ACCESS_KEY="your-aws-secret-key"
AWS_STORAGE_BUCKET_NAME="your-s3-bucket"
AWS_S3_REGION_NAME="us-east-1"
```

### Optional Environment Variables

#### Cache Configuration
```bash
# Redis cache (recommended for production)
CACHE_URL="redis://localhost:6379/1"
REDIS_URL="redis://localhost:6379/0"
```

#### Monitoring & Analytics
```bash
# Sentry error monitoring
SENTRY_DSN="https://your-sentry-dsn@sentry.io/project-id"

# Google Analytics
GOOGLE_ANALYTICS_ID="UA-XXXXXXXX-X"
```

#### School Configuration
```bash
# School-specific settings
SCHOOL_NAME="Your School Name"
SCHOOL_TIMEZONE="America/New_York"
SCHOOL_DOMAIN="yourschool.edu"
```

## Production Settings Configuration

### 1. Create Production Settings File

Create `schooldriver-modern/schooldriver_modern/settings_production.py`:

```python
from .settings import *
import os

# Override settings for production
DEBUG = False
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',')

# Database
if os.getenv('DATABASE_URL'):
    import dj_database_url
    DATABASES['default'] = dj_database_url.parse(os.getenv('DATABASE_URL'))

# Security settings
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# Session security
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Email configuration
if os.getenv('EMAIL_HOST'):
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.getenv('EMAIL_HOST')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
    DEFAULT_FROM_EMAIL = os.getenv('EMAIL_DEFAULT_FROM', 'noreply@example.com')

# Logging
LOGGING['handlers']['file'] = {
    'level': 'INFO',
    'class': 'logging.FileHandler',
    'filename': '/var/log/schooldriver/django.log',
    'formatter': 'verbose',
}
LOGGING['root']['handlers'].append('file')
```

### 2. Environment File Template

Create `.env.production.example`:

```bash
# Copy this file to .env.production and fill in your values
# Never commit .env.production to version control

# =============================================================================
# REQUIRED SETTINGS
# =============================================================================

# Django Core
DJANGO_SECRET_KEY=
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=

# Database
DATABASE_URL=

# =============================================================================
# OPTIONAL SETTINGS
# =============================================================================

# Email
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_DEFAULT_FROM=

# Storage (choose one)
GCS_BUCKET_NAME=
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_STORAGE_BUCKET_NAME=

# Cache
REDIS_URL=

# Monitoring
SENTRY_DSN=
GOOGLE_ANALYTICS_ID=

# School Settings
SCHOOL_NAME=
SCHOOL_TIMEZONE=America/New_York
SCHOOL_DOMAIN=
```

## Deployment Checklist

### Pre-Deployment
- [ ] Set `DEBUG = False`
- [ ] Configure production database (PostgreSQL recommended)
- [ ] Set secure `SECRET_KEY` (50+ characters)
- [ ] Configure HTTPS/SSL certificates
- [ ] Set up static file serving (CDN recommended)
- [ ] Configure email backend
- [ ] Set up error monitoring (Sentry)
- [ ] Configure backup strategy

### Security Checklist
- [ ] All environment variables secured
- [ ] Database credentials encrypted
- [ ] HTTPS enforced (`SECURE_SSL_REDIRECT = True`)
- [ ] Security headers configured
- [ ] Session security enabled
- [ ] CSRF protection active
- [ ] Input validation implemented
- [ ] Rate limiting configured

### Performance Checklist
- [ ] Database connection pooling
- [ ] Static file caching (CDN)
- [ ] Database query optimization
- [ ] Cache backend configured (Redis)
- [ ] Gzip compression enabled
- [ ] Database indexes optimized

### Monitoring Checklist
- [ ] Error logging configured
- [ ] Performance monitoring setup
- [ ] Health check endpoints
- [ ] Database backup monitoring
- [ ] Security event logging
- [ ] Uptime monitoring

## Deployment Commands

### Initial Deployment
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DJANGO_SETTINGS_MODULE=schooldriver_modern.settings_production

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser
python manage.py createsuperuser

# Load initial data
python manage.py populate_sample_data
```

### Regular Updates
```bash
# Pull latest code
git pull origin main

# Install/update dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart application server
systemctl restart schooldriver-modern
```

## Server Configuration Examples

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    location /static/ {
        alias /path/to/schooldriver-modern/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /path/to/schooldriver-modern/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Systemd Service
```ini
[Unit]
Description=SchoolDriver Modern Django App
After=network.target

[Service]
User=schooldriver
Group=schooldriver
WorkingDirectory=/path/to/schooldriver-modern
ExecStart=/path/to/venv/bin/gunicorn schooldriver_modern.wsgi:application --bind 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

## Database Migration Strategy

### Backup Strategy
```bash
# Create backup before migration
pg_dump schooldriver_modern > backup_$(date +%Y%m%d_%H%M%S).sql

# Run migrations
python manage.py migrate

# Verify data integrity
python manage.py check
```

### Zero-Downtime Deployment
1. Deploy new version alongside old version
2. Run migrations on separate database
3. Switch traffic to new version
4. Monitor for issues
5. Remove old version if stable

## Troubleshooting

### Common Issues
- **Static files not loading**: Check `STATIC_ROOT` and `collectstatic`
- **Database connection errors**: Verify `DATABASE_URL` and network access
- **SSL certificate issues**: Check certificate validity and configuration
- **Permission errors**: Verify file/directory permissions for web server user

### Logs Location
- Application logs: `/var/log/schooldriver/django.log`
- Web server logs: `/var/log/nginx/error.log`
- System logs: `journalctl -u schooldriver-modern`

### Health Check Endpoints
- `/health/` - Basic application health
- `/health/db/` - Database connectivity
- `/health/cache/` - Cache connectivity (if configured)
