# SchoolDriver Modern: Student Portal Navigation Fix Prompt

## Problem Analysis
The Student Portal has broken navigation where buttons and links don't lead to their intended destinations:

1. **Grades Button**: Doesn't navigate to grades page
2. **Schedule Button**: Doesn't navigate to schedule page  
3. **Attendance Button**: Doesn't navigate to attendance page
4. **My Profile Button**: Doesn't navigate to profile page
5. **SchoolDriver Modern Logo**: Should return to home page but doesn't work properly

## Required Fixes

### 1. Fix Student Portal URL Patterns
**File: `schooldriver-modern/student_portal/urls.py`**

Ensure all required URL patterns exist:

```python
from django.urls import path
from . import views

app_name = 'student_portal'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('grades/', views.grades_view, name='grades'),
    path('schedule/', views.schedule_view, name='schedule'),
    path('attendance/', views.attendance_view, name='attendance'),
    path('profile/', views.profile_view, name='profile'),
    path('assignments/', views.assignments_view, name='assignments'),
    path('messages/', views.messages_view, name='messages'),
]
```

### 2. Create Missing View Functions
**File: `schooldriver-modern/student_portal/views.py`**

Add all the missing view functions:

```python
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from authentication.decorators import role_required

@login_required
@role_required(['Student'])
def grades_view(request):
    """Student grades and academic performance"""
    try:
        # Mock student grades data
        courses_with_grades = [
            {
                'name': 'Mathematics',
                'teacher': 'Mr. Johnson',
                'current_grade': 'A-',
                'percentage': 88.5,
                'assignments': [
                    {'name': 'Quiz 1', 'grade': 92, 'date': '2024-09-15', 'points': '23/25'},
                    {'name': 'Homework Set 1', 'grade': 87, 'date': '2024-09-20', 'points': '17.4/20'},
                    {'name': 'Test 1', 'grade': 85, 'date': '2024-09-25', 'points': '85/100'},
                ]
            },
            {
                'name': 'English Literature',
                'teacher': 'Ms. Davis', 
                'current_grade': 'B+',
                'percentage': 86.2,
                'assignments': [
                    {'name': 'Essay 1', 'grade': 88, 'date': '2024-09-18', 'points': '44/50'},
                    {'name': 'Reading Quiz', 'grade': 82, 'date': '2024-09-22', 'points': '16.4/20'},
                    {'name': 'Discussion Posts', 'grade': 90, 'date': '2024-09-28', 'points': '18/20'},
                ]
            },
            # Add more courses...
        ]
        
        context = {
            'courses_with_grades': courses_with_grades,
            'overall_gpa': 3.7,
            'semester': 'Fall 2024'
        }
        
    except Exception as e:
        messages.error(request, f"Unable to load grades: {e}")
        context = {'error': 'Unable to load grades at this time.'}
    
    return render(request, 'student_portal/grades.html', context)

@login_required
@role_required(['Student'])
def schedule_view(request):
    """Student class schedule"""
    try:
        # Mock schedule data
        schedule_data = [
            {'period': '1st', 'time': '8:00 AM - 8:50 AM', 'subject': 'Mathematics', 'teacher': 'Mr. Johnson', 'room': '101'},
            {'period': '2nd', 'time': '9:00 AM - 9:50 AM', 'subject': 'English Literature', 'teacher': 'Ms. Davis', 'room': '205'},
            {'period': '3rd', 'time': '10:00 AM - 10:50 AM', 'subject': 'Science', 'teacher': 'Dr. Wilson', 'room': '302'},
            {'period': '4th', 'time': '11:00 AM - 11:50 AM', 'subject': 'Social Studies', 'teacher': 'Mr. Rodriguez', 'room': '150'},
            {'period': '5th', 'time': '1:00 PM - 1:50 PM', 'subject': 'Art', 'teacher': 'Ms. Chen', 'room': '210'},
            {'period': '6th', 'time': '2:00 PM - 2:50 PM', 'subject': 'Physical Education', 'teacher': 'Coach Smith', 'room': 'Gym'},
        ]
        
        context = {
            'schedule_data': schedule_data,
            'semester': 'Fall 2024'
        }
        
    except Exception as e:
        messages.error(request, f"Unable to load schedule: {e}")
        context = {'error': 'Unable to load schedule at this time.'}
    
    return render(request, 'student_portal/schedule.html', context)

@login_required
@role_required(['Student'])
def attendance_view(request):
    """Student attendance records"""
    try:
        # Mock attendance data
        attendance_records = []
        from datetime import date, timedelta
        
        start_date = date(2024, 8, 15)
        for i in range(30):  # Last 30 school days
            current_date = start_date + timedelta(days=i)
            if current_date.weekday() < 5:  # Weekdays only
                status = 'Present'
                if i % 12 == 0:
                    status = 'Absent'
                elif i % 8 == 0:
                    status = 'Tardy'
                
                attendance_records.append({
                    'date': current_date,
                    'status': status,
                    'notes': 'Doctor appointment' if status == 'Absent' and i % 24 == 0 else ''
                })
        
        attendance_summary = {
            'total_days': len(attendance_records),
            'present': len([r for r in attendance_records if r['status'] == 'Present']),
            'absent': len([r for r in attendance_records if r['status'] == 'Absent']),
            'tardy': len([r for r in attendance_records if r['status'] == 'Tardy']),
        }
        attendance_summary['percentage'] = round((attendance_summary['present'] / attendance_summary['total_days']) * 100, 1)
        
        context = {
            'attendance_records': attendance_records[:10],  # Show last 10 days
            'attendance_summary': attendance_summary,
            'semester': 'Fall 2024'
        }
        
    except Exception as e:
        messages.error(request, f"Unable to load attendance: {e}")
        context = {'error': 'Unable to load attendance at this time.'}
    
    return render(request, 'student_portal/attendance.html', context)

@login_required
@role_required(['Student'])
def profile_view(request):
    """Student profile management"""
    try:
        student = request.user.student_profile if hasattr(request.user, 'student_profile') else None
        
        context = {
            'student': student,
            'user': request.user,
        }
        
    except Exception as e:
        messages.error(request, f"Unable to load profile: {e}")
        context = {'error': 'Unable to load profile at this time.'}
    
    return render(request, 'student_portal/profile.html', context)

@login_required
@role_required(['Student'])
def assignments_view(request):
    """Student assignments and homework"""
    try:
        # Mock assignments data
        upcoming_assignments = [
            {
                'course': 'Mathematics',
                'title': 'Algebra Quiz',
                'due_date': timezone.now() + timedelta(days=2),
                'description': 'Quiz covering Chapter 5: Linear Equations'
            },
            {
                'course': 'English Literature',
                'title': 'Character Analysis Essay',
                'due_date': timezone.now() + timedelta(days=5),
                'description': 'Write a 2-page essay analyzing the main character'
            }
        ]
        
        context = {
            'upcoming_assignments': upcoming_assignments,
        }
        
    except Exception as e:
        messages.error(request, f"Unable to load assignments: {e}")
        context = {'error': 'Unable to load assignments at this time.'}
    
    return render(request, 'student_portal/assignments.html', context)

@login_required
@role_required(['Student'])
def messages_view(request):
    """Student messages and announcements"""
    try:
        # Mock messages data
        messages_data = [
            {
                'from': 'Mr. Johnson (Mathematics)',
                'subject': 'Great progress!',
                'message': 'You are showing excellent progress in algebra.',
                'date': timezone.now() - timedelta(days=1),
                'read': False
            },
            {
                'from': 'School Office',
                'subject': 'Reminder: Picture Day',
                'message': 'Picture day is scheduled for next Friday.',
                'date': timezone.now() - timedelta(days=2),
                'read': True
            }
        ]
        
        context = {
            'messages_data': messages_data,
        }
        
    except Exception as e:
        messages.error(request, f"Unable to load messages: {e}")
        context = {'error': 'Unable to load messages at this time.'}
    
    return render(request, 'student_portal/messages.html', context)
```

