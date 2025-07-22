from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.contrib import messages
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta, date
from authentication.decorators import role_required
from students.models import Student, EmergencyContact, SchoolYear
from academics.models import Enrollment, Assignment, Grade, Schedule, Attendance, Announcement
import logging

logger = logging.getLogger(__name__)

# Helper function to get current student
def get_current_student(user):
    """Get the Student object associated with the current user."""
    try:
        # In a real implementation, you'd link User to Student via a profile or foreign key
        # For now, we'll use a simple match by email or username
        student = Student.objects.filter(
            Q(primary_contact_email=user.email) | 
            Q(emergency_contacts__email=user.email)
        ).distinct().first()
        
        if not student:
            # Fallback: try to match by name if username contains student name
            name_parts = user.get_full_name().split() if user.get_full_name() else user.username.split()
            if len(name_parts) >= 2:
                student = Student.objects.filter(
                    first_name__icontains=name_parts[0],
                    last_name__icontains=name_parts[-1]
                ).first()
        
        # For demo/test users, return the first student if none found
        if not student and user.username.startswith('test'):
            logger.warning(f"No student profile found for test user {user.username}, using first available student for demo")
            student = Student.objects.first()
            if student:
                logger.info(f"Using demo student: {student.first_name} {student.last_name}")
        
        return student
    except Exception as e:
        logger.error(f"Error finding student for user {user.username}: {e}")
        return None


