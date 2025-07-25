from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Avg
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import HttpResponse, JsonResponse
from django.template.loader import get_template
from datetime import timedelta, date
from authentication.decorators import role_required
from students.models import Student, SchoolYear, ParentVerificationCode, EmergencyContact, AuthorizedPickupPerson, MedicalInformation
from academics.models import Enrollment, Grade, Assignment, Attendance, CourseSection, EarlyDismissalRequest, SchoolCalendarEvent, Message, MessageAttachment
from .forms import (
    ParentRegistrationForm, VerificationCodeForm, ParentAccountLinkForm, 
    VerificationRequestForm, EarlyDismissalRequestForm, MessageForm, MessageReplyForm,
    EmergencyContactForm, AuthorizedPickupPersonForm, MedicalInformationForm
)
from .profile_forms import ParentProfileForm
import logging

# PDF generation imports
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
from io import BytesIO

logger = logging.getLogger(__name__)


# Parent Registration and Verification Views

def parent_register_view(request):
    """Parent account registration with verification code"""
    if request.user.is_authenticated:
        return redirect('parent_portal:dashboard')
    
    if request.method == 'POST':
        form = ParentRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                messages.success(
                    request, 
                    f"Welcome! Your account has been created and linked to {form._verification.student.full_name}."
                )
                return redirect('parent_portal:dashboard')
            except Exception as e:
                logger.error(f"Error creating parent account: {e}")
                messages.error(request, "There was an error creating your account. Please try again.")
    else:
        form = ParentRegistrationForm()
    
    return render(request, 'parent_portal/register.html', {'form': form})


def verification_code_view(request):
    """Standalone verification code entry for account linking"""
    if not request.user.is_authenticated:
        return redirect('parent_portal:register')
    
    if request.method == 'POST':
        form = VerificationCodeForm(request.POST)
        if form.is_valid():
            verification = form._verification
            success = verification.use_code(request.user)
            if success:
                messages.success(
                    request,
                    f"Successfully linked {verification.student.full_name} to your account!"
                )
                return redirect('parent_portal:dashboard')
            else:
                messages.error(request, "Failed to link student to your account.")
    else:
        form = VerificationCodeForm()
    
    return render(request, 'parent_portal/verify_code.html', {'form': form})


def request_verification_view(request):
    """Allow parents to request verification codes (for admin approval)"""
    if request.method == 'POST':
        form = VerificationRequestForm(request.POST)
        if form.is_valid():
            # In a real implementation, this would create a request for admin approval
            # For now, we'll just show a success message
            messages.success(
                request,
                "Your verification request has been submitted. The school office will contact you "
                "with your verification code within 1-2 business days."
            )
            return redirect('login')
    else:
        form = VerificationRequestForm()
    
    return render(request, 'parent_portal/request_verification.html', {'form': form})


# Helper function to get parent's children
def get_parent_children(user):
    """Get all students associated with the current parent user via family_access_users."""
    try:
        # Use the secure family_access_users relationship
        children = user.accessible_students.filter(is_active=True).select_related(
            "grade_level"
        ).prefetch_related("emergency_contacts")
        
        return children
    except Exception as e:
        logger.error(f"Error finding children for parent {user.username}: {e}")
        return Student.objects.none()


def get_current_child(user, request):
    """Get the currently selected child for the parent, with proper access verification."""
    try:
        children = get_parent_children(user)
        
        if not children.exists():
            return None, children
        
        # Check if a specific child is requested
        child_id = request.GET.get('child')
        if child_id:
            try:
                current_child = children.get(id=child_id)
                return current_child, children
            except (Student.DoesNotExist, ValueError):
                # Invalid child ID or parent doesn't have access
                pass
        
        # Default to first child
        return children.first(), children
        
    except Exception as e:
        logger.error(f"Error getting current child for parent {user.username}: {e}")
        return None, Student.objects.none()


def verify_parent_access(user, student):
    """Verify that the parent has access to view this student's information."""
    parent_children = get_parent_children(user)
    return student in parent_children


@login_required
@role_required(["Parent"])
def dashboard_view(request):
    """Parent dashboard showing overview of current child or all children"""
    try:
        current_child, children = get_current_child(request.user, request)
        
        if not children.exists():
            messages.warning(
                request,
                "No student records found for your account. Please contact the school office.",
            )
            return render(
                request, "parent_portal/dashboard.html", {"error": "No children found"}
            )

        # Get current school year
        current_school_year = SchoolYear.objects.filter(is_active=True).first()

        # If we have a current child selected, show detailed view for that child
        if current_child:
            # Use centralized academic data function for consistency with student portal
            from student_portal.views import get_student_academic_data
            academic_data = get_student_academic_data(current_child)
            
            current_gpa = academic_data["gpa_data"]["gpa4"]
            course_grades = []
            
            # Convert academic data format to parent portal format
            for course in academic_data["current_courses"]:
                course_grades.append({
                    'course': course['name'],
                    'teacher': course['teacher'],
                    'grade': course['current_grade'],
                    'percentage': course['percentage']
                })
            
            enrollments = academic_data["enrollments"]
            attendance_summary = academic_data["attendance_summary"]

            # Get recent grades (last 5 graded assignments)
            recent_grades = Grade.objects.filter(
                enrollment__student=current_child,
                enrollment__section__school_year=current_school_year,
                points_earned__isnull=False,
                is_excused=False
            ).select_related(
                'assignment__section__course', 'assignment'
            ).order_by('-graded_date', '-created_at')[:5]
            
            recent_grades_data = []
            for grade in recent_grades:
                recent_grades_data.append({
                    'course': grade.assignment.section.course.name,
                    'assignment': grade.assignment.name,
                    'points_earned': grade.points_earned,
                    'max_points': grade.assignment.max_points,
                    'percentage': round(grade.percentage, 1) if grade.percentage else None,
                    'letter_grade': grade.letter_grade,
                    'date': grade.graded_date or grade.created_at
                })

            # Get upcoming assignments (next 7 days)
            upcoming_assignments = Assignment.objects.filter(
                section__enrollments__student=current_child,
                section__school_year=current_school_year,
                due_date__gte=timezone.now().date(),
                due_date__lte=timezone.now().date() + timedelta(days=7),
                is_published=True
            ).select_related('section__course').order_by('due_date', 'due_time')[:10]
            
            upcoming_assignments_data = []
            for assignment in upcoming_assignments:
                # Check if student has submitted or has grade
                has_grade = Grade.objects.filter(
                    enrollment__student=current_child,
                    assignment=assignment
                ).exists()
                
                upcoming_assignments_data.append({
                    'course': assignment.section.course.name,
                    'title': assignment.name,
                    'due_date': assignment.due_date,
                    'due_time': assignment.due_time,
                    'max_points': assignment.max_points,
                    'is_overdue': assignment.is_overdue,
                    'has_grade': has_grade,
                    'category': assignment.category.name
                })

            # Get comprehensive attendance data for current child
            # Today's attendance status
            today = timezone.now().date()
            today_attendance = Attendance.objects.filter(
                enrollment__student=current_child,
                enrollment__section__school_year=current_school_year,
                date=today
            ).first()
            
            # Recent attendance (last 10 days)
            recent_attendance = Attendance.objects.filter(
                enrollment__student=current_child,
                enrollment__section__school_year=current_school_year,
                date__gte=today - timedelta(days=10),
                date__lte=today
            ).order_by('-date')[:10]
            
            # Get attendance patterns (using centralized attendance_summary from above)
            attendance_patterns = {}
            if enrollments.exists():
                enrollment = enrollments.first()
                attendance_patterns = Attendance.get_attendance_patterns(enrollment, days=30)
                
            # Get class schedule for today
            today_schedule = []
            weekdays = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT', 'SUN']
            today_weekday = weekdays[today.weekday()]
            
            for enrollment in enrollments:
                schedules = enrollment.section.schedules.filter(
                    day_of_week=today_weekday,
                    is_active=True
                ).order_by('start_time')
                
                for schedule in schedules:
                    today_schedule.append({
                        'course': enrollment.section.course.name,
                        'teacher': enrollment.section.teacher.get_full_name(),
                        'start_time': schedule.start_time,
                        'end_time': schedule.end_time,
                        'room': schedule.room,
                    })
            
            # Sort schedule by start time
            today_schedule.sort(key=lambda x: x['start_time'])
            
            # Get school calendar events
            upcoming_events = SchoolCalendarEvent.get_upcoming_events(days=14, school_year=current_school_year)
            
            # Filter events that affect this student
            relevant_events = []
            for event in upcoming_events:
                if event.affects_student(current_child):
                    relevant_events.append(event)
            
            # Get today's events
            today_events = SchoolCalendarEvent.objects.filter(
                school_year=current_school_year,
                is_public=True,
                start_date__lte=today,
                end_date__gte=today
            )
            
            # Filter today's events for this student
            relevant_today_events = []
            for event in today_events:
                if event.affects_student(current_child):
                    relevant_today_events.append(event)

        # Combined view for families with multiple children
        children_summary = []
        for child in children:
            # Use centralized academic data function for each child
            child_academic_data = get_student_academic_data(child)
            
            # Get most recent activity
            recent_grade = Grade.objects.filter(
                enrollment__student=child,
                enrollment__section__school_year=current_school_year
            ).order_by('-graded_date', '-created_at').first()
            
            if recent_grade and recent_grade.graded_date:
                last_activity = recent_grade.graded_date.strftime('%b %d')
            else:
                last_activity = "No recent activity"
            
            children_summary.append({
                "student": child,
                "current_gpa": child_academic_data["gpa_data"]["gpa4"],
                "attendance_rate": child_academic_data["attendance_summary"]["attendance_rate"],
                "recent_activity": f"Last grade: {last_activity}"
            })

        # Get real school announcements for parents
        from academics.models import Announcement
        announcements = Announcement.objects.filter(
            is_published=True,
            audience__in=['ALL', 'PARENTS'],
            publish_date__lte=timezone.now()
        ).exclude(
            expire_date__lt=timezone.now()
        ).order_by('-priority', '-publish_date')[:10]

        context = {
            "current_child": current_child,
            "children": children,
            "children_summary": children_summary,
            "current_school_year": current_school_year,
            "announcements": announcements,
            "total_children": children.count(),
        }
        
        # Add current child specific data if selected
        if current_child:
            context.update({
                "current_gpa": current_gpa,
                "recent_grades": recent_grades_data,
                "upcoming_assignments": upcoming_assignments_data,
                "course_grades": course_grades,
                # Attendance data
                "today_attendance": today_attendance,
                "recent_attendance": recent_attendance,
                "attendance_summary": attendance_summary,
                "attendance_patterns": attendance_patterns,
                # Schedule data
                "today_schedule": today_schedule,
                "today_date": today,
                # Calendar events
                "upcoming_events": relevant_events[:5],  # Show next 5 events
                "today_events": relevant_today_events,
            })

    except Exception as e:
        logger.error(f"Error loading parent dashboard: {e}")
        context = {"error": "Unable to load dashboard data at this time."}

    return render(request, "parent_portal/dashboard.html", context)