### 3. Fix Navigation Links in Student Portal Template
**File: `schooldriver-modern/student_portal/templates/student_portal/dashboard.html`**

Update all navigation buttons to use proper URL patterns:

```html
<!-- Student Menu Navigation -->
<div class="col-md-3">
    <div class="card">
        <div class="card-header">
            <h5 class="card-title mb-0">Student Menu</h5>
        </div>
        <div class="list-group list-group-flush">
            <a href="{% url 'student_portal:dashboard' %}" class="list-group-item list-group-item-action {% if request.resolver_match.url_name == 'dashboard' %}active{% endif %}">
                <i class="bi bi-speedometer2 me-2"></i>Dashboard
            </a>
            <a href="{% url 'student_portal:grades' %}" class="list-group-item list-group-item-action {% if request.resolver_match.url_name == 'grades' %}active{% endif %}">
                <i class="bi bi-bar-chart me-2"></i>Grades
            </a>
            <a href="{% url 'student_portal:schedule' %}" class="list-group-item list-group-item-action {% if request.resolver_match.url_name == 'schedule' %}active{% endif %}">
                <i class="bi bi-calendar3 me-2"></i>Schedule
            </a>
            <a href="{% url 'student_portal:attendance' %}" class="list-group-item list-group-item-action {% if request.resolver_match.url_name == 'attendance' %}active{% endif %}">
                <i class="bi bi-check2-circle me-2"></i>Attendance
            </a>
            <a href="{% url 'student_portal:profile' %}" class="list-group-item list-group-item-action {% if request.resolver_match.url_name == 'profile' %}active{% endif %}">
                <i class="bi bi-person me-2"></i>My Profile
            </a>
        </div>
    </div>
</div>
```