@login_required
@role_required(['Student'])
def dashboard_view(request):
    """Student dashboard with overview of grades, attendance, and upcoming assignments"""
    logger.info(f"🏠 DASHBOARD ACCESS: User {request.user.username} accessing dashboard")
    logger.info(f"🔍 Request path: {request.path}")
    logger.info(f"🔍 Request method: {request.method}")
    logger.info(f"🔍 User authenticated: {request.user.is_authenticated}")
    try:
        student = get_current_student(request.user)
        if not student:
            messages.error(request, "Student profile not found. Please contact administration.")
            return render(request, 'student_portal/dashboard.html', {'error': 'Student profile not found'})
        
        # Get current school year
        current_school_year = SchoolYear.objects.filter(is_active=True).first()
        
        # Get real enrollment data
        enrollments = Enrollment.objects.filter(
            student=student,
            section__school_year=current_school_year,
            is_active=True
        ).select_related('section__course', 'section__teacher')
        
        # Build course data with calculated grades
        current_courses = []
        for enrollment in enrollments:
            # Calculate current grade from assignments
            grades = Grade.objects.filter(
                enrollment=enrollment,
                assignment__is_published=True
            ).select_related('assignment__category')
            
            if grades.exists():
                total_points = sum(float(g.points_earned or 0) for g in grades)
                max_points = sum(float(g.assignment.max_points) for g in grades)
                grade_percentage = (total_points / max_points * 100) if max_points > 0 else 0
            else:
                grade_percentage = 0
            
            # Convert percentage to letter grade
            if grade_percentage >= 97: letter_grade = 'A+'
            elif grade_percentage >= 93: letter_grade = 'A'
            elif grade_percentage >= 90: letter_grade = 'A-'
            elif grade_percentage >= 87: letter_grade = 'B+'
            elif grade_percentage >= 83: letter_grade = 'B'
            elif grade_percentage >= 80: letter_grade = 'B-'
            elif grade_percentage >= 77: letter_grade = 'C+'
            elif grade_percentage >= 73: letter_grade = 'C'
            elif grade_percentage >= 70: letter_grade = 'C-'
            elif grade_percentage >= 67: letter_grade = 'D+'
            elif grade_percentage >= 63: letter_grade = 'D'
            elif grade_percentage >= 60: letter_grade = 'D-'
            else: letter_grade = 'F'
            
            current_courses.append({
                'name': enrollment.section.course.name,
                'teacher': f"{enrollment.section.teacher.first_name} {enrollment.section.teacher.last_name}",
                'room': enrollment.section.room,
                'current_grade': letter_grade,
                'grade_percentage': round(grade_percentage, 1)
            })
        
        # Get recent assignments (upcoming and recently due)
        recent_assignment_objs = Assignment.objects.filter(
            section__enrollments__student=student,
            section__school_year=current_school_year,
            is_published=True,
            due_date__gte=timezone.now().date() - timedelta(days=7)
        ).select_related('section__course').order_by('due_date')[:10]
        
        recent_assignments = []
        for assignment in recent_assignment_objs:
            # Check if student has submitted/been graded
            grade = Grade.objects.filter(
                enrollment__student=student,
                assignment=assignment
            ).first()
            
            if grade:
                status = 'Submitted' if grade.points_earned is not None else 'Graded'
            elif assignment.due_date < timezone.now().date():
                status = 'Overdue'
            else:
                status = 'Pending'
            
            recent_assignments.append({
                'course': assignment.section.course.name,
                'title': assignment.name,
                'due_date': assignment.due_date,
                'status': status
            })
        
        # Calculate real attendance summary
        attendance_records = Attendance.objects.filter(
            enrollment__student=student,
            enrollment__section__school_year=current_school_year
        )
        
        total_days = attendance_records.count()
        days_present = attendance_records.filter(status='P').count()
        days_absent = attendance_records.filter(status='A').count()
        days_tardy = attendance_records.filter(status='T').count()
        days_excused = attendance_records.filter(status='E').count()
        
        attendance_percentage = (days_present / total_days * 100) if total_days > 0 else 100
        
        attendance_summary = {
            'days_present': days_present,
            'days_absent': days_absent,
            'days_tardy': days_tardy,
            'days_excused': days_excused,
            'attendance_percentage': round(attendance_percentage, 1)
        }
        
        # Calculate GPA from course percentages
        total_points = sum(course['grade_percentage'] for course in current_courses)
        gpa = total_points / len(current_courses) if current_courses else 0
        
        # Get recent announcements for students
        announcements = Announcement.objects.filter(
            audience__in=['ALL', 'STUDENTS'],
            is_published=True,
            publish_date__lte=timezone.now()
        ).filter(
            Q(expire_date__isnull=True) | Q(expire_date__gte=timezone.now())
        ).order_by('-publish_date')[:5]
        
        context = {
            'student': student,
            'current_school_year': current_school_year,
            'current_courses': current_courses,
            'recent_assignments': recent_assignments,
            'attendance_summary': attendance_summary,
            'announcements': announcements,
            'gpa': round(gpa, 2),
            'upcoming_assignments_count': len([a for a in recent_assignments if a['status'] == 'Pending']),
        }
        
    except Exception as e:
        logger.error(f"Error loading student dashboard: {e}")
        context = {
            'error': 'Unable to load dashboard data at this time.'
        }
    
    return render(request, 'student_portal/dashboard.html', context)


