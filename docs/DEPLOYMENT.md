# SchoolDriver Modern - Production Deployment Guide

This guide covers deploying SchoolDriver Modern to production using Docker containers with PostgreSQL and Redis.

## Prerequisites

- Docker 20.10+ and Docker Compose v2
- Production server with 2GB+ RAM
- Domain name with SSL certificate (recommended)
- PostgreSQL 15+ and Redis 7+ (if not using Docker)

## Quick Start with Docker

### 1. Clone and Build

```bash
git clone https://github.com/your-org/abandoned-products.git
cd abandoned-products
```

### 2. Configure Environment

Copy and customize the environment configuration:

```bash
cp docker/docker-compose.yml docker/docker-compose.prod.yml
```

Edit `docker/docker-compose.prod.yml` and update:
- Database passwords
- SECRET_KEY
- ALLOWED_HOSTS
- Domain-specific settings

### 3. Build and Deploy

```bash
cd docker
docker compose -f docker-compose.prod.yml up --build -d
```

### 4. Initialize Database

```bash
# Run migrations
docker compose exec web python manage.py migrate

# Create superuser
docker compose exec web python manage.py createsuperuser

# Load sample data (optional)
docker compose exec web python manage.py populate_sample_data
```

### 5. Verify Deployment

- **Web interface**: http://your-domain.com
- **Admin interface**: http://your-domain.com/admin/
- **Health check**: `docker compose ps` (all services should be "healthy")

## Production Configuration

### Database Setup (PostgreSQL)

For production, use a managed PostgreSQL service or dedicated server:

```bash
# Create database and user
sudo -u postgres psql
CREATE DATABASE schooldriver;
CREATE USER schooldriver_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE schooldriver TO schooldriver_user;
ALTER USER schooldriver_user CREATEDB;  -- For running tests
\q
```

### Static Files & Media

SchoolDriver uses Whitenoise for static files in production. For high-traffic sites, serve static files via nginx:

```nginx
# /etc/nginx/sites-available/schooldriver
server {
    listen 80;
    server_name your-domain.com;

    location /static/ {
        alias /path/to/schooldriver/staticfiles/;
        expires 30d;
    }

    location /media/ {
        alias /path/to/schooldriver/media/;
        expires 7d;
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

### Gunicorn Configuration

Create `gunicorn.conf.py` for production tuning:

```python
# gunicorn.conf.py
bind = "0.0.0.0:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 120
keepalive = 5
user = "schooldriver"
group = "schooldriver"
preload_app = True
```

Run with: `gunicorn -c gunicorn.conf.py schooldriver_modern.wsgi:application`

### SSL/HTTPS Setup

For production, always use HTTPS:

```bash
# Using Let's Encrypt with certbot
sudo certbot --nginx -d your-domain.com
```

Update Django settings:
```python
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

## Environment Variables

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `SECRET_KEY` | ✅ | Django secret key (50+ chars) | `django-prod-key-abc123...` |
| `DEBUG` | ✅ | Debug mode (False in production) | `False` |
| `ALLOWED_HOSTS` | ✅ | Comma-separated allowed hostnames | `your-domain.com,www.your-domain.com` |
| `DATABASE_URL` | ✅ | PostgreSQL connection string | `postgres://user:pass@host:5432/db` |
| `REDIS_URL` | ✅ | Redis connection for caching/sessions | `redis://localhost:6379/0` |
| `EMAIL_HOST` | ❌ | SMTP server for email notifications | `smtp.mailgun.org` |
| `EMAIL_HOST_USER` | ❌ | SMTP username | `postmaster@mg.your-domain.com` |
| `EMAIL_HOST_PASSWORD` | ❌ | SMTP password | `your-mailgun-key` |
| `AWS_ACCESS_KEY_ID` | ❌ | S3 credentials (if using S3 storage) | `AKIA...` |
| `AWS_SECRET_ACCESS_KEY` | ❌ | S3 secret key | `abc123...` |
| `AWS_STORAGE_BUCKET_NAME` | ❌ | S3 bucket for media files | `schooldriver-media` |
| `SENTRY_DSN` | ❌ | Error tracking (recommended) | `https://abc@sentry.io/123` |
| `FIREBASE_CREDENTIALS_JSON` | ❌ | Firebase service account JSON for FCM notifications | `{"type":"service_account",...}` |