@login_required
@role_required(["Parent"])
def attendance_view(request):
    """Detailed attendance view with calendar and patterns"""
    try:
        current_child, children = get_current_child(request.user, request)
        
        if not current_child:
            messages.warning(request, "Please select a child to view attendance details.")
            return redirect('parent_portal:dashboard')
        
        # Get current school year
        current_school_year = SchoolYear.objects.filter(is_active=True).first()
        
        # Get all enrollments for the student
        enrollments = Enrollment.objects.filter(
            student=current_child,
            section__school_year=current_school_year,
            is_active=True
        )
        
        if not enrollments.exists():
            context = {'error': 'No enrollment records found for this student.'}
            return render(request, "parent_portal/attendance.html", context)
        
        # Get attendance records for the school year
        enrollment = enrollments.first()  # Use first enrollment for attendance data
        attendance_records = Attendance.objects.filter(
            enrollment=enrollment
        ).order_by('-date')
        
        # Get attendance summary
        attendance_summary = Attendance.get_attendance_summary(enrollment)
        
        # Get attendance patterns
        attendance_patterns = Attendance.get_attendance_patterns(enrollment, days=60)
        
        # Group attendance by month for calendar view
        from datetime import datetime
        import calendar
        
        monthly_attendance = {}
        for record in attendance_records:
            month_key = record.date.strftime("%Y-%m")
            if month_key not in monthly_attendance:
                monthly_attendance[month_key] = []
            monthly_attendance[month_key].append(record)
        
        # Get absence reasons summary
        absence_reasons = {}
        absent_records = attendance_records.filter(status__in=['A', 'E'], absence_reason__isnull=False)
        for record in absent_records:
            reason_name = record.absence_reason.name
            if reason_name not in absence_reasons:
                absence_reasons[reason_name] = {'count': 0, 'is_excused': record.absence_reason.is_excused}
            absence_reasons[reason_name]['count'] += 1
        
        # Recent attendance notifications
        recent_notifications = attendance_records.filter(
            parent_notified=True,
            parent_notified_at__isnull=False
        ).order_by('-parent_notified_at')[:10]
        
        context = {
            'current_child': current_child,
            'children': children,
            'attendance_records': attendance_records[:50],  # Latest 50 records
            'attendance_summary': attendance_summary,
            'attendance_patterns': attendance_patterns,
            'monthly_attendance': monthly_attendance,
            'absence_reasons': absence_reasons,
            'recent_notifications': recent_notifications,
            'current_school_year': current_school_year,
        }
        
    except Exception as e:
        logger.error(f"Error loading attendance view: {e}")
        context = {"error": "Unable to load attendance data at this time."}
    
    return render(request, "parent_portal/attendance.html", context)


@login_required
@role_required(["Parent"])
def early_dismissal_request_view(request):
    """View for parents to request early dismissal for their child"""
    try:
        current_child, children = get_current_child(request.user, request)
        
        if not current_child:
            messages.warning(request, "Please select a child to request early dismissal.")
            return redirect('parent_portal:dashboard')
        
        if request.method == 'POST':
            form = EarlyDismissalRequestForm(
                request.POST, 
                student=current_child, 
                user=request.user
            )
            if form.is_valid():
                dismissal_request = form.save()
                messages.success(
                    request, 
                    f"Early dismissal request submitted for {current_child.display_name} on {dismissal_request.request_date}. "
                    "You will be notified when the request is processed."
                )
                return redirect('parent_portal:attendance_current')
        else:
            form = EarlyDismissalRequestForm(student=current_child, user=request.user)
        
        # Get existing requests for this student
        existing_requests = EarlyDismissalRequest.objects.filter(
            student=current_child,
            requested_by=request.user
        ).order_by('-created_at')[:10]
        
        context = {
            'form': form,
            'current_child': current_child,
            'children': children,
            'existing_requests': existing_requests,
        }
        
    except Exception as e:
        logger.error(f"Error in early dismissal request view: {e}")
        messages.error(request, "Unable to process request at this time.")
        context = {"error": "Unable to load dismissal request form."}
    
    return render(request, "parent_portal/early_dismissal_request.html", context)


@login_required
@role_required(["Parent"])
def conference_scheduling_view(request):
    """View available conference slots and book appointments"""
    try:
        current_child, children = get_current_child(request.user, request)
        
        if not current_child:
            return render(request, "parent_portal/conference_scheduling.html", {
                "error": "Please select a child to view conference scheduling.",
                "children": children,
            })
        
        # Get teachers for the current child
        from academics.models import ConferenceSlot, Enrollment
        from django.db.models import Q
        
        # Get current child's teachers
        enrollments = Enrollment.objects.filter(
            student=current_child,
            course__school_year__is_active=True
        ).select_related('course__teacher')
        
        teachers = [enrollment.course.teacher for enrollment in enrollments if enrollment.course.teacher]
        
        # Get available conference slots for these teachers
        available_slots = ConferenceSlot.objects.filter(
            teacher__in=teachers,
            status='AVAILABLE',
            date__gte=timezone.now().date()
        ).select_related('teacher').order_by('date', 'start_time')
        
        # Get booked conferences for current user
        booked_conferences = ConferenceSlot.objects.filter(
            booked_by=request.user,
            student=current_child
        ).select_related('teacher').order_by('date', 'start_time')
        
        # Handle booking
        if request.method == "POST":
            slot_id = request.POST.get('slot_id')
            parent_notes = request.POST.get('parent_notes', '')
            
            try:
                slot = ConferenceSlot.objects.get(id=slot_id)
                slot.book_for_parent(request.user, current_child, parent_notes)
                messages.success(request, f"Conference booked successfully with {slot.teacher.get_full_name()} on {slot.date} at {slot.start_time}")
                return redirect('parent_portal:conference_scheduling')
            except ConferenceSlot.DoesNotExist:
                messages.error(request, "Conference slot not found.")
            except ValueError as e:
                messages.error(request, str(e))
        
        context = {
            "current_child": current_child,
            "children": children,
            "available_slots": available_slots,
            "booked_conferences": booked_conferences,
            "teachers": teachers,
        }
        
        return render(request, "parent_portal/conference_scheduling.html", context)
        
    except Exception as e:
        return render(request, "parent_portal/conference_scheduling.html", {
            "error": f"Error loading conference scheduling: {str(e)}",
            "children": children if 'children' in locals() else [],
        })


