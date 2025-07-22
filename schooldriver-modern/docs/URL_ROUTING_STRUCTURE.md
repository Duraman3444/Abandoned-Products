# SchoolDriver Modern URL Routing Structure

## Overview
This document outlines the complete URL routing structure for SchoolDriver Modern, including public pages, authenticated portals, and administrative areas.

## Main URLs (`schooldriver_modern/urls.py`)

### Public URLs (No Authentication Required)
- `/` - Public home page
- `/about/` - About page  
- `/admissions/` - Admissions information
- `/contact/` - Contact page
- `/programs/` - Academic programs

### Authentication URLs
- `/accounts/login/` - User login
- `/accounts/signup/` - User registration
- `/accounts/logout/` - User logout
- `/accounts/password_change/` - Password change
- `/accounts/password_reset/` - Password reset

### Role-Based Portal URLs (Authentication Required)

#### Student Portal (`/student/`)
- `/student/` - Student dashboard
- `/student/grades/` - Grades view
- `/student/schedule/` - Class schedule
- `/student/attendance/` - Attendance records
- `/student/profile/` - Profile management

#### Parent Portal (`/parent/`)
- `/parent/` - Parent dashboard
- `/parent/children/` - Children overview
- `/parent/grades/<student_id>/` - Child's grades (dynamic)
- `/parent/messages/` - Teacher communications
- `/parent/profile/` - Profile management

### Administrative Areas
- `/admin/` - Django admin interface
- `/dashboard/` - General dashboard (role-based redirect)
- `/dashboard/admin/` - Administrator dashboard
- `/profile/` - User profile view
- `/profile/edit/` - Profile editing
- `/profile/password/` - Password change form

### Legacy URLs (To Be Phased Out)
- `/parent-legacy/` - Legacy parent view
- `/student-legacy/` - Legacy student view
- `/admissions-old/` - Legacy admissions URLs

### Utility URLs
- `/health/` - Health check endpoint

## App-Specific URL Configurations

### Public App (`public/urls.py`)
```python
app_name = 'public'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('admissions/', views.admissions_view, name='admissions'),
    path('contact/', views.contact_view, name='contact'),
    path('programs/', views.programs_view, name='programs'),
]
```

### Student Portal App (`student_portal/urls.py`)
```python
app_name = 'student_portal'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('grades/', views.grades_view, name='grades'),
    path('schedule/', views.schedule_view, name='schedule'),
    path('attendance/', views.attendance_view, name='attendance'),
    path('profile/', views.profile_view, name='profile'),
]
```

### Parent Portal App (`parent_portal/urls.py`)
```python
app_name = 'parent_portal'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('children/', views.children_view, name='children'),
    path('grades/<int:student_id>/', views.grades_view, name='grades'),
    path('messages/', views.messages_view, name='messages'),
    path('profile/', views.profile_view, name='profile'),
]
```

## URL Namespacing

All app-specific URLs use proper Django namespacing:

- **Public URLs**: `public:home`, `public:about`, etc.
- **Student Portal URLs**: `student_portal:dashboard`, `student_portal:grades`, etc.
- **Parent Portal URLs**: `parent_portal:dashboard`, `parent_portal:children`, etc.

## Role-Based Access Control

Views in the student and parent portals use the `@role_required` decorator to ensure proper access control:

```python
@login_required
@role_required(['student'])
def dashboard_view(request):
    # Student-only view
    pass

@login_required
@role_required(['parent'])
def dashboard_view(request):
    # Parent-only view
    pass
```

## Integration with Authentication System

The URL structure integrates with the existing authentication system in the `auth` app:

1. **Login redirects**: After login, users are redirected based on their role
2. **Permission checking**: Views use decorators to enforce role-based access
3. **Authentication flow**: Seamless integration with Django's auth system

## Template Structure

Templates should be organized to match the URL structure:

```
templates/
├── public/
│   ├── home.html
│   ├── about.html
│   ├── admissions.html
│   ├── contact.html
│   └── programs.html
├── student_portal/
│   ├── dashboard.html
│   ├── grades.html
│   ├── schedule.html
│   ├── attendance.html
│   └── profile.html
└── parent_portal/
    ├── dashboard.html
    ├── children.html
    ├── grades.html
    ├── messages.html
    └── profile.html
```

## Future Considerations

1. **API URLs**: API endpoints will be added under `/api/` prefix
2. **Mobile Apps**: Consider separate API endpoints for mobile applications
3. **Additional Roles**: Teacher and staff portals can be added following the same pattern
4. **Legacy Migration**: Gradually phase out legacy URLs as new functionality is implemented

## Usage Examples

### Template URL References
```html
<!-- Public URLs -->
<a href="{% url 'public:home' %}">Home</a>
<a href="{% url 'public:about' %}">About</a>

<!-- Student Portal URLs -->
<a href="{% url 'student_portal:dashboard' %}">Dashboard</a>
<a href="{% url 'student_portal:grades' %}">My Grades</a>

<!-- Parent Portal URLs -->
<a href="{% url 'parent_portal:dashboard' %}">Dashboard</a>
<a href="{% url 'parent_portal:grades' student.id %}">Child's Grades</a>
```

### View Redirects
```python
from django.urls import reverse
from django.shortcuts import redirect

# Redirect to student dashboard
return redirect('student_portal:dashboard')

# Redirect to specific child's grades
return redirect('parent_portal:grades', student_id=student.id)
```
