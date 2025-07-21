# Original SchoolDriver Architecture (2015)

## System Overview

SchoolDriver was an open-source school information system built with Django, designed to manage the complete lifecycle of student information, admissions, work study programs, and academic records. The system was archived in 2018 due to maintenance challenges.

---

## Technology Stack

### Core Framework
- **Django 1.7.8** (Released: April 2015, EOL: April 2016)
- **Python 2.7** (Deprecated: January 1, 2020)
- **WSGI Application Server**: uWSGI 2.0.8

### Database
- **Primary**: PostgreSQL (psycopg2 2.5.4)
- **ORM**: Django 1.7 ORM
- **Migrations**: Django South (pre-1.7 migration system)

### Frontend Technologies
- **Template Engine**: Django Templates
- **JavaScript**: jQuery 1.x
- **UI Framework**: Gumby CSS Framework
- **AJAX**: django-dajax-ng 0.9.4
- **Rich Text**: CKEditor 4.4.7

### Background Processing
- **Task Queue**: Celery 3.1.17
- **Message Broker**: Redis 2.10.3
- **Background Tasks**: django-celery 3.1.16

### Deployment Environment
- **OS**: Ubuntu 12.04 LTS (EOL: April 2017)
- **Container**: Docker (basic setup)
- **Process Management**: Supervisor 3.1.3

---

## Application Architecture

### Monolithic Structure
```
schooldriver/
├── ecwsp/                    # Main application package
│   ├── sis/                 # Student Information System (Core)
│   ├── admissions/          # Admissions management
│   ├── work_study/          # Work study program
│   ├── attendance/          # Attendance tracking  
│   ├── discipline/          # Discipline management
│   ├── grades/              # Grade management
│   ├── schedule/            # Course scheduling
│   ├── alumni/              # Alumni tracking
│   ├── volunteer_track/     # Volunteer hours
│   ├── counseling/          # Student counseling
│   └── administration/      # System configuration
├── django_sis/              # Project settings
└── templates/               # HTML templates
```

### Core Business Models

#### Student Information System (ecwsp/sis/models.py)
```python
class Student(User, CustomFieldModel):
    mname = models.CharField(max_length=150, blank=True, null=True)
    grad_date = models.DateField(blank=True, null=True)
    pic = ImageWithThumbsField(upload_to="student_pics", blank=True, null=True)
    alert = models.CharField(max_length=500, blank=True)
    sex = models.CharField(max_length=1, choices=(('M', 'Male'), ('F', 'Female')))
    bday = models.DateField(blank=True, null=True)
    year = models.ForeignKey(GradeLevel, blank=True, null=True)
    unique_id = models.IntegerField(blank=True, null=True, unique=True)
    # ... many more fields
```

#### Admissions System (ecwsp/admissions/models.py)
```python
class Applicant(models.Model, CustomFieldModel):
    fname = models.CharField(max_length=255, verbose_name="First Name")
    lname = models.CharField(max_length=255, verbose_name="Last Name")
    sex = models.CharField(max_length=1, choices=(('M', 'Male'), ('F', 'Female')))
    level = models.ForeignKey(AdmissionLevel, blank=True, null=True)
    checklist = models.ManyToManyField(AdmissionCheck, blank=True, null=True)
    ready_for_export = models.BooleanField(default=False)
    # Complex admission workflow logic
```

#### Work Study System (ecwsp/work_study/models.py)
```python
class TimeSheet(models.Model):
    student = models.ForeignKey(StudentWorker)
    company = models.ForeignKey(WorkTeam)
    date = models.DateField()
    time_in = models.TimeField()
    time_lunch = models.TimeField()
    time_lunch_return = models.TimeField()
    time_out = models.TimeField()
    approved = models.BooleanField(default=False)
    supervisor_comment = models.TextField(blank=True)
    # Email workflow system with supervisor approval
```

---

## Database Design