@login_required
@role_required(["Parent"])
def school_calendar_view(request):
    """School calendar view with events and holidays"""
    try:
        current_child, children = get_current_child(request.user, request)
        
        # Get current school year
        current_school_year = SchoolYear.objects.filter(is_active=True).first()
        
        # Get month and year from request, default to current
        from datetime import datetime
        today = datetime.now()
        month = int(request.GET.get('month', today.month))
        year = int(request.GET.get('year', today.year))
        
        # Get events for the month
        month_events = SchoolCalendarEvent.get_events_for_month(year, month, current_school_year)
        
        # Filter events for current child if one is selected
        if current_child:
            filtered_events = []
            for event in month_events:
                if event.affects_student(current_child):
                    filtered_events.append(event)
            month_events = filtered_events
        
        # Get upcoming events (next 30 days)
        upcoming_events = SchoolCalendarEvent.get_upcoming_events(days=30, school_year=current_school_year)
        
        # Filter upcoming events for current child
        if current_child:
            filtered_upcoming = []
            for event in upcoming_events:
                if event.affects_student(current_child):
                    filtered_upcoming.append(event)
            upcoming_events = filtered_upcoming
        
        # Generate calendar data
        import calendar
        cal = calendar.monthcalendar(year, month)
        
        # Create a dictionary to map dates to events
        events_by_date = {}
        for event in month_events:
            # Handle multi-day events
            current_date = event.start_date
            while current_date <= event.end_date:
                if current_date.month == month and current_date.year == year:
                    if current_date not in events_by_date:
                        events_by_date[current_date] = []
                    events_by_date[current_date].append(event)
                current_date += timedelta(days=1)
        
        # Month navigation
        if month == 1:
            prev_month, prev_year = 12, year - 1
        else:
            prev_month, prev_year = month - 1, year
            
        if month == 12:
            next_month, next_year = 1, year + 1
        else:
            next_month, next_year = month + 1, year
        
        context = {
            'current_child': current_child,
            'children': children,
            'current_school_year': current_school_year,
            'calendar_data': cal,
            'events_by_date': events_by_date,
            'upcoming_events': upcoming_events[:10],
            'current_month': month,
            'current_year': year,
            'month_name': calendar.month_name[month],
            'prev_month': prev_month,
            'prev_year': prev_year,
            'next_month': next_month,
            'next_year': next_year,
            'today': today.date(),
        }
        
    except Exception as e:
        logger.error(f"Error loading school calendar: {e}")
        context = {"error": "Unable to load school calendar at this time."}
    
    return render(request, "parent_portal/school_calendar.html", context)


@login_required
@role_required(["Parent"])
def children_view(request):
    """Parent children overview with detailed academic information"""
    try:
        children = get_parent_children(request.user)

        if not children.exists():
            messages.warning(request, "No student records found.")
            return redirect("parent_portal:dashboard")

        children_details = []
        for child in children:
            # Mock detailed academic information
            courses = [
                {
                    "name": "Mathematics",
                    "teacher": "Mr. Johnson",
                    "grade": "A-",
                    "percentage": 88.5,
                },
                {
                    "name": "English Literature",
                    "teacher": "Ms. Davis",
                    "grade": "B+",
                    "percentage": 86.2,
                },
                {
                    "name": "Science",
                    "teacher": "Dr. Wilson",
                    "grade": "A",
                    "percentage": 92.1,
                },
                {
                    "name": "Social Studies",
                    "teacher": "Mr. Rodriguez",
                    "grade": "B",
                    "percentage": 83.7,
                },
                {
                    "name": "Art",
                    "teacher": "Ms. Chen",
                    "grade": "A",
                    "percentage": 95.0,
                },
            ]

            # Calculate overall GPA
            total_points = sum(course["percentage"] for course in courses)
            gpa = total_points / len(courses) if courses else 0

            # Mock attendance data
            attendance_summary = {
                "total_days": 45,
                "present": 42,
                "absent": 2,
                "tardy": 1,
                "percentage": 93.3,
            }

            # Get emergency contacts
            emergency_contacts = child.emergency_contacts.all().order_by(
                "is_primary", "relationship"
            )

            children_details.append(
                {
                    "student": child,
                    "courses": courses,
                    "gpa": round(gpa, 2),
                    "attendance": attendance_summary,
                    "emergency_contacts": emergency_contacts,
                    "age": child.get_age(),
                }
            )

        context = {
            "children_details": children_details,
        }

    except Exception as e:
        logger.error(f"Error loading children overview: {e}")
        context = {"error": "Unable to load children information at this time."}

    return render(request, "parent_portal/children.html", context)


@login_required
@role_required(["Parent"])
def child_detail_view(request, student_id=None):
    """Individual child detail view with comprehensive academic information"""
    try:
        # If no student_id provided, use the current child selection
        if student_id is None:
            current_child, children = get_current_child(request.user, request)
            if not current_child:
                messages.warning(request, "Please select a child to view details.")
                return redirect("parent_portal:dashboard")
            student = current_child
        else:
            student = get_object_or_404(Student, id=student_id)
            # Verify parent has access to this student
            if not verify_parent_access(request.user, student):
                messages.error(
                    request, "You don't have permission to view this student's information."
                )
                return redirect("parent_portal:dashboard")
        
        # Get all children for the template context
        _, children = get_current_child(request.user, request)

        # Mock detailed course information
        courses_with_grades = [
            {
                "name": "Mathematics",
                "teacher": "Mr. Johnson",
                "period": "1st Period",
                "room": "Room 101",
                "current_grade": "A-",
                "percentage": 88.5,
                "assignments": [
                    {
                        "name": "Quiz 1",
                        "grade": 92,
                        "date": "2024-09-15",
                        "category": "Quiz",
                    },
                    {
                        "name": "Homework Set 1",
                        "grade": 87,
                        "date": "2024-09-20",
                        "category": "Homework",
                    },
                    {
                        "name": "Test 1",
                        "grade": 85,
                        "date": "2024-09-25",
                        "category": "Test",
                    },
                ],
            },
            {
                "name": "English Literature",
                "teacher": "Ms. Davis",
                "period": "2nd Period",
                "room": "Room 205",
                "current_grade": "B+",
                "percentage": 86.2,
                "assignments": [
                    {
                        "name": "Essay 1",
                        "grade": 88,
                        "date": "2024-09-18",
                        "category": "Essay",
                    },
                    {
                        "name": "Reading Quiz",
                        "grade": 82,
                        "date": "2024-09-22",
                        "category": "Quiz",
                    },
                    {
                        "name": "Discussion Posts",
                        "grade": 90,
                        "date": "2024-09-28",
                        "category": "Participation",
                    },
                ],
            },
        ]

        # Mock attendance records
        attendance_records = []
        start_date = date(2024, 8, 15)
        current_date = start_date

        for i in range(30):  # Last 30 school days
            if current_date.weekday() < 5:
                status = "Present"
                if i % 12 == 0:
                    status = "Absent"
                elif i % 8 == 0:
                    status = "Tardy"

                attendance_records.append(
                    {
                        "date": current_date,
                        "status": status,
                        "notes": "Doctor appointment"
                        if status == "Absent" and i % 24 == 0
                        else "",
                    }
                )
            current_date += timedelta(days=1)

        attendance_records.reverse()  # Most recent first

        # Mock upcoming assignments
        upcoming_assignments = [
            {
                "course": "Mathematics",
                "title": "Algebra Quiz",
                "due_date": timezone.now() + timedelta(days=2),
                "description": "Quiz covering Chapter 5: Linear Equations",
            },
            {
                "course": "English Literature",
                "title": "Character Analysis Essay",
                "due_date": timezone.now() + timedelta(days=5),
                "description": "Write a 2-page essay analyzing the main character",
            },
        ]

        context = {
            "student": student,
            "current_child": student,
            "children": children,
            "courses_with_grades": courses_with_grades,
            "attendance_records": attendance_records[:10],  # Show last 10 days
            "upcoming_assignments": upcoming_assignments,
            "total_attendance_days": len(attendance_records),
            "present_days": len(
                [r for r in attendance_records if r["status"] == "Present"]
            ),
        }

    except Exception as e:
        logger.error(f"Error loading child detail: {e}")
        context = {"error": "Unable to load student information at this time."}

    return render(request, "parent_portal/child_detail.html", context)