@login_required
@role_required(['Student'])
def grades_view(request):
    """Student grades view with detailed course grades and GPA calculation"""
    logger.info(f"📊 GRADES ACCESS: User {request.user.username} accessing grades")
    logger.info(f"🔍 Request path: {request.path}")
    try:
        student = get_current_student(request.user)
        if not student:
            messages.error(request, "Student profile not found.")
            return redirect('student_portal:dashboard')
        
        # Get selected school year from query parameter
        year_id = request.GET.get("year")
        if year_id and year_id.isdigit():
            selected_year = get_object_or_404(SchoolYear, pk=year_id)
        else:
            selected_year = SchoolYear.objects.filter(is_active=True).first()
        
        # Get all school years for dropdown (most recent first)
        all_years = SchoolYear.objects.order_by("-start_date")
        
        # Get real enrollment and grade data for selected year
        enrollments = Enrollment.objects.filter(
            student=student,
            section__school_year=selected_year,
            is_active=True
        ).select_related('section__course', 'section__teacher')
        
        courses_with_grades = []
        for enrollment in enrollments:
            # Get all grades for this enrollment
            grades = Grade.objects.filter(
                enrollment=enrollment,
                assignment__is_published=True
            ).select_related('assignment__category').order_by('-assignment__due_date')
            
            # Calculate course grade
            if grades.exists():
                total_points = sum(float(g.points_earned or 0) for g in grades)
                max_points = sum(float(g.assignment.max_points) for g in grades)
                percentage = (total_points / max_points * 100) if max_points > 0 else 0
            else:
                percentage = 0
            
            # Convert percentage to letter grade
            if percentage >= 97: letter_grade = 'A+'
            elif percentage >= 93: letter_grade = 'A'
            elif percentage >= 90: letter_grade = 'A-'
            elif percentage >= 87: letter_grade = 'B+'
            elif percentage >= 83: letter_grade = 'B'
            elif percentage >= 80: letter_grade = 'B-'
            elif percentage >= 77: letter_grade = 'C+'
            elif percentage >= 73: letter_grade = 'C'
            elif percentage >= 70: letter_grade = 'C-'
            elif percentage >= 67: letter_grade = 'D+'
            elif percentage >= 63: letter_grade = 'D'
            elif percentage >= 60: letter_grade = 'D-'
            else: letter_grade = 'F'
            
            # Build assignment list
            assignments = []
            for grade in grades:
                assignments.append({
                    'id': grade.assignment.id,
                    'name': grade.assignment.name,
                    'grade': round(float(grade.percentage), 1) if grade.percentage else 0,
                    'points': f"{grade.points_earned or 0}/{grade.assignment.max_points}",
                    'date': grade.assignment.due_date.strftime('%Y-%m-%d'),
                    'category': grade.assignment.category.name,
                    'is_late': grade.is_late,
                    'is_excused': grade.is_excused
                })
            
            courses_with_grades.append({
                'name': enrollment.section.course.name,
                'teacher': f"{enrollment.section.teacher.first_name} {enrollment.section.teacher.last_name}",
                'credit_hours': float(enrollment.section.course.credit_hours),
                'current_grade': letter_grade,
                'percentage': round(percentage, 1),
                'assignments': assignments
            })
        
        # Calculate semester GPA for selected year
        semester_total_points = sum(course['percentage'] for course in courses_with_grades)
        semester_gpa = semester_total_points / len(courses_with_grades) if courses_with_grades else 0
        
        # Calculate cumulative GPA across all years
        all_enrollments = Enrollment.objects.filter(
            student=student,
            is_active=True
        ).select_related('section__course', 'section__teacher', 'section__school_year')
        
        cumulative_points = 0
        cumulative_courses = 0
        
        for enrollment in all_enrollments:
            # Get all grades for this enrollment
            grades = Grade.objects.filter(
                enrollment=enrollment,
                assignment__is_published=True
            )
            
            if grades.exists():
                total_points = sum(float(g.points_earned or 0) for g in grades)
                max_points = sum(float(g.assignment.max_points) for g in grades)
                percentage = (total_points / max_points * 100) if max_points > 0 else 0
                cumulative_points += percentage
                cumulative_courses += 1
        
        cumulative_gpa = cumulative_points / cumulative_courses if cumulative_courses else 0
        
        # Grade scale for reference
        grade_scale = [
            {'letter': 'A', 'range': '90-100', 'gpa': '4.0'},
            {'letter': 'B', 'range': '80-89', 'gpa': '3.0'},
            {'letter': 'C', 'range': '70-79', 'gpa': '2.0'},
            {'letter': 'D', 'range': '60-69', 'gpa': '1.0'},
            {'letter': 'F', 'range': '0-59', 'gpa': '0.0'},
        ]
        
        context = {
            'student': student,
            'courses_with_grades': courses_with_grades,
            'semester_gpa': round(semester_gpa, 2),
            'cumulative_gpa': round(cumulative_gpa, 2),
            'grade_scale': grade_scale,
            'selected_year': selected_year,
            'all_years': all_years,
            'semester': selected_year.name if selected_year else 'Current Semester',
        }
        
    except Exception as e:
        logger.error(f"Error loading student grades: {e}")
        context = {
            'error': 'Unable to load grades at this time.'
        }
    
    return render(request, 'student_portal/grades.html', context)