### Primary Key Strategy
- **Integer Auto-increment**: All models used standard Django integer PKs
- **Security Risk**: Sequential, predictable IDs
- **Scalability Issues**: Limited for distributed systems

### Relationship Patterns
```python
# Legacy relationship patterns
class Student(User, CustomFieldModel):
    year = models.ForeignKey(GradeLevel, blank=True, null=True)
    emergency_contacts = models.ManyToManyField(EmergencyContact)
    cohorts = models.ManyToManyField(Cohort, through='StudentCohort')
    
# Complex through tables for relationships
class StudentCohort(models.Model):
    student = models.ForeignKey(Student)
    cohort = models.ForeignKey(Cohort) 
    primary = models.BooleanField(default=False)
```

### Data Integrity Issues
- **Nullable Foreign Keys**: Many critical relationships allowed NULL
- **No Audit Trail**: No created_at/updated_at fields
- **Missing Indexes**: Poor query performance on large datasets
- **Inconsistent Naming**: Mixed naming conventions across models

---

## User Interface Architecture

### Django Admin Customization
```python
# Heavy admin customization (sis/admin.py)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['__unicode__', 'year', 'is_active']
    list_filter = ['is_active', 'year', 'cohorts']
    search_fields = ['first_name', 'last_name', 'username']
    # Basic admin interface with minimal UX enhancements
```

### Template System
- **Server-Side Rendering**: All pages rendered server-side
- **Basic HTML**: Minimal JavaScript interaction
- **Poor Mobile Support**: Not responsive design
- **Limited AJAX**: Basic form submission only

### Workflow Management
```python
# Admission level progression (admissions/models.py)
def __set_level(self):
    prev = None
    for level in AdmissionLevel.objects.all():
        checks = level.admissioncheck_set.filter(required=True)
        i = 0
        for check in checks:
            if check in self.checklist.all():
                i += 1
        if not i >= checks.count():
            break
        prev = level
    self.level = prev
```

---

## Integration Points

### Email System
```python
# Work study supervisor email workflow
def save(self, *args, **kwargs):
    if email and self.student.primary_contact:
        try:
            sendTo = self.student.primary_contact.email
            subject = "Time Sheet for " + str(self.student)
            msg = "Please click link to approve..."
            send_mail(subject, msg, from_addr, [sendTo])
        except:
            print >> sys.stderr, "Unable to send e-mail to supervisor!"
```

### External Systems
- **SugarCRM Integration**: Customer relationship management sync
- **Naviance SSO**: College planning platform integration  
- **Engrade Sync**: Grade book synchronization
- **Canvas LMS**: Learning management system connection
- **Google Apps**: Authentication and email integration

### Reporting System
```python
# Report generation (multiple apps)
class XlReport:
    """Excel report generation"""
    def add_sheet(self, data, header_row=None):
        # Custom Excel generation system
        pass
        
class TemplateReport:
    """PDF template reports using ReportLab"""
    def pod_save(self, template):
        # Document generation from templates
        pass
```

---

## Security Architecture

### Authentication
```python
AUTHENTICATION_BACKENDS = (
    'ecwsp.sis.backends.CaseInsensitiveModelBackend',
    'ecwsp.google_auth.backends.GoogleAppsBackend',
)

# LDAP Integration
LDAP_SERVER = 'admin.example.org'
LDAP_URL = 'ldap://%s:%s' % (LDAP_SERVER, LDAP_PORT)
```

### Authorization
- **Django Permissions**: Built-in permission system
- **Group-Based Access**: Students, teachers, administrators
- **Custom Permissions**: Module-specific permissions
- **Impersonation**: Admin user impersonation feature

### Security Issues
- **Outdated Dependencies**: All packages had known vulnerabilities
- **Weak Session Management**: Django 1.7 session handling
- **CSRF Vulnerabilities**: Basic CSRF protection
- **SQL Injection Risk**: ORM protected but custom queries vulnerable

---

## Performance Characteristics