@login_required
@role_required(["Parent"])
def grades_view(request, student_id=None):
    """Child's detailed grades view"""
    try:
        # If no student_id provided, use the current child selection
        if student_id is None:
            current_child, children = get_current_child(request.user, request)
            if not current_child:
                messages.warning(request, "Please select a child to view grades.")
                return redirect("parent_portal:dashboard")
            student = current_child
        else:
            student = get_object_or_404(Student, id=student_id)
            # Verify parent has access to this student
            if not verify_parent_access(request.user, student):
                messages.error(
                    request, "You don't have permission to view this student's information."
                )
                return redirect("parent_portal:dashboard")
        
        # Get all children for the template context
        _, children = get_current_child(request.user, request)

        # Get real detailed grade data with assignment breakdown
        enrollments = Enrollment.objects.filter(
            student=student,
            section__school_year__is_active=True,
            is_active=True
        ).select_related(
            'section__course', 'section__teacher'
        ).prefetch_related(
            'grades__assignment__category',
            'grades__assignment'
        )
        
        courses_with_grades = []
        
        for enrollment in enrollments:
            # Get all grades for this enrollment
            grades = enrollment.grades.filter(
                is_excused=False
            ).select_related('assignment__category').order_by('-assignment__due_date')
            
            assignments_data = []
            for grade in grades:
                assignments_data.append({
                    'name': grade.assignment.name,
                    'grade': grade.points_earned,
                    'max_points': grade.assignment.max_points,
                    'percentage': round(grade.percentage, 1) if grade.percentage else None,
                    'letter_grade': grade.letter_grade,
                    'date': grade.graded_date or grade.created_at,
                    'category': grade.assignment.category.name,
                    'weight': grade.assignment.weight,
                    'is_late': grade.is_late,
                    'comments': grade.comments,
                })
            
            # Calculate current grade
            calculated_grade = enrollment.calculate_grade()
            current_percentage = round(calculated_grade, 1) if calculated_grade else None
            current_letter = enrollment.get_letter_grade(calculated_grade) if calculated_grade else "N/A"
            
            courses_with_grades.append({
                'name': enrollment.section.course.name,
                'course_code': enrollment.section.course.course_code,
                'teacher': enrollment.section.teacher.get_full_name(),
                'credit_hours': enrollment.section.course.credit_hours,
                'current_grade': current_letter,
                'percentage': current_percentage,
                'assignments': assignments_data,
                'section': enrollment.section.section_name,
            })

        # Calculate overall statistics
        total_points = 0
        total_credits = 0
        
        for course in courses_with_grades:
            if course["percentage"] is not None:
                # Convert percentage to GPA points
                letter = course["current_grade"]
                grade_points = {
                    'A+': 4.0, 'A': 4.0, 'A-': 3.7,
                    'B+': 3.3, 'B': 3.0, 'B-': 2.7,
                    'C+': 2.3, 'C': 2.0, 'C-': 1.7,
                    'D+': 1.3, 'D': 1.0, 'D-': 0.7,
                    'F': 0.0
                }.get(letter, 0.0)
                
                total_points += grade_points * float(course["credit_hours"])
                total_credits += float(course["credit_hours"])
        
        overall_gpa = round(total_points / total_credits, 2) if total_credits > 0 else 0.0

        # Calculate grade trends based on actual grades over time
        from datetime import datetime, timedelta
        from django.db.models import Avg
        
        # Get grades from the last 8 weeks
        eight_weeks_ago = timezone.now().date() - timedelta(weeks=8)
        recent_grades = Grade.objects.filter(
            enrollment__student=student,
            enrollment__section__school_year__is_active=True,
            graded_date__gte=eight_weeks_ago,
            points_earned__isnull=False,
            is_excused=False
        ).order_by('graded_date')
        
        # Group grades by week and calculate averages
        grade_trends = []
        if recent_grades.exists():
            current_date = eight_weeks_ago
            week_count = 1
            
            while current_date <= timezone.now().date() and week_count <= 8:
                week_end = current_date + timedelta(days=6)
                week_grades = recent_grades.filter(
                    graded_date__gte=current_date,
                    graded_date__lte=week_end
                )
                
                if week_grades.exists():
                    avg_percentage = week_grades.aggregate(
                        avg=Avg('percentage')
                    )['avg']
                    grade_trends.append({
                        "week": f"Week {week_count}",
                        "average": round(avg_percentage, 1) if avg_percentage else None
                    })
                
                current_date = week_end + timedelta(days=1)
                week_count += 1
        
        # Find missing assignments (assignments without grades)
        missing_assignments = []
        for enrollment in enrollments:
            # Get assignments that don't have grades yet
            assignments_with_no_grades = Assignment.objects.filter(
                section=enrollment.section,
                is_published=True,
                due_date__lte=timezone.now().date()
            ).exclude(
                grades__enrollment=enrollment
            ).select_related('section__course')
            
            for assignment in assignments_with_no_grades:
                missing_assignments.append({
                    'course': assignment.section.course.name,
                    'title': assignment.name,
                    'due_date': assignment.due_date,
                    'days_overdue': (timezone.now().date() - assignment.due_date).days,
                    'max_points': assignment.max_points,
                    'category': assignment.category.name,
                })

        context = {
            "student": student,
            "current_child": student,
            "children": children,
            "courses_with_grades": courses_with_grades,
            "overall_gpa": round(overall_gpa, 2),
            "grade_trends": grade_trends,
            "missing_assignments": missing_assignments,
            "semester": "Fall 2024",
        }

    except Exception as e:
        logger.error(f"Error loading child grades: {e}")
        context = {"error": "Unable to load grade information at this time."}

    return render(request, "parent_portal/grades.html", context)


@login_required
@role_required(["Parent"])
def messages_view(request):
    """Enhanced teacher messaging with threads, attachments, and read receipts"""
    try:
        current_child, children = get_current_child(request.user, request)
        
        # Get filter parameter from URL
        filter_type = request.GET.get('filter', '').lower()
        
        # Get message threads (group by thread_id)
        from django.db.models import Q, Max
        
        # Get all messages involving this parent
        all_messages = Message.objects.filter(
            Q(sender=request.user) | Q(recipient=request.user)
        ).select_related('sender', 'recipient', 'student_context').prefetch_related('attachments')
        
        # Group messages by thread_id
        threads = {}
        for message in all_messages:
            thread_id = message.thread_id
            if not thread_id:
                # Create a thread ID for messages without one
                import uuid
                thread_id = str(uuid.uuid4())[:12]
                message.thread_id = thread_id
                message.save()
            
            if thread_id not in threads:
                threads[thread_id] = []
            threads[thread_id].append(message)
        
        # Create thread summaries
        thread_data = []
        for thread_id, messages in threads.items():
            # Sort messages in thread by date
            messages.sort(key=lambda x: x.sent_at)
            latest_message = messages[-1]
            
            # Check if user has unread messages in this thread
            unread_count = sum(1 for msg in messages if msg.recipient == request.user and not msg.is_read)
            has_urgent = any(msg.is_urgent and msg.recipient == request.user and not msg.is_read for msg in messages)
            
            # Get participants (excluding current user)
            participants = set()
            for msg in messages:
                if msg.sender != request.user:
                    participants.add(msg.sender)
                if msg.recipient != request.user:
                    participants.add(msg.recipient)
            
            thread_data.append({
                'thread_id': thread_id,
                'subject': latest_message.subject,
                'latest_message': latest_message,
                'messages': messages,
                'message_count': len(messages),
                'unread_count': unread_count,
                'has_urgent': has_urgent,
                'participants': list(participants),
                'student_context': latest_message.student_context,
                'has_attachments': any(msg.attachments.exists() for msg in messages)
            })
        
        # Sort threads by latest message date
        thread_data.sort(key=lambda x: x['latest_message'].sent_at, reverse=True)
        
        # Apply filters
        if filter_type == 'unread':
            thread_data = [thread for thread in thread_data if thread['unread_count'] > 0]
        elif filter_type == 'urgent':
            thread_data = [thread for thread in thread_data if thread['has_urgent']]
        
        # Paginate threads
        paginator = Paginator(thread_data, 10)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        
        # Count total unread messages
        total_unread = Message.objects.filter(recipient=request.user, is_read=False).count()
        total_urgent = Message.objects.filter(recipient=request.user, is_read=False, is_urgent=True).count()
        
        context = {
            "current_child": current_child,
            "children": children,
            "page_obj": page_obj,
            "total_unread": total_unread,
            "total_urgent": total_urgent,
            "current_filter": filter_type,
        }
        
    except Exception as e:
        logger.error(f"Error loading parent messages: {e}")
        context = {"error": "Unable to load messages at this time."}

    return render(request, "parent_portal/messages.html", context)


