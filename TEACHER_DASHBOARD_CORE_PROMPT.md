# AI Coding Prompt: Teachers/Staff Dashboard Core Infrastructure

## Context
You are building the core infrastructure for a Teachers/Staff Dashboard in the SchoolDriver Modern system, a Django 4.2 K-12 school information system. This modernizes a legacy Django 1.7 system with proper authentication, role-based access, and teacher-focused functionality.

## Project Structure Overview
```
schooldriver-modern/
├── schooldriver_modern/         # Main project settings
│   ├── roles.py                # Existing role-based access system  
│   ├── auth_views.py           # Custom authentication views
│   └── portal_middleware.py    # Portal access control
├── authentication/             # Authentication decorators
├── academics/                  # Course, sections, assignments models
├── students/                   # Student and grade level models
├── templates/                  # HTML templates
└── static/                     # CSS, JS, images
```

## Existing System Components

### Authentication & Roles
- **Role System**: `UserRoles.ADMIN`, `UserRoles.STAFF`, `UserRoles.PARENT`, `UserRoles.STUDENT`
- **Permission Decorators**: `@role_required(['Staff', 'Admin'])` available
- **Portal Middleware**: Restricts access to `/teacher/` URLs to Staff/Admin users
- **User Groups**: Django groups for role management already implemented

### Academic Models (Already Implemented)
```python
# From academics/models.py
class Department(models.Model):
    name, description, head (User FK), is_active

class Course(models.Model):  
    name, course_code, department, credit_hours, prerequisites

class CourseSection(models.Model):
    course, school_year, section_name, teacher (User FK), room, max_students
    # Key: teacher field links User to CourseSection

class Enrollment(models.Model):
    student, section, enrollment_date, is_active, final_grade

class Assignment(models.Model):
    section, category, name, due_date, max_points, is_published

class Schedule(models.Model):
    section, day_of_week, start_time, end_time, room
```

## Requirements: Teachers/Staff Dashboard Core Infrastructure

### 1. Teacher Authentication & Role-Based Access ✅ (Use Existing)
**Implementation Notes:**
- Authentication system is already complete
- Use `@role_required(['Staff', 'Admin'])` decorator on views
- Portal middleware will restrict `/teacher/` URLs to appropriate users
- User role detection via `get_user_role(user)` function

### 2. Class/Section Assignment & Permissions ⭐ **BUILD THIS**
**Requirements:**
- Display teacher's assigned CourseSection objects via `teacher` foreign key
- Show course details: course name, section, room, student count, schedule
- Handle teachers with multiple sections efficiently
- Create permissions system for section-specific data access

### 3. Multi-Class Support for Teachers ⭐ **BUILD THIS**  
**Requirements:**
- Dashboard navigation between different sections
- Section-specific grade entry and attendance
- Quick section switcher in navigation
- Context awareness (current section selection)

### 4. Academic Year & Term Management ⭐ **BUILD THIS**
**Requirements:**
- Filter sections by active SchoolYear 
- Show current academic year prominently
- Handle year transitions gracefully
- Archive/hide inactive year data

### 5. Basic Navigation & Layout Structure ⭐ **BUILD THIS**
**Requirements:**
- Professional teacher-focused UI design
- Responsive Bootstrap 5 layout
- Quick access to: Grade entry, Attendance, Assignments, Reports
- Role indicator showing "Staff" badge
- Breadcrumb navigation for multi-level pages

## Implementation Tasks

### Task 1: Create Teacher Portal URL Structure
Create `teacher_portal/` Django app with URL routing:
```
/teacher/                     # Teacher dashboard home
/teacher/section/<int:id>/    # Section-specific views  
/teacher/gradebook/<int:id>/  # Grade management
/teacher/attendance/<int:id>/ # Attendance tracking
/teacher/assignments/<int:id>/ # Assignment management
```

### Task 2: Build Teacher Dashboard Views
**Create views in `teacher_portal/views.py`:**

```python
from authentication.decorators import role_required
from academics.models import CourseSection, Enrollment
from students.models import SchoolYear

@role_required(['Staff', 'Admin'])
def teacher_dashboard(request):
    """Main teacher dashboard showing assigned sections"""
    # Get current school year
    # Get teacher's sections: CourseSection.objects.filter(teacher=request.user)
    # Calculate enrollment counts, recent assignments
    # Return dashboard with section summary cards

@role_required(['Staff', 'Admin'])  
def section_detail(request, section_id):
    """Detailed view of specific course section"""
    # Verify teacher owns this section or is admin
    # Get section with related course, enrollments, assignments
    # Show student roster, recent grades, upcoming assignments
```