### Database Performance
```python
# N+1 Query Problems
for student in Student.objects.all():
    print(student.emergency_contacts.all())  # N+1 queries
    print(student.year.name)  # Another query per student
```

### Caching Strategy
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
# Minimal caching, mostly in-memory
```

### Background Processing
```python
# Celery task configuration
CELERYBEAT_SCHEDULE = {
    'cache-grades-nightly': {
        'task': 'ecwsp.grades.tasks.build_grade_cache_task',
        'schedule': crontab(hour=23, minute=1),
    },
}
```

---

## Deployment Architecture

### Docker Configuration
```yaml
# docker-compose.yml (Basic)
db:
  image: postgres
redis:
  image: dockerfile/redis  
web:
  build: .
  command: ./run.sh
  ports:
    - "8000:8000"
  links:
    - db
    - redis
```

### Process Management
```bash
#!/bin/bash
# run.sh - Multiple processes in one container (anti-pattern)
export C_FORCE_ROOT="true"
python manage.py celery worker -E -A django_sis -B --loglevel=INFO &
python manage.py celery flower &
supervisord -c /etc/supervisor/supervisord.conf
python manage.py runserver_plus 0.0.0.0:8000
```

---

## Configuration Management

### Settings Structure
```python
# django_sis/settings.py - Monolithic settings
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('DATABASE_NAME', 'postgres'),
        # Environment variable configuration
    }
}

INSTALLED_APPS = (
    # 30+ apps in single tuple
    'ecwsp.work_study',
    'ecwsp.engrade_sync',
    'ecwsp.benchmarks',
    # ... many more
)
```

### Multi-Tenancy
```python
# Basic multi-tenant support
MULTI_TENANT = os.getenv('MULTI_TENANT', False)
TENANT_MODEL = "customers.Client"

if MULTI_TENANT:
    INSTALLED_APPS += ('tenant_schemas',)
```

---

## System Limitations

### Technical Debt
1. **Framework Version**: Django 1.7.8 (9 years old)
2. **Python 2.7**: Deprecated language version
3. **Security Vulnerabilities**: All dependencies outdated
4. **Performance Issues**: N+1 queries, no caching strategy
5. **Mobile Incompatibility**: Not responsive design

### Business Logic Issues
1. **Complex Workflows**: Difficult to modify admission process
2. **Data Integrity**: Nullable foreign keys caused inconsistencies  
3. **Reporting Bottlenecks**: Synchronous report generation
4. **Integration Fragility**: Hardcoded external system connections
5. **User Experience**: Basic HTML forms, poor usability

### Operational Challenges
1. **Deployment Complexity**: Multiple processes in single container
2. **Monitoring Gaps**: Limited logging and error tracking
3. **Backup Strategy**: Basic database backups only
4. **Scaling Limitations**: Monolithic architecture constraints
5. **Maintenance Burden**: Outdated dependencies impossible to update

---

## Why Modernization Was Required

### Complete System Failure
```bash
# Attempting to run on modern Python
$ python3 manage.py runserver
AttributeError: module 'html.parser' has no attribute 'HTMLParseError'

# Django 1.7.8 completely incompatible with Python 3.9
# No migration path available - complete rewrite required
```

### Business Continuity Risk
- **Security Vulnerabilities**: Multiple CVEs in all dependencies
- **Compliance Issues**: FERPA requirements not met
- **Performance Degradation**: System became unusably slow
- **Integration Failures**: Third-party APIs changed, broke connections
- **Staff Productivity**: Poor UX resulted in data entry errors

### Strategic Value Loss
- **Competitive Disadvantage**: Schools moved to modern alternatives
- **Feature Gaps**: Missing mobile access, parent portals
- **Cost Escalation**: Custom maintenance became prohibitively expensive
- **Innovation Blockage**: Could not add new features on outdated platform

This legacy architecture represents a common enterprise scenario: valuable business logic trapped in an obsolete technical foundation that requires complete modernization to preserve business value. 