@login_required
@role_required(["Parent"])
def mark_all_read_view(request):
    """Mark all messages as read for the current parent"""
    if request.method == 'POST':
        try:
            updated_count = Message.objects.filter(
                recipient=request.user,
                is_read=False
            ).update(is_read=True, read_at=timezone.now())
            
            return JsonResponse({
                'success': True,
                'message': f'Marked {updated_count} messages as read.'
            })
        except Exception as e:
            logger.error(f"Error marking messages as read: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Unable to mark messages as read.'
            })
    
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})


@login_required
@role_required(["Parent"])
def compose_message_view(request):
    """Compose new message to teachers"""
    try:
        current_child, children = get_current_child(request.user, request)
        
        # Get available teachers (teachers of this parent's children)
        teacher_ids = set()
        for child in children:
            enrollments = Enrollment.objects.filter(
                student=child,
                section__school_year__is_active=True,
                is_active=True
            ).select_related('section__teacher')
            
            for enrollment in enrollments:
                if enrollment.section.teacher:
                    teacher_ids.add(enrollment.section.teacher.id)
        
        available_teachers = User.objects.filter(id__in=teacher_ids)
        
        if request.method == 'POST':
            form = MessageForm(
                request.POST, 
                request.FILES,
                sender=request.user,
                available_recipients=available_teachers,
                student_context_options=children
            )
            if form.is_valid():
                message = form.save()
                messages.success(request, f"Message sent to {message.recipient.get_full_name()}!")
                return redirect('parent_portal:messages')
        else:
            form = MessageForm(
                sender=request.user,
                available_recipients=available_teachers,
                student_context_options=children
            )
        
        context = {
            'form': form,
            'current_child': current_child,
            'children': children,
            'available_teachers': available_teachers,
        }
        
    except Exception as e:
        logger.error(f"Error in compose message view: {e}")
        messages.error(request, "Unable to load compose form at this time.")
        context = {"error": "Unable to load compose form."}
    
    return render(request, "parent_portal/compose_message.html", context)


@login_required
@role_required(["Parent"])
def message_thread_view(request, thread_id):
    """View individual message thread with reply functionality"""
    try:
        # Get current child and children for sidebar context
        current_child, children = get_current_child(request.user, request)
        # Get all messages in thread
        thread_messages = Message.objects.filter(
            thread_id=thread_id
        ).filter(
            Q(sender=request.user) | Q(recipient=request.user)
        ).select_related('sender', 'recipient', 'student_context').prefetch_related('attachments').order_by('sent_at')
        
        if not thread_messages.exists():
            messages.error(request, "Message thread not found.")
            return redirect('parent_portal:messages')
        
        # Mark unread messages as read
        unread_messages = thread_messages.filter(recipient=request.user, is_read=False)
        for message in unread_messages:
            message.mark_as_read()
        
        # Get the original message for context
        original_message = thread_messages.first()
        
        # Handle reply form
        if request.method == 'POST':
            form = MessageReplyForm(
                request.POST,
                request.FILES,
                sender=request.user,
                original_message=original_message
            )
            if form.is_valid():
                reply = form.save()
                messages.success(request, "Reply sent!")
                return redirect('parent_portal:message_thread', thread_id=thread_id)
        else:
            form = MessageReplyForm(
                sender=request.user,
                original_message=original_message
            )
        
        context = {
            'thread_messages': thread_messages,
            'thread_id': thread_id,
            'original_message': original_message,
            'form': form,
            'current_child': current_child,
            'children': children,
        }
        
    except Exception as e:
        logger.error(f"Error loading message thread: {e}")
        messages.error(request, "Unable to load message thread.")
        context = {"error": "Unable to load message thread."}
    
    return render(request, "parent_portal/message_thread.html", context)


@login_required
@role_required(["Parent"])
def download_attachment_view(request, attachment_id):
    """Download message attachment"""
    try:
        attachment = get_object_or_404(MessageAttachment, id=attachment_id)
        
        # Verify access - user must be sender or recipient of the message
        if request.user not in [attachment.message.sender, attachment.message.recipient]:
            messages.error(request, "You don't have permission to download this file.")
            return redirect('parent_portal:messages')
        
        # Record download
        attachment.record_download()
        
        # Serve file
        response = HttpResponse(attachment.file.read(), content_type=attachment.content_type)
        response['Content-Disposition'] = f'attachment; filename="{attachment.original_filename}"'
        response['Content-Length'] = attachment.file_size
        
        return response
        
    except Exception as e:
        logger.error(f"Error downloading attachment: {e}")
        messages.error(request, "Unable to download file.")
        return redirect('parent_portal:messages')


@login_required
@role_required(["Parent"])
def profile_view(request):
    """Parent profile management with language preference support"""
    try:
        children = get_parent_children(request.user)
        
        # Get or create user profile and notification preferences
        from schooldriver_modern.models import UserProfile, NotificationPreferences
        profile, created = UserProfile.objects.get_or_create(user=request.user)
        notification_prefs, prefs_created = NotificationPreferences.objects.get_or_create(user=request.user)

        if request.method == "POST":
            form = ParentProfileForm(request.POST, instance=profile, user=request.user)
            
            # Handle notification preferences update
            if 'update_notifications' in request.POST:
                # Update notification preferences
                notification_prefs.grade_notifications_email = request.POST.get('grade_notifications_email') == 'on'
                notification_prefs.grade_notifications_sms = request.POST.get('grade_notifications_sms') == 'on'
                notification_prefs.attendance_notifications_email = request.POST.get('attendance_notifications_email') == 'on'
                notification_prefs.attendance_notifications_sms = request.POST.get('attendance_notifications_sms') == 'on'
                notification_prefs.assignment_reminders_email = request.POST.get('assignment_reminders_email') == 'on'
                notification_prefs.assignment_reminders_sms = request.POST.get('assignment_reminders_sms') == 'on'
                notification_prefs.announcement_notifications_email = request.POST.get('announcement_notifications_email') == 'on'
                notification_prefs.announcement_notifications_sms = request.POST.get('announcement_notifications_sms') == 'on'
                notification_prefs.emergency_notifications_email = request.POST.get('emergency_notifications_email') == 'on'
                notification_prefs.emergency_notifications_sms = request.POST.get('emergency_notifications_sms') == 'on'
                notification_prefs.conference_reminders_email = request.POST.get('conference_reminders_email') == 'on'
                notification_prefs.conference_reminders_sms = request.POST.get('conference_reminders_sms') == 'on'
                notification_prefs.weekend_notifications = request.POST.get('weekend_notifications') == 'on'
                
                # Update frequency settings
                notification_prefs.grade_frequency = request.POST.get('grade_frequency', 'IMMEDIATE')
                notification_prefs.attendance_frequency = request.POST.get('attendance_frequency', 'IMMEDIATE')
                notification_prefs.assignment_frequency = request.POST.get('assignment_frequency', 'DAILY')
                notification_prefs.announcement_frequency = request.POST.get('announcement_frequency', 'IMMEDIATE')
                
                notification_prefs.save()
                messages.success(request, "Notification preferences updated successfully.")
                return redirect("parent_portal:profile")
            
            elif form.is_valid():
                form.save()
                
                # Update language preference in session for immediate effect
                from django.utils import translation
                language = form.cleaned_data.get('preferred_language')
                if language:
                    translation.activate(language)
                    request.session['django_language'] = language
                
                messages.success(request, "Profile updated successfully.")
                return redirect("parent_portal:profile")
        else:
            form = ParentProfileForm(instance=profile, user=request.user)

        # Get emergency contact information for all children
        emergency_contacts_by_child = {}
        for child in children:
            emergency_contacts_by_child[child] = child.emergency_contacts.filter(
                Q(email=request.user.email)
                | Q(
                    first_name__icontains=request.user.first_name,
                    last_name__icontains=request.user.last_name,
                )
            )

        context = {
            "form": form,
            "children": children,
            "emergency_contacts_by_child": emergency_contacts_by_child,
            "notification_prefs": notification_prefs,
        }

    except Exception as e:
        logger.error(f"Error loading parent profile: {e}")
        context = {"error": "Unable to load profile information at this time."}

    return render(request, "parent_portal/profile.html", context)


