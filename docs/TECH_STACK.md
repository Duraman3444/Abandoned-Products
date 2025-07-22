# SchoolDriver Modern – Technical Stack Overview
_A concise guide to every major technology powering the application_

---

## 1. Languages

| Layer | Language | Why we use it |
|-------|----------|---------------|
| Backend | **Python 3.11** | High-productivity, huge ecosystem, first-class Django support |
| Front-end templating | **Django Templates (HTML + Jinja-style tags)** | Server-side rendering keeps pages fast without a SPA |
| Styling | **CSS / SCSS** | Custom dark-theme variables + small Tailwind snippets |
| Client-side widgets | **JavaScript (ES 6)** | Chart rendering & interactive helpers |
| SQL | **PostgreSQL dialect** | Advanced aggregates, JSON fields, and indexing |

---

## 2. Core Frameworks & Libraries

| Area | Library | Purpose |
|------|---------|---------|
| Web Framework | **Django 4.x** | URL routing, ORM, auth, admin |
| UI Framework | **Bootstrap 5 + Bootstrap-Icons** | Responsive grid, cards, modals, icon set |
| Utility CSS | **Tailwind (CDN)** | Quick spacing / colour tweaks |
| Charts | **Chart.js 4** | Dashboard visualisations |
| Auth Helpers | `django-allauth` (optional) | Social login, email verification |
| Testing | **pytest-django**, **factory-boy** | Fast unit & integration tests |

---

## 3. Data & Persistence

| Environment | Store | Notes |
|-------------|-------|-------|
| Dev / CI | **SQLite 3** | Zero-config for contributors |
| Prod | **PostgreSQL 13+** | Relational data + JSONB |
| File Storage | **AWS S3** via `django-storages` | User uploads & static assets |
| Caching / Broker | **Redis** (optional) | Sessions, Celery tasks |

---

## 4. Messaging / Notifications

| Tool | Role |
|------|------|
| **Firebase Cloud Messaging (FCM)** | Push notifications to mobile & web clients |
| Django **messages** framework | Flash alerts inside the UI |

---

## 5. Dev-Ops & Runtime

| Component | Image / Service | What it does |
|-----------|-----------------|--------------|
| **Docker** | Multi-stage build (`python:3.11-slim`) | Reproducible deployments |
| **Docker-Compose** | Local stack (`web`, `db`, `redis`) | One-command dev up-spin |
| **Gunicorn** | WSGI process manager | Runs Django in production |
| **nginx** | Reverse-proxy & static file cache | Terminates TLS if needed |
| **GitHub Actions** | CI pipeline | Lint, tests, Docker build |
| **Sentry** (optional) | Error aggregation | Drop-in via DSN env var |

---

## 6. Security & Compliance

| Feature | Library / Practice |
|---------|--------------------|
| Password hashing | `PBKDF2 + pepper` via Django defaults |
| Rate-limiting | `django-axes` (optional) |
| CSP headers | Enabled in `settings.security` |
| Secrets | Docker secrets / environment vars – **never** committed |

---

## 7. Development Conveniences

| Tool | Why we like it |
|------|---------------|
| **pip-tools / poetry** | Deterministic dependency locking |
| **django-extensions** | Shell Plus, model graphing |
| **pre-commit** | Black, isort, flake8 on every commit |
| **django-debug-toolbar** | SQL & template profiling in dev |

---

## 8. Local Setup Quick-start

```bash
# 1 · Clone
git clone git@github.com:your-org/schooldriver-modern.git
cd schooldriver-modern

# 2 · Build stack
docker-compose up --build  # web, db, redis

# 3 · Create superuser
docker-compose exec web python manage.py createsuperuser

# 4 · 🎉  Visit http://localhost:8000
```

---

## 9. Legacy vs Modern
Legacy tree (`schooldriver/`) ships Angular 1, jQuery-UI, >200 Django models.
Modern focuses on a slimmer Django-only backend + Bootstrap 5 dark-theme, reducing JS dependencies to a single Chart.js file.

---

## 10. Future Considerations

| Idea | Benefit |
|------|---------|
| Celery + Redis | Async email, long-running exports |
| Compiled Tailwind | Purge unused CSS → <20 KB bundle |
| Adopt **HTMX** | Rich interactivity without a SPA |
| Terraform IaC | Version-controlled cloud infra |

---

_Last updated: 2025-07-22_ 