### Task 3: Implement Section Permission System
**Create permission utilities in `teacher_portal/permissions.py`:**

```python
def user_can_access_section(user, section_id):
    """Check if user can access specific section"""
    # Admin can access all sections
    # Staff can only access sections they teach
    # Return True/False with helpful error messages

def get_teacher_sections(user, school_year=None):
    """Get sections this teacher can access"""
    # Filter by current school year if not specified
    # Include enrollment counts, schedules
    # Order by course code, section name
```

### Task 4: Build Academic Year Management
**Create year management in `teacher_portal/utils.py`:**

```python
def get_current_school_year():
    """Get active school year with caching"""
    
def get_teacher_year_context(user):
    """Get year context for teacher views"""
    # Current year, available years, section counts per year
```

### Task 5: Create Teacher Dashboard Templates
**Templates in `teacher_portal/templates/teacher_portal/`:**

1. **`dashboard.html`** - Main dashboard with section cards
2. **`section_detail.html`** - Individual section management
3. **`base_teacher.html`** - Teacher-specific base template
4. **`partials/section_card.html`** - Reusable section summary card
5. **`partials/navigation.html`** - Teacher navigation sidebar

### Task 6: Dashboard UI Design Requirements
**Visual Design Specifications:**
- **Header**: School logo, teacher name, role badge ("Staff"), logout
- **Sidebar Navigation**: Dashboard, My Sections, Gradebook, Attendance, Reports
- **Main Content**: Section cards grid (3 columns on desktop)
- **Section Cards**: Course name, section, room, student count, quick actions
- **Colors**: Professional blue/gray theme matching existing design
- **Responsive**: Mobile-friendly navigation (collapsed sidebar)

### Task 7: Multi-Section Context Management
**Implementation Requirements:**
- **Session Storage**: Remember last selected section per teacher
- **URL Parameters**: Support `?section=123` for deep linking
- **Navigation**: Section switcher dropdown in header
- **Breadcrumbs**: "Dashboard > Math 101-A > Gradebook" navigation

## Technical Requirements

### Database Queries (Performance)
- Use `select_related()` for course, department, school_year joins
- Use `prefetch_related()` for enrollments, assignments
- Cache teacher sections list (5 minute timeout)
- Optimize for teachers with 6+ sections

### Security & Permissions
- All views require `@role_required(['Staff', 'Admin'])` decorator
- Verify section ownership on all section-specific views
- Validate section_id parameters exist and are accessible
- Log unauthorized access attempts

### Error Handling
- Graceful handling of missing sections, inactive school years
- User-friendly error messages for permission denials
- Fallback to dashboard if section not found
- Loading states for slow database queries

### Testing Requirements
- Unit tests for permission functions
- Integration tests for dashboard views
- Test teacher with 0, 1, and 6+ sections
- Test admin access to all sections
- Test inactive school year handling

## Success Criteria

### Functional Requirements ✅
- [ ] Teachers can log in and see only their assigned sections
- [ ] Section cards show accurate enrollment counts and schedules  
- [ ] Multi-section teachers can navigate between sections efficiently
- [ ] Academic year filtering works correctly
- [ ] Admin users can access all sections
- [ ] Responsive design works on mobile devices

### Performance Requirements ✅
- [ ] Dashboard loads in < 300ms for teachers with 6 sections
- [ ] Database queries optimized (max 5 queries per dashboard load)
- [ ] Section switching feels instant (cached data)

### Security Requirements ✅
- [ ] Teachers cannot access other teachers' sections
- [ ] All URLs properly protected with role decorators
- [ ] Permission system prevents data leakage
- [ ] Admin access logging implemented

## Implementation Notes

### Don't Over-Engineer
- Use existing authentication system (don't rebuild)
- Leverage Django's built-in session framework
- Keep templates simple and maintainable
- Focus on core functionality first

### Code Quality
- Follow existing project patterns and naming conventions
- Add comprehensive docstrings to new functions
- Use type hints for complex functions
- Write tests for permission logic

### Future Considerations
- Design URLs to accommodate gradebook and attendance features
- Plan for assignment creation workflow
- Consider parent communication integration
- Design for potential mobile app API consumption

---

**Next Steps After Completion:**
1. Grade Management System (Priority 1)
2. Attendance Tracking (Priority 1) 
3. Assignment & Curriculum Management (Priority 2)
4. Communication Tools (Priority 2)

This foundation will support all subsequent teacher dashboard features. Focus on getting the core infrastructure solid before adding advanced functionality. 