@login_required
@role_required(["Parent"])
def progress_report_view(request, student_id=None):
    """Generate current progress report for student"""
    try:
        # Get student and verify access
        if student_id is None:
            current_child, children = get_current_child(request.user, request)
            if not current_child:
                messages.warning(request, "Please select a child to view progress report.")
                return redirect("parent_portal:dashboard")
            student = current_child
        else:
            student = get_object_or_404(Student, id=student_id)
            if not verify_parent_access(request.user, student):
                messages.error(request, "You don't have permission to view this student's information.")
                return redirect("parent_portal:dashboard")
        
        # Get all children for template context
        _, children = get_current_child(request.user, request)
        
        # Get current school year
        current_school_year = SchoolYear.objects.filter(is_active=True).first()
        if not current_school_year:
            messages.error(request, "No active school year found.")
            return redirect("parent_portal:dashboard")
        
        # Get student's enrollments for current year
        enrollments = Enrollment.objects.filter(
            student=student,
            section__school_year=current_school_year,
            is_active=True
        ).select_related(
            'section__course',
            'section__teacher'
        ).prefetch_related('grades__assignment__category')
        
        # Generate report data
        report_data = {
            'student': student,
            'school_year': current_school_year,
            'generated_date': timezone.now(),
            'courses': [],
            'overall_gpa': 0,
            'total_credits': 0,
            'attendance_summary': None
        }
        
        total_grade_points = 0
        total_credits = 0
        
        for enrollment in enrollments:
            # Calculate current grade
            calculated_grade = enrollment.calculate_grade()
            current_percentage = round(calculated_grade, 1) if calculated_grade else None
            current_letter = enrollment.get_letter_grade(calculated_grade) if calculated_grade else "N/A"
            
            # Get assignment breakdown by category
            assignment_categories = {}
            grades = enrollment.grades.filter(
                is_excused=False,
                points_earned__isnull=False
            ).select_related('assignment__category')
            
            for grade in grades:
                category = grade.assignment.category.name
                if category not in assignment_categories:
                    assignment_categories[category] = {
                        'total_points': 0,
                        'earned_points': 0,
                        'count': 0,
                        'assignments': []
                    }
                
                assignment_categories[category]['total_points'] += float(grade.assignment.max_points)
                assignment_categories[category]['earned_points'] += float(grade.points_earned)
                assignment_categories[category]['count'] += 1
                assignment_categories[category]['assignments'].append({
                    'name': grade.assignment.name,
                    'points_earned': grade.points_earned,
                    'max_points': grade.assignment.max_points,
                    'percentage': round(grade.percentage, 1) if grade.percentage else None,
                    'date': grade.graded_date or grade.created_at
                })
            
            # Calculate category averages
            for category_data in assignment_categories.values():
                if category_data['total_points'] > 0:
                    category_data['average'] = round(
                        (category_data['earned_points'] / category_data['total_points']) * 100, 1
                    )
                else:
                    category_data['average'] = None
            
            # Add course data to report
            course_data = {
                'name': enrollment.section.course.name,
                'code': enrollment.section.course.course_code,
                'teacher': enrollment.section.teacher.get_full_name(),
                'section': enrollment.section.section_name,
                'credit_hours': enrollment.section.course.credit_hours,
                'current_grade': current_letter,
                'percentage': current_percentage,
                'assignment_categories': assignment_categories,
                'total_assignments': grades.count()
            }
            
            report_data['courses'].append(course_data)
            
            # Calculate GPA contribution
            if calculated_grade is not None:
                grade_points = {
                    'A+': 4.0, 'A': 4.0, 'A-': 3.7,
                    'B+': 3.3, 'B': 3.0, 'B-': 2.7,
                    'C+': 2.3, 'C': 2.0, 'C-': 1.7,
                    'D+': 1.3, 'D': 1.0, 'D-': 0.7,
                    'F': 0.0
                }.get(current_letter, 0.0)
                
                total_grade_points += grade_points * float(enrollment.section.course.credit_hours)
                total_credits += float(enrollment.section.course.credit_hours)
        
        # Calculate overall GPA
        if total_credits > 0:
            report_data['overall_gpa'] = round(total_grade_points / total_credits, 2)
            report_data['total_credits'] = total_credits
        
        # Get attendance summary
        attendance_records = Attendance.objects.filter(
            enrollment__student=student,
            enrollment__section__school_year=current_school_year
        )
        
        if attendance_records.exists():
            total_days = attendance_records.count()
            present_days = attendance_records.filter(status='P').count()
            absent_days = attendance_records.filter(status__in=['A', 'E']).count()
            tardy_days = attendance_records.filter(status__in=['T', 'L']).count()
            
            report_data['attendance_summary'] = {
                'total_days': total_days,
                'present_days': present_days,
                'absent_days': absent_days,
                'tardy_days': tardy_days,
                'attendance_rate': round((present_days / total_days) * 100, 1) if total_days > 0 else 0
            }
        
        context = {
            'student': student,
            'current_child': student,
            'children': children,
            'report_data': report_data,
            'page_title': f"Progress Report - {student.display_name}"
        }
        
        return render(request, "parent_portal/progress_report.html", context)
        
    except Exception as e:
        logger.error(f"Error generating progress report: {e}")
        messages.error(request, "Unable to generate progress report at this time.")
        return redirect("parent_portal:dashboard")


@login_required
@role_required(["Parent"])
def progress_report_pdf(request, student_id=None):
    """Generate and download progress report as PDF"""
    try:
        # Get student and verify access
        if student_id is None:
            current_child, children = get_current_child(request.user, request)
            if not current_child:
                messages.warning(request, "Please select a child to download report.")
                return redirect("parent_portal:dashboard")
            student = current_child
        else:
            student = get_object_or_404(Student, id=student_id)
            if not verify_parent_access(request.user, student):
                messages.error(request, "You don't have permission to access this report.")
                return redirect("parent_portal:dashboard")
        
        # Get report data (reuse logic from progress_report_view)
        current_school_year = SchoolYear.objects.filter(is_active=True).first()
        enrollments = Enrollment.objects.filter(
            student=student,
            section__school_year=current_school_year,
            is_active=True
        ).select_related('section__course', 'section__teacher').prefetch_related('grades__assignment__category')
        
        # Create PDF response
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="progress_report_{student.last_name}_{student.first_name}_{timezone.now().strftime("%Y%m%d")}.pdf"'
        
        # Create PDF document
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        
        # Define styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=12,
            spaceAfter=10,
            textColor=colors.darkblue
        )
        
        # Build PDF content
        content = []
        
        # Title
        content.append(Paragraph("PROGRESS REPORT", title_style))
        content.append(Spacer(1, 20))
        
        # Student information
        student_info = [
            ['Student Name:', f"{student.first_name} {student.last_name}"],
            ['Student ID:', student.student_id],
            ['Grade Level:', student.grade_level.name if student.grade_level else 'N/A'],
            ['School Year:', current_school_year.name if current_school_year else 'N/A'],
            ['Report Date:', timezone.now().strftime('%B %d, %Y')]
        ]
        
        student_table = Table(student_info, colWidths=[2*inch, 3*inch])
        student_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        content.append(student_table)
        content.append(Spacer(1, 20))
        
        # Course grades
        if enrollments.exists():
            content.append(Paragraph("COURSE GRADES", heading_style))
            
            # Create grades table
            grade_data = [['Course', 'Teacher', 'Current Grade', 'Percentage', 'Credits']]
            
            total_grade_points = 0
            total_credits = 0
            
            for enrollment in enrollments:
                calculated_grade = enrollment.calculate_grade()
                current_percentage = round(calculated_grade, 1) if calculated_grade else None
                current_letter = enrollment.get_letter_grade(calculated_grade) if calculated_grade else "N/A"
                
                grade_data.append([
                    f"{enrollment.section.course.course_code}: {enrollment.section.course.name}",
                    enrollment.section.teacher.get_full_name(),
                    current_letter,
                    f"{current_percentage}%" if current_percentage else "N/A",
                    str(enrollment.section.course.credit_hours)
                ])
                
                # Calculate GPA
                if calculated_grade is not None:
                    grade_points = {
                        'A+': 4.0, 'A': 4.0, 'A-': 3.7,
                        'B+': 3.3, 'B': 3.0, 'B-': 2.7,
                        'C+': 2.3, 'C': 2.0, 'C-': 1.7,
                        'D+': 1.3, 'D': 1.0, 'D-': 0.7,
                        'F': 0.0
                    }.get(current_letter, 0.0)
                    
                    total_grade_points += grade_points * float(enrollment.section.course.credit_hours)
                    total_credits += float(enrollment.section.course.credit_hours)
            
            grades_table = Table(grade_data, colWidths=[2.5*inch, 1.5*inch, 1*inch, 1*inch, 0.7*inch])
            grades_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            content.append(grades_table)
            content.append(Spacer(1, 15))
            
            # Overall GPA
            if total_credits > 0:
                overall_gpa = round(total_grade_points / total_credits, 2)
                gpa_info = [['Overall GPA:', f"{overall_gpa} / 4.0"], ['Total Credits:', str(total_credits)]]
                gpa_table = Table(gpa_info, colWidths=[2*inch, 2*inch])
                gpa_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ]))
                content.append(gpa_table)
                content.append(Spacer(1, 20))
        
        # Attendance summary
        attendance_records = Attendance.objects.filter(
            enrollment__student=student,
            enrollment__section__school_year=current_school_year
        )
        
        if attendance_records.exists():
            content.append(Paragraph("ATTENDANCE SUMMARY", heading_style))
            
            total_days = attendance_records.count()
            present_days = attendance_records.filter(status='P').count()
            absent_days = attendance_records.filter(status__in=['A', 'E']).count()
            tardy_days = attendance_records.filter(status__in=['T', 'L']).count()
            attendance_rate = round((present_days / total_days) * 100, 1) if total_days > 0 else 0
            
            attendance_data = [
                ['Total School Days:', str(total_days)],
                ['Days Present:', str(present_days)],
                ['Days Absent:', str(absent_days)],
                ['Days Tardy:', str(tardy_days)],
                ['Attendance Rate:', f"{attendance_rate}%"]
            ]
            
            attendance_table = Table(attendance_data, colWidths=[2*inch, 1.5*inch])
            attendance_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ]))
            content.append(attendance_table)
        
        # Build PDF
        doc.build(content)
        pdf = buffer.getvalue()
        buffer.close()
        response.write(pdf)
        
        return response
        
    except Exception as e:
        logger.error(f"Error generating PDF report: {e}")
        messages.error(request, "Unable to generate PDF report at this time.")
        return redirect("parent_portal:dashboard")