### 4. Fix Logo/Brand Navigation in Base Template
**File: `schooldriver-modern/templates/base.html`**

Update the navbar brand section to properly route students back to their dashboard:

```html
{% if user.is_authenticated %}
    {% get_user_role user as user_role %}
    {% if user_role == 'Student' %}
        <a class="navbar-brand fw-bold" href="{% url 'student_portal:dashboard' %}">
            <i class="bi bi-mortarboard-fill me-2"></i>SchoolDriver Modern
        </a>
    {% elif user_role == 'Parent' %}
        <a class="navbar-brand fw-bold" href="{% url 'parent_portal:dashboard' %}">
            <i class="bi bi-mortarboard-fill me-2"></i>SchoolDriver Modern
        </a>
    {% elif user_role == 'Admin' or user_role == 'Staff' %}
        <a class="navbar-brand fw-bold" href="{% url 'dashboard' %}">
            <i class="bi bi-mortarboard-fill me-2"></i>SchoolDriver Modern
        </a>
    {% else %}
        <a class="navbar-brand fw-bold" href="{% url 'public:home' %}">
            <i class="bi bi-mortarboard-fill me-2"></i>SchoolDriver Modern
        </a>
    {% endif %}
{% else %}
    <a class="navbar-brand fw-bold" href="{% url 'public:home' %}">
        <i class="bi bi-mortarboard-fill me-2"></i>SchoolDriver Modern
    </a>
{% endif %}
```

### 5. Create Missing Template Files

Create these template files in `schooldriver-modern/student_portal/templates/student_portal/`:

#### `grades.html`
```html
{% extends "student_base.html" %}
{% load static %}

{% block title %}Grades - Student Portal{% endblock %}

{% block content %}
<div class="container-fluid">
    <div class="row">
        <div class="col-12">
            <h2 class="mb-4">My Grades</h2>
            
            {% if error %}
                <div class="alert alert-danger">{{ error }}</div>
            {% else %}
                <div class="row">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-header">
                                <h5 class="card-title mb-0">Current Semester: {{ semester }}</h5>
                                <small class="text-muted">Overall GPA: {{ overall_gpa }}</small>
                            </div>
                            <div class="card-body">
                                {% for course in courses_with_grades %}
                                <div class="course-section mb-4">
                                    <h6>{{ course.name }} - {{ course.teacher }}</h6>
                                    <div class="grade-summary mb-3">
                                        <span class="badge bg-primary">{{ course.current_grade }}</span>
                                        <span class="text-muted">{{ course.percentage }}%</span>
                                    </div>
                                    
                                    <div class="table-responsive">
                                        <table class="table table-sm">
                                            <thead>
                                                <tr>
                                                    <th>Assignment</th>
                                                    <th>Date</th>
                                                    <th>Points</th>
                                                    <th>Grade</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                {% for assignment in course.assignments %}
                                                <tr>
                                                    <td>{{ assignment.name }}</td>
                                                    <td>{{ assignment.date }}</td>
                                                    <td>{{ assignment.points }}</td>
                                                    <td>
                                                        <span class="badge {% if assignment.grade >= 90 %}bg-success{% elif assignment.grade >= 80 %}bg-primary{% elif assignment.grade >= 70 %}bg-warning{% else %}bg-danger{% endif %}">
                                                            {{ assignment.grade }}%
                                                        </span>
                                                    </td>
                                                </tr>
                                                {% endfor %}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                                {% endfor %}
                            </div>
                        </div>
                    </div>
                </div>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}
```

#### `schedule.html`, `attendance.html`, `profile.html`
Similar template structure for each page with appropriate content.

### 6. Update Main URLs Configuration
**File: `schooldriver-modern/schooldriver_modern/urls.py`**

Ensure student portal URLs are included:

```python
from django.urls import path, include

urlpatterns = [
    # ... existing patterns ...
    path('student/', include('student_portal.urls')),
    # ... other patterns ...
]
```

### 7. Fix Student Base Template Navigation
**File: `schooldriver-modern/templates/student_base.html`**

Ensure all navigation links work properly:

```html
<div class="student-sidebar">
    <nav class="nav flex-column">
        <a class="nav-link {% if request.resolver_match.url_name == 'dashboard' %}active{% endif %}" 
           href="{% url 'student_portal:dashboard' %}">
            <i class="bi bi-speedometer2 me-2"></i>Dashboard
        </a>
        <a class="nav-link {% if request.resolver_match.url_name == 'grades' %}active{% endif %}" 
           href="{% url 'student_portal:grades' %}">
            <i class="bi bi-bar-chart me-2"></i>Grades
        </a>
        <a class="nav-link {% if request.resolver_match.url_name == 'schedule' %}active{% endif %}" 
           href="{% url 'student_portal:schedule' %}">
            <i class="bi bi-calendar3 me-2"></i>Schedule
        </a>
        <a class="nav-link {% if request.resolver_match.url_name == 'attendance' %}active{% endif %}" 
           href="{% url 'student_portal:attendance' %}">
            <i class="bi bi-check2-circle me-2"></i>Attendance
        </a>
        <a class="nav-link {% if request.resolver_match.url_name == 'profile' %}active{% endif %}" 
           href="{% url 'student_portal:profile' %}">
            <i class="bi bi-person me-2"></i>My Profile
        </a>
    </nav>
</div>
```

## Implementation Priority

1. **CRITICAL**: Create missing URL patterns and views
2. **HIGH**: Fix navigation links in templates  
3. **HIGH**: Fix logo/brand navigation
4. **MEDIUM**: Create missing template files
5. **LOW**: Add styling and active state indicators

## Testing Checklist

After implementation, verify:
- [ ] Grades button navigates to working grades page
- [ ] Schedule button navigates to working schedule page
- [ ] Attendance button navigates to working attendance page
- [ ] My Profile button navigates to working profile page
- [ ] SchoolDriver Modern logo returns to appropriate home page
- [ ] All navigation shows active states correctly
- [ ] No 404 errors when clicking any navigation element
- [ ] Back button works correctly between pages

## Notes

- Ensure all view functions have proper authentication decorators
- Add proper error handling for missing student data
- Consider adding breadcrumb navigation for better UX
- Test navigation flow from both authenticated and unauthenticated states 