@login_required
@role_required(['Student'])
def schedule_view(request):
    """Student class schedule view with course details and meeting times"""
    logger.info(f"📅 SCHEDULE ACCESS: User {request.user.username} accessing schedule")
    logger.info(f"🔍 Request path: {request.path}")
    try:
        student = get_current_student(request.user)
        if not student:
            messages.error(request, "Student profile not found.")
            return redirect('student_portal:dashboard')
        
        # Get current school year
        current_school_year = SchoolYear.objects.filter(is_active=True).first()
        
        # Get real schedule data
        enrollments = Enrollment.objects.filter(
            student=student,
            section__school_year=current_school_year,
            is_active=True
        ).select_related('section__course', 'section__teacher')
        
        # Build daily schedule from schedule objects
        day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        daily_schedule = {day: [] for day in day_names}
        
        for enrollment in enrollments:
            schedules = Schedule.objects.filter(
                section=enrollment.section,
                is_active=True
            ).order_by('start_time')
            
            for schedule in schedules:
                day_name = schedule.get_day_of_week_display()
                time_range = f"{schedule.start_time.strftime('%H:%M')}-{schedule.end_time.strftime('%H:%M')}"
                
                # Determine period based on start time
                hour = schedule.start_time.hour
                if hour < 9:
                    period = '1st'
                elif hour < 10:
                    period = '2nd'
                elif hour < 11:
                    period = '3rd'
                elif hour < 12:
                    period = '4th'
                elif hour < 13:
                    period = 'Lunch'
                elif hour < 14:
                    period = '5th'
                elif hour < 15:
                    period = '6th'
                else:
                    period = '7th'
                
                daily_schedule[day_name].append({
                    'period': period,
                    'time': time_range,
                    'course': enrollment.section.course.name,
                    'teacher': f"{enrollment.section.teacher.first_name} {enrollment.section.teacher.last_name}",
                    'room': schedule.room or enrollment.section.room or 'TBA'
                })
        
        # Sort each day's schedule by time
        for day in daily_schedule:
            daily_schedule[day].sort(key=lambda x: x['time'])
        
        # Get today's schedule highlighted
        today = timezone.now().strftime('%A')
        today_schedule = daily_schedule.get(today, [])
        
        context = {
            'student': student,
            'daily_schedule': daily_schedule,
            'today': today,
            'today_schedule': today_schedule,
            'current_time': timezone.now().time(),
        }
        
    except Exception as e:
        logger.error(f"Error loading student schedule: {e}")
        context = {
            'error': 'Unable to load schedule at this time.'
        }
    
    return render(request, 'student_portal/schedule.html', context)


@login_required
@role_required(['Student'])
def attendance_view(request):
    """Student attendance records with detailed history"""
    try:
        student = get_current_student(request.user)
        if not student:
            messages.error(request, "Student profile not found.")
            return redirect('student_portal:dashboard')
        
        # Mock attendance data (would come from StudentAttendance models)
        attendance_records = []
        start_date = date(2024, 8, 15)  # Start of school year
        current_date = start_date
        
        # Generate mock attendance for the past 60 school days
        for i in range(60):
            if current_date.weekday() < 5:  # Monday to Friday
                status = 'Present'
                if i % 15 == 0:  # Occasional absence
                    status = 'Absent'
                elif i % 10 == 0:  # Occasional tardy
                    status = 'Tardy'
                
                attendance_records.append({
                    'date': current_date,
                    'status': status,
                    'period': 'Full Day',
                    'notes': 'Excused' if status == 'Absent' and i % 30 == 0 else ''
                })
            current_date += timedelta(days=1)
        
        # Reverse to show most recent first
        attendance_records.reverse()
        
        # Calculate statistics
        total_days = len(attendance_records)
        present_days = len([r for r in attendance_records if r['status'] == 'Present'])
        absent_days = len([r for r in attendance_records if r['status'] == 'Absent'])
        tardy_days = len([r for r in attendance_records if r['status'] == 'Tardy'])
        
        attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
        
        # Paginate attendance records
        paginator = Paginator(attendance_records, 20)  # Show 20 records per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'student': student,
            'page_obj': page_obj,
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'tardy_days': tardy_days,
            'attendance_percentage': round(attendance_percentage, 1),
        }
        
    except Exception as e:
        logger.error(f"Error loading student attendance: {e}")
        context = {
            'error': 'Unable to load attendance records at this time.'
        }
    
    return render(request, 'student_portal/attendance.html', context)