### Environment File Example

Create `.env` file (never commit to git):

```bash
# .env
SECRET_KEY=your-50-character-secret-key-here-never-commit-this
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DATABASE_URL=postgres://schooldriver_user:secure_password@localhost:5432/schooldriver
REDIS_URL=redis://localhost:6379/0
EMAIL_HOST=smtp.mailgun.org
EMAIL_HOST_USER=postmaster@mg.your-domain.com
EMAIL_HOST_PASSWORD=your-mailgun-key
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
FIREBASE_CREDENTIALS_JSON={"type":"service_account","project_id":"your-project-id",...}
```

## Performance Optimization

### Database Optimization

```sql
-- PostgreSQL performance tuning
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
SELECT pg_reload_conf();
```

### Redis Configuration

```bash
# /etc/redis/redis.conf
maxmemory 128mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### Django Cache Settings

```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

## Monitoring & Logging

### Application Monitoring

```python
# settings.py - Sentry integration
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

if not DEBUG:
    sentry_sdk.init(
        dsn=os.getenv('SENTRY_DSN'),
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=True
    )
```

### System Monitoring

```bash
# Install monitoring tools
pip install psutil django-health-check

# Add to INSTALLED_APPS
INSTALLED_APPS += ['health_check', 'health_check.db', 'health_check.cache']
```

Health check endpoint: `/health/`

### Log Configuration

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/schooldriver/django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file'],
        'level': 'INFO',
    },
}
```

## Backup & Recovery

### Database Backups

```bash
# Automated backup script
#!/bin/bash
# /etc/cron.daily/backup-schooldriver
BACKUP_DIR="/backup/schooldriver"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
pg_dump -h localhost -U schooldriver_user schooldriver | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Keep last 30 days
find $BACKUP_DIR -name "db_*.sql.gz" -mtime +30 -delete
```

### Media Files Backup

```bash
# Sync to S3 or backup server
rsync -av /path/to/media/ backup-server:/backup/schooldriver/media/
```

## Scaling Considerations

### Horizontal Scaling

- Use load balancer (nginx, HAProxy, or cloud LB)
- Run multiple gunicorn instances
- Shared PostgreSQL and Redis instances
- Shared media storage (S3, NFS)

### Vertical Scaling

- 2GB RAM minimum, 4GB+ recommended
- 2 CPU cores minimum
- SSD storage for database
- Monitor with `htop`, `iotop`, `pg_stat_activity`

## Troubleshooting

### Common Issues

**Permission Errors**
```bash
# Fix file permissions
sudo chown -R www-data:www-data /path/to/schooldriver/
sudo chmod -R 755 /path/to/schooldriver/
```

**Database Connection Issues**
```bash
# Test PostgreSQL connection
psql -h localhost -U schooldriver_user -d schooldriver -c "SELECT version();"
```

**Static Files Not Loading**
```bash
# Collect static files
python manage.py collectstatic --noinput --clear
```

**Memory Issues**
```bash
# Monitor memory usage
free -h
sudo systemctl status schooldriver
```

### Performance Debugging

```bash
# Django debug toolbar (development only)
pip install django-debug-toolbar

# Query analysis
python manage.py shell
from django.db import connection
print(connection.queries)
```

## Security Checklist

- [ ] SECRET_KEY is secure and not in version control
- [ ] DEBUG=False in production
- [ ] ALLOWED_HOSTS configured correctly
- [ ] HTTPS enabled with valid SSL certificate
- [ ] Database credentials secured
- [ ] Regular security updates applied
- [ ] Firewall configured (only 80, 443, SSH open)
- [ ] Backup strategy tested and verified
- [ ] Error monitoring configured (Sentry)
- [ ] Log rotation configured

---

For additional support, see the [Deployment Checklist](DEPLOYMENT_CHECKLIST.md) or contact the development team.