@login_required
@role_required(["Parent"])
def historical_reports_view(request, student_id=None):
    """View historical report cards for student"""
    try:
        # Get student and verify access
        if student_id is None:
            current_child, children = get_current_child(request.user, request)
            if not current_child:
                messages.warning(request, "Please select a child to view historical reports.")
                return redirect("parent_portal:dashboard")
            student = current_child
        else:
            student = get_object_or_404(Student, id=student_id)
            if not verify_parent_access(request.user, student):
                messages.error(request, "You don't have permission to view this student's information.")
                return redirect("parent_portal:dashboard")
        
        # Get all children for template context
        _, children = get_current_child(request.user, request)
        
        # Get all school years the student has been enrolled in
        historical_years = SchoolYear.objects.filter(
            coursesection__enrollments__student=student
        ).distinct().order_by('-start_date')
        
        reports_data = []
        
        for school_year in historical_years:
            # Get enrollments for this school year
            enrollments = Enrollment.objects.filter(
                student=student,
                section__school_year=school_year,
                is_active=True
            ).select_related('section__course', 'section__teacher')
            
            if enrollments.exists():
                # Calculate summary data for this year
                total_grade_points = 0
                total_credits = 0
                courses_completed = 0
                
                for enrollment in enrollments:
                    calculated_grade = enrollment.calculate_grade()
                    if calculated_grade is not None:
                        courses_completed += 1
                        letter_grade = enrollment.get_letter_grade(calculated_grade)
                        grade_points = {
                            'A+': 4.0, 'A': 4.0, 'A-': 3.7,
                            'B+': 3.3, 'B': 3.0, 'B-': 2.7,
                            'C+': 2.3, 'C': 2.0, 'C-': 1.7,
                            'D+': 1.3, 'D': 1.0, 'D-': 0.7,
                            'F': 0.0
                        }.get(letter_grade, 0.0)
                        
                        total_grade_points += grade_points * float(enrollment.section.course.credit_hours)
                        total_credits += float(enrollment.section.course.credit_hours)
                
                year_gpa = round(total_grade_points / total_credits, 2) if total_credits > 0 else 0.0
                
                reports_data.append({
                    'school_year': school_year,
                    'gpa': year_gpa,
                    'total_credits': total_credits,
                    'courses_completed': courses_completed,
                    'is_current': school_year.is_active
                })
        
        context = {
            'student': student,
            'current_child': student,
            'children': children,
            'reports_data': reports_data,
            'page_title': f"Historical Reports - {student.display_name}"
        }
        
        return render(request, "parent_portal/historical_reports.html", context)
        
    except Exception as e:
        logger.error(f"Error loading historical reports: {e}")
        messages.error(request, "Unable to load historical reports at this time.")
        return redirect("parent_portal:dashboard")


# Emergency Contact Management Views

@login_required
@role_required(["Parent"])
def emergency_contacts_view(request):
    """View and manage emergency contacts"""
    try:
        current_child, children = get_current_child(request.user, request)
        
        if not children.exists():
            messages.error(
                request, 
                "No student records found for your account. Please contact the school office."
            )
            return redirect('parent_portal:dashboard')
        
        if not current_child:
            current_child = children.first()
        
        child = current_child
        
        # Get emergency contacts for the child
        emergency_contacts = child.emergency_contacts.all().order_by('is_primary', 'last_name', 'first_name')
        
        # Get authorized pickup persons
        pickup_persons = child.authorized_pickup_persons.filter(is_active=True).order_by('last_name', 'first_name')
        
        # Get medical information (if model exists)
        try:
            medical_info = getattr(child, 'medical_information', None)
        except:
            medical_info = None
        
        context = {
            'child': child,
            'current_child': current_child,
            'children': children,
            'emergency_contacts': emergency_contacts,
            'pickup_persons': pickup_persons,
            'medical_info': medical_info,
        }
        
        return render(request, 'parent_portal/emergency_contacts.html', context)
        
    except Exception as e:
        logger.error(f"Error loading emergency contacts: {e}")
        messages.error(request, "Unable to load emergency contact information.")
        return redirect('parent_portal:dashboard')


@login_required
@role_required(["Parent"])
def add_emergency_contact_view(request):
    """Add new emergency contact"""
    try:
        # Get parent's children
        children = request.user.accessible_students.filter(is_active=True)
        
        if not children.exists():
            messages.error(request, "No student records found for your account.")
            return redirect('parent_portal:dashboard')
        
        child_id = request.GET.get('child') or request.POST.get('child')
        if child_id:
            try:
                child = children.get(id=child_id)
            except Student.DoesNotExist:
                child = children.first()
        else:
            child = children.first()
        
        if request.method == 'POST':
            form = EmergencyContactForm(request.POST)
            if form.is_valid():
                emergency_contact = form.save(commit=False)
                emergency_contact.save()
                child.emergency_contacts.add(emergency_contact)
                
                messages.success(request, f"Emergency contact {emergency_contact.full_name} added successfully.")
                return redirect(f'/parent/emergency-contacts/?child={child.id}')
        else:
            form = EmergencyContactForm()
        
        context = {
            'form': form,
            'child': child,
            'children': children,
            'action': 'Add'
        }
        
        return render(request, 'parent_portal/emergency_contact_form.html', context)
        
    except Exception as e:
        logger.error(f"Error adding emergency contact: {e}")
        messages.error(request, "Unable to add emergency contact.")
        return redirect('parent_portal:emergency_contacts')


@login_required
@role_required(["Parent"])
def edit_emergency_contact_view(request, contact_id):
    """Edit existing emergency contact"""
    try:
        # Get parent's children
        children = request.user.accessible_students.filter(is_active=True)
        
        # Get the emergency contact and verify access
        contact = get_object_or_404(EmergencyContact, id=contact_id)
        
        # Verify the contact belongs to one of the parent's children
        if not children.filter(emergency_contacts=contact).exists():
            messages.error(request, "You don't have permission to edit this contact.")
            return redirect('parent_portal:emergency_contacts')
        
        child = children.filter(emergency_contacts=contact).first()
        
        if request.method == 'POST':
            form = EmergencyContactForm(request.POST, instance=contact)
            if form.is_valid():
                form.save()
                messages.success(request, f"Emergency contact {contact.full_name} updated successfully.")
                return redirect(f'/parent/emergency-contacts/?child={child.id}')
        else:
            form = EmergencyContactForm(instance=contact)
        
        context = {
            'form': form,
            'contact': contact,
            'child': child,
            'children': children,
            'action': 'Edit'
        }
        
        return render(request, 'parent_portal/emergency_contact_form.html', context)
        
    except Exception as e:
        logger.error(f"Error editing emergency contact: {e}")
        messages.error(request, "Unable to edit emergency contact.")
        return redirect('parent_portal:emergency_contacts')