@login_required
@role_required(['Student'])
def profile_view(request):
    """Student profile management with emergency contact information"""
    try:
        student = get_current_student(request.user)
        if not student:
            messages.error(request, "Student profile not found.")
            return redirect('student_portal:dashboard')
        
        if request.method == 'POST':
            # Handle profile updates (limited fields students can edit)
            preferred_name = request.POST.get('preferred_name', '').strip()
            special_notes = request.POST.get('special_notes', '').strip()
            
            if preferred_name != student.preferred_name:
                student.preferred_name = preferred_name
                messages.success(request, 'Preferred name updated successfully.')
            
            # Note: Special needs would typically require admin approval
            # Here we're just showing the interface
            
            student.save()
            
        # Get emergency contacts
        emergency_contacts = student.emergency_contacts.all().order_by('is_primary', 'relationship')
        
        context = {
            'student': student,
            'emergency_contacts': emergency_contacts,
            'age': student.get_age(),
            'years_enrolled': (timezone.now().date() - student.enrollment_date).days // 365,
        }
        
    except Exception as e:
        logger.error(f"Error loading student profile: {e}")
        context = {
            'error': 'Unable to load profile at this time.'
        }
    
    return render(request, 'student_portal/profile.html', context)


@login_required
@role_required(['Student'])
def assignments_view(request):
    """List upcoming & recently-due assignments for the logged-in student."""
    try:
        student = get_current_student(request.user)
        if not student:
            messages.error(request, "Student profile not found.")
            return redirect('student_portal:dashboard')
        
        current_year = SchoolYear.objects.filter(is_active=True).first()

        assignments = (
            Assignment.objects
            .filter(section__enrollments__student=student,
                    section__school_year=current_year,
                    is_published=True)
            .select_related('section__course')
            .order_by('due_date')
        )
        
        # Add status to each assignment
        assignments_with_status = []
        for assignment in assignments:
            grade = Grade.objects.filter(assignment=assignment,
                                         enrollment__student=student).first()
            
            if grade:
                status = 'Submitted' if grade.points_earned is not None else 'Graded'
            elif assignment.due_date < timezone.now().date():
                status = 'Overdue'
            else:
                status = 'Pending'
            
            assignments_with_status.append({
                'assignment': assignment,
                'status': status,
                'grade': grade
            })

        context = {
            'student': student,
            'assignments': assignments_with_status,
            'current_year': current_year
        }
        
    except Exception as e:
        logger.error(f"Error loading assignments: {e}")
        context = {
            'error': 'Unable to load assignments at this time.'
        }
    
    return render(request, 'student_portal/assignments.html', context)


@login_required
@role_required(['Student'])
def assignment_detail_view(request, assignment_id):
    """Show grade & teacher feedback for a single assignment."""
    try:
        student = get_current_student(request.user)
        if not student:
            messages.error(request, "Student profile not found.")
            return redirect('student_portal:dashboard')
        
        assignment = get_object_or_404(
            Assignment,
            pk=assignment_id,
            section__enrollments__student=student,
            is_published=True
        )
        grade = Grade.objects.filter(assignment=assignment,
                                     enrollment__student=student).first()

        context = {
            'student': student,
            'assignment': assignment,
            'grade': grade
        }
        
    except Exception as e:
        logger.error(f"Error loading assignment detail: {e}")
        context = {
            'error': 'Unable to load assignment details at this time.'
        }
    
    return render(request, 'student_portal/assignment_detail.html', context)