@login_required
@role_required(["Parent"])
def add_pickup_person_view(request):
    """Add authorized pickup person"""
    try:
        # Get parent's children
        children = request.user.accessible_students.filter(is_active=True)
        
        if not children.exists():
            messages.error(request, "No student records found for your account.")
            return redirect('parent_portal:dashboard')
        
        child_id = request.GET.get('child') or request.POST.get('child')
        if child_id:
            try:
                child = children.get(id=child_id)
            except Student.DoesNotExist:
                child = children.first()
        else:
            child = children.first()
        
        if request.method == 'POST':
            form = AuthorizedPickupPersonForm(request.POST)
            if form.is_valid():
                pickup_person = form.save(commit=False)
                pickup_person.student = child
                pickup_person.save()
                
                messages.success(request, f"Authorized pickup person {pickup_person.full_name} added successfully.")
                return redirect(f'/parent/emergency-contacts/?child={child.id}')
        else:
            form = AuthorizedPickupPersonForm()
        
        context = {
            'form': form,
            'child': child,
            'children': children,
            'action': 'Add',
            'form_type': 'pickup'
        }
        
        return render(request, 'parent_portal/pickup_person_form.html', context)
        
    except Exception as e:
        logger.error(f"Error adding pickup person: {e}")
        messages.error(request, "Unable to add pickup person.")
        return redirect('parent_portal:emergency_contacts')


@login_required
@role_required(["Parent"])
def edit_pickup_person_view(request, person_id):
    """Edit authorized pickup person"""
    try:
        # Get parent's children
        children = request.user.accessible_students.filter(is_active=True)
        
        # Get the pickup person and verify access
        pickup_person = get_object_or_404(AuthorizedPickupPerson, id=person_id)
        
        # Verify the pickup person belongs to one of the parent's children
        if pickup_person.student not in children:
            messages.error(request, "You don't have permission to edit this pickup person.")
            return redirect('parent_portal:emergency_contacts')
        
        child = pickup_person.student
        
        if request.method == 'POST':
            form = AuthorizedPickupPersonForm(request.POST, instance=pickup_person)
            if form.is_valid():
                form.save()
                messages.success(request, f"Pickup person {pickup_person.full_name} updated successfully.")
                return redirect(f'/parent/emergency-contacts/?child={child.id}')
        else:
            form = AuthorizedPickupPersonForm(instance=pickup_person)
        
        context = {
            'form': form,
            'pickup_person': pickup_person,
            'child': child,
            'children': children,
            'action': 'Edit',
            'form_type': 'pickup'
        }
        
        return render(request, 'parent_portal/pickup_person_form.html', context)
        
    except Exception as e:
        logger.error(f"Error editing pickup person: {e}")
        messages.error(request, "Unable to edit pickup person.")
        return redirect('parent_portal:emergency_contacts')


@login_required
@role_required(["Parent"])
def medical_information_view(request):
    """View and update medical information"""
    try:
        # Get current child and children using the helper function
        current_child, children = get_current_child(request.user, request)
        
        if not current_child:
            messages.error(request, "No student records found for your account.")
            return redirect('parent_portal:dashboard')
        
        # Use current_child as the selected child
        child = current_child
        
        # Get or create medical information
        try:
            medical_info = child.medical_information
        except MedicalInformation.DoesNotExist:
            medical_info = None
        
        if request.method == 'POST':
            if medical_info:
                form = MedicalInformationForm(request.POST, instance=medical_info)
            else:
                form = MedicalInformationForm(request.POST)
            
            if form.is_valid():
                medical_info = form.save(commit=False)
                medical_info.student = child
                medical_info.last_updated_by = request.user
                medical_info.save()
                
                messages.success(request, f"Medical information for {child.full_name} updated successfully.")
                return redirect(f'/parent/emergency-contacts/?child={child.id}')
        else:
            form = MedicalInformationForm(instance=medical_info)
        
        context = {
            'form': form,
            'child': child,
            'current_child': current_child,
            'children': children,
            'medical_info': medical_info,
            'action': 'Update' if medical_info else 'Add'
        }
        
        return render(request, 'parent_portal/medical_information_form.html', context)
        
    except Exception as e:
        logger.error(f"Error updating medical information: {e}")
        messages.error(request, "Unable to update medical information.")
        return redirect('parent_portal:emergency_contacts')


@login_required
@role_required(["Parent"])
def upload_document_view(request):
    """Upload documents/photos for students"""
    try:
        current_child, children = get_current_child(request.user, request)
        
        if request.method == "POST":
            from academics.models import DocumentUpload
            
            child_id = request.POST.get('student_id')
            if child_id:
                try:
                    student = next((child for child in children if str(child.id) == child_id), None)
                    if not student:
                        messages.error(request, "Invalid student selected.")
                        return redirect('parent_portal:upload_document')
                except:
                    messages.error(request, "Invalid student selected.")
                    return redirect('parent_portal:upload_document')
            else:
                student = current_child
                
            if not student:
                messages.error(request, "Please select a student.")
                return redirect('parent_portal:upload_document')
            
            # Handle file upload
            uploaded_file = request.FILES.get('document')
            if not uploaded_file:
                messages.error(request, "Please select a file to upload.")
                return redirect('parent_portal:upload_document')
            
            # Validate file size (max 10MB)
            if uploaded_file.size > 10 * 1024 * 1024:
                messages.error(request, "File size must be less than 10MB.")
                return redirect('parent_portal:upload_document')
            
            # Create document upload
            document = DocumentUpload.objects.create(
                uploaded_by=request.user,
                student=student,
                title=request.POST.get('title', uploaded_file.name),
                description=request.POST.get('description', ''),
                document_type=request.POST.get('document_type', 'OTHER'),
                file=uploaded_file,
                shared_with_teachers=request.POST.get('shared_with_teachers') == 'on',
                shared_with_nurse=request.POST.get('shared_with_nurse') == 'on',
                is_private=request.POST.get('is_private') == 'on'
            )
            
            messages.success(request, f"Document '{document.title}' uploaded successfully.")
            return redirect('parent_portal:document_list')
        
        context = {
            "current_child": current_child,
            "children": children,
        }
        
        return render(request, "parent_portal/upload_document.html", context)
        
    except Exception as e:
        logger.error(f"Error in document upload view: {e}")
        return render(request, "parent_portal/upload_document.html", {
            "error": "Unable to load document upload form.",
            "children": children if 'children' in locals() else [],
        })


@login_required
@role_required(["Parent"])
def document_list_view(request):
    """List uploaded documents"""
    try:
        current_child, children = get_current_child(request.user, request)
        from academics.models import DocumentUpload
        
        # Get documents for current child or all children
        if current_child:
            documents = DocumentUpload.objects.filter(
                uploaded_by=request.user,
                student=current_child
            ).order_by('-uploaded_at')
        else:
            documents = DocumentUpload.objects.filter(
                uploaded_by=request.user,
                student__in=children
            ).order_by('-uploaded_at')
        
        context = {
            "current_child": current_child,
            "children": children,
            "documents": documents,
        }
        
        return render(request, "parent_portal/document_list.html", context)
        
    except Exception as e:
        logger.error(f"Error in document list view: {e}")
        return render(request, "parent_portal/document_list.html", {
            "error": "Unable to load documents.",
            "children": children if 'children' in locals() else [],
        })


@login_required
@role_required(["Parent"])
def quick_grades_api(request):
    """API endpoint for quick grade widget"""
    try:
        children = get_parent_children(request.user)
        
        children_data = []
        for child in children:
            # Get recent grades
            recent_grades = []
            enrollments = child.enrollments.filter(
                course__school_year__is_active=True
            ).select_related('course')[:5]
            
            for enrollment in enrollments:
                if hasattr(enrollment, 'grades') and enrollment.grades.exists():
                    latest_grade = enrollment.grades.order_by('-date_assigned').first()
                    if latest_grade:
                        recent_grades.append({
                            'subject': enrollment.course.name,
                            'grade': latest_grade.grade or 'N/A'
                        })
            
            # Calculate GPA (simplified)
            gpa = child.current_gpa if hasattr(child, 'current_gpa') else None
            
            children_data.append({
                'name': child.display_name,
                'gpa': f"{gpa:.2f}" if gpa else 'N/A',
                'recent_grades': recent_grades[:3]  # Show last 3
            })
        
        return JsonResponse({
            'children': children_data,
            'updated_at': timezone.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in quick grades API: {e}")
        return JsonResponse({'error': 'Unable to load grade data'}, status=500)
