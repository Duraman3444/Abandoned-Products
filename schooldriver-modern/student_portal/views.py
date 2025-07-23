from typing import Optional, Dict, Any, List, Union
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import HttpResponse, HttpRequest
from datetime import timedelta, date
from authentication.decorators import role_required
from .forms import StudentProfileForm
from schooldriver_modern.cache_utils import (
    invalidate_student_cache,
)
from students.models import Student, SchoolYear
from academics.models import (
    Enrollment,
    Assignment,
    Grade,
    Schedule,
    Attendance,
    Announcement,
)
from .utils import gpa as gpa_utils
import logging
import csv

logger = logging.getLogger(__name__)


# Helper function to get current student
def get_current_student(user: User) -> Optional[Student]:
    """
    Get the Student object associated with the current user.
    
    This function attempts to find a Student record that matches the provided user
    by checking email addresses and names. It includes fallback logic for test users.
    
    Args:
        user: Django User object to find the associated Student for
        
    Returns:
        Optional[Student]: The associated Student object if found, None otherwise
        
    Note:
        - First tries to match by primary_contact_email or emergency contact email
        - Falls back to name matching if email match fails
        - For test users, returns the first available student for demo purposes
        - Logs warnings and errors for debugging purposes
    """
    try:
        # In a real implementation, you'd link User to Student via a profile or foreign key
        # For now, we'll use a simple match by email or username
        student = (
            Student.objects.filter(
                Q(primary_contact_email=user.email)
                | Q(emergency_contacts__email=user.email)
            )
            .distinct()
            .first()
        )

        if not student:
            # Fallback: try to match by name if username contains student name
            name_parts = (
                user.get_full_name().split()
                if user.get_full_name()
                else user.username.split()
            )
            if len(name_parts) >= 2:
                student = Student.objects.filter(
                    first_name__icontains=name_parts[0],
                    last_name__icontains=name_parts[-1],
                ).first()

        # For demo/test users, return the first student if none found
        if not student and user.username.startswith("test"):
            logger.warning(
                f"No student profile found for test user {user.username}, using first available student for demo"
            )
            student = Student.objects.first()
            if student:
                logger.info(
                    f"Using demo student: {student.first_name} {student.last_name}"
                )

        return student
    except Exception as e:
        logger.error(f"Error finding student for user {user.username}: {e}")
        return None


def get_student_academic_data(student: Student) -> Dict[str, Any]:
    """
    Get comprehensive academic data for a student across all views.
    
    This function aggregates all academic information for a student including
    current courses, grades, GPA calculations, and attendance data. It uses
    optimized queries to avoid N+1 problems and includes proper error handling.
    
    Args:
        student: Student object to get academic data for
        
    Returns:
        Dict[str, Any]: Dictionary containing:
            - current_courses: List of current course enrollments with grades
            - gpa_data: GPA calculations (4.0 scale, percentage, weighted)
            - attendance_summary: Attendance statistics and percentages
            - total_credits: Sum of credit hours for current courses
            - course_count: Number of currently enrolled courses
            - current_school_year: Active school year object
            - enrollments: QuerySet of current enrollments
            
    Note:
        - Uses select_related and prefetch_related for query optimization
        - Handles cases where no data exists gracefully
        - Logs errors and returns safe defaults on exceptions
    """
    try:
        current_school_year = SchoolYear.objects.filter(is_active=True).first()
        # Optimized query with prefetch_related to avoid N+1 problems
        enrollments = (
            Enrollment.objects.filter(
                student=student,
                section__school_year=current_school_year,
                is_active=True,
            )
            .select_related(
                "section__course__department",
                "section__teacher",
                "section__school_year",
            )
            .prefetch_related("grades__assignment__category")
        )

        # Calculate current courses and grades
        current_courses = []
        for enrollment in enrollments:
            # Use prefetched grades to avoid N+1 query
            grades = [g for g in enrollment.grades.all() if g.assignment.is_published]

            if grades:
                total_points = sum(float(g.points_earned or 0) for g in grades)
                max_points = sum(float(g.assignment.max_points) for g in grades)
                grade_percentage = (
                    (total_points / max_points * 100) if max_points > 0 else 0
                )
            else:
                grade_percentage = 0

            # Convert percentage to letter grade using utility
            letter_grade = gpa_utils.get_letter_grade(grade_percentage)

            current_courses.append(
                {
                    "name": enrollment.section.course.name,
                    "teacher": f"{enrollment.section.teacher.first_name} {enrollment.section.teacher.last_name}",
                    "room": enrollment.section.room,
                    "current_grade": letter_grade,
                    "percentage": round(grade_percentage, 1),
                    "credit_hours": float(enrollment.section.course.credit_hours),
                }
            )

        # Calculate GPA using utility for consistency
        gpa_data = gpa_utils.calculate_gpa_from_courses(current_courses)

        # Calculate attendance summary
        attendance_records = Attendance.objects.filter(
            enrollment__student=student,
            enrollment__section__school_year=current_school_year,
        )

        total_days = attendance_records.count()
        days_present = attendance_records.filter(status="P").count()
        days_absent = attendance_records.filter(status="A").count()
        days_tardy = attendance_records.filter(status="T").count()
        days_excused = attendance_records.filter(status="E").count()

        # Present rate: only days marked "Present"
        present_rate = (
            (days_present / total_days * 100) if total_days > 0 else 100
        )
        
        # Attendance rate: present + tardy (student was there)
        days_attending = days_present + days_tardy
        attendance_rate = (
            (days_attending / total_days * 100) if total_days > 0 else 100
        )

        attendance_summary = {
            "days_present": days_present,
            "days_absent": days_absent,
            "days_tardy": days_tardy,
            "days_excused": days_excused,
            "present_rate": round(present_rate, 1),
            "attendance_rate": round(attendance_rate, 1),
        }

        # Calculate total credits
        total_credits = sum(course["credit_hours"] for course in current_courses)

        return {
            "current_courses": current_courses,
            "gpa_data": gpa_data,
            "attendance_summary": attendance_summary,
            "total_credits": total_credits,
            "course_count": len(current_courses),
            "current_school_year": current_school_year,
            "enrollments": enrollments,
        }
    except Exception as e:
        logger.error(f"Error getting academic data for student {student}: {e}")
        return {
            "current_courses": [],
            "gpa_data": {"gpa4": 0.0, "gpa_pct": 0.0, "weighted_gpa4": 0.0},
            "attendance_summary": {"attendance_percentage": 0},
            "total_credits": 0.0,
            "course_count": 0,
            "current_school_year": None,
            "enrollments": [],
        }


@login_required
@role_required(["Student"])
def dashboard_view(request: HttpRequest) -> HttpResponse:
    """Student dashboard with overview of grades, attendance, and upcoming assignments"""
    logger.info(
        f"🏠 DASHBOARD ACCESS: User {request.user.username} accessing dashboard"
    )
    logger.info(f"🔍 Request path: {request.path}")
    logger.info(f"🔍 Request method: {request.method}")
    logger.info(f"🔍 User authenticated: {request.user.is_authenticated}")
    try:
        student = get_current_student(request.user)
        if not student:
            messages.error(
                request, "Student profile not found. Please contact administration."
            )
            return render(
                request,
                "student_portal/dashboard.html",
                {"error": "Student profile not found"},
            )

        # Get consistent academic data
        academic_data = get_student_academic_data(student)
        current_courses = academic_data["current_courses"]
        gpa_data = academic_data["gpa_data"]
        attendance_summary = academic_data["attendance_summary"]
        current_school_year = academic_data["current_school_year"]
        enrollments = academic_data["enrollments"]

        # Get ALL assignments for accurate pending count (same logic as assignments page)
        all_assignment_objs = (
            Assignment.objects.filter(
                section__enrollments__student=student,
                section__school_year=current_school_year,
                is_published=True,
            )
            .select_related("section__course")
            .prefetch_related("grades__enrollment")
        )

        # Count pending assignments (same logic as assignments page)
        pending_count = 0

        # Get recent assignments for display (upcoming and recent)
        recent_assignment_objs = all_assignment_objs.filter(
            due_date__gte=timezone.now().date() - timedelta(days=30)  # Last 30 days plus upcoming for debugging
        ).order_by("due_date")[:10]

        recent_assignments = []
        for assignment in recent_assignment_objs:
            # Check if student has submitted/been graded (use prefetched data)
            grade = None
            for g in assignment.grades.all():
                if g.enrollment.student == student:
                    grade = g
                    break

            if grade:
                if grade.points_earned is not None:
                    status = "Graded"
                else:
                    status = "Submitted"
            elif assignment.due_date < timezone.now().date():
                status = "Overdue"
            else:
                status = "Pending"

            recent_assignments.append(
                {
                    "course": assignment.section.course.name,
                    "title": assignment.name,
                    "due_date": assignment.due_date,
                    "status": status,
                }
            )

        # Count ALL pending assignments (not just recent ones) - same as assignments page
        for assignment in all_assignment_objs:
            grade = None
            for g in assignment.grades.all():
                if g.enrollment.student == student:
                    grade = g
                    break

            # Count as pending if: no grade AND due date is today or future
            if not grade and assignment.due_date >= timezone.now().date():
                pending_count += 1

        # Get today's schedule
        today_weekday = timezone.now().weekday()  # 0=Monday, 6=Sunday
        # Convert to the string format used in Schedule model
        weekday_mapping = {
            0: "MON",
            1: "TUE", 
            2: "WED",
            3: "THU",
            4: "FRI",
            5: "SAT",
            6: "SUN"
        }
        today_weekday_str = weekday_mapping.get(today_weekday, "MON")
        today_schedule = []

        for enrollment in enrollments:
            # Get all schedules for this enrollment, then filter by day
            schedules = Schedule.objects.filter(
                section=enrollment.section, is_active=True
            ).order_by("start_time")

            for schedule in schedules:
                # Check if this schedule is for today
                if schedule.day_of_week == today_weekday_str:
                    today_schedule.append(
                        {
                            "course_name": enrollment.section.course.name,
                            "teacher": f"{enrollment.section.teacher.first_name} {enrollment.section.teacher.last_name}",
                            "room": schedule.room or enrollment.section.room or "TBA",
                            "start_time": schedule.start_time.strftime("%I:%M %p"),
                            "end_time": schedule.end_time.strftime("%I:%M %p"),
                        }
                    )

        # Sort by start time
        today_schedule.sort(key=lambda x: x["start_time"])
        
        # Debug logging
        logger.info(f"Dashboard: Found {len(today_schedule)} classes for today ({today_weekday_str})")
        logger.info(f"Dashboard: Found {len(recent_assignments)} recent assignments")

        # Get recent grades (last 5 graded assignments)
        recent_grades = []
        all_grades = (
            Grade.objects.filter(
                enrollment__student=student,
                enrollment__section__school_year=current_school_year,
                assignment__is_published=True,
                points_earned__isnull=False,
            )
            .select_related("assignment__section__course", "assignment")
            .order_by("-created_at")[:5]
        )

        for grade in all_grades:
            letter_grade = gpa_utils.get_letter_grade(
                float(grade.percentage) if grade.percentage else 0
            )
            recent_grades.append(
                {
                    "assignment_name": grade.assignment.name,
                    "course_name": grade.assignment.section.course.name,
                    "letter_grade": letter_grade,
                    "percentage": grade.percentage or 0,
                }
            )

        # Get recent announcements for students
        announcements = (
            Announcement.objects.filter(
                audience__in=["ALL", "STUDENTS"],
                is_published=True,
                publish_date__lte=timezone.now(),
            )
            .filter(Q(expire_date__isnull=True) | Q(expire_date__gte=timezone.now()))
            .order_by("-publish_date")[:5]
        )

        context = {
            "student": student,
            "current_school_year": current_school_year,
            "current_courses": current_courses,
            "recent_assignments": recent_assignments,
            "today_schedule": today_schedule,
            "recent_grades": recent_grades,
            "attendance_summary": attendance_summary,
            "announcements": announcements,
            "gpa4": gpa_data["gpa4"],
            "gpa_pct": gpa_data["gpa_pct"],
            "weighted_gpa4": gpa_data["weighted_gpa4"],
            "course_count": len(current_courses),
            "pending_count": pending_count,
            "upcoming_assignments_count": pending_count,  # Keep for backward compatibility
        }

    except Exception as e:
        logger.error(f"Error loading student dashboard: {e}")
        context = {"error": "Unable to load dashboard data at this time."}

    return render(request, "student_portal/dashboard.html", context)


@login_required
@role_required(["Student"])
def grades_view(request: HttpRequest) -> HttpResponse:
    """Student grades view with detailed course grades and GPA calculation"""
    logger.info(f"📊 GRADES ACCESS: User {request.user.username} accessing grades")
    logger.info(f"🔍 Request path: {request.path}")
    try:
        student = get_current_student(request.user)
        if not student:
            messages.error(request, "Student profile not found.")
            return redirect("student_portal:dashboard")

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
            student=student, section__school_year=selected_year, is_active=True
        ).select_related("section__course", "section__teacher")

        courses_with_grades = []
        for enrollment in enrollments:
            # Get all grades for this enrollment
            grades = (
                Grade.objects.filter(
                    enrollment=enrollment, assignment__is_published=True
                )
                .select_related("assignment__category")
                .order_by("-assignment__due_date")
            )

            # Calculate course grade
            if grades.exists():
                total_points = sum(float(g.points_earned or 0) for g in grades)
                max_points = sum(float(g.assignment.max_points) for g in grades)
                percentage = (total_points / max_points * 100) if max_points > 0 else 0
            else:
                percentage = 0

            # Convert percentage to letter grade using utility
            letter_grade = gpa_utils.get_letter_grade(percentage)

            # Build assignment list
            assignments = []
            for grade in grades:
                assignments.append(
                    {
                        "id": grade.assignment.id,
                        "name": grade.assignment.name,
                        "grade": round(float(grade.percentage), 1)
                        if grade.percentage
                        else 0,
                        "points": f"{grade.points_earned or 0}/{grade.assignment.max_points}",
                        "date": grade.assignment.due_date.strftime("%Y-%m-%d"),
                        "category": grade.assignment.category.name,
                        "is_late": grade.is_late,
                        "is_excused": grade.is_excused,
                    }
                )

            courses_with_grades.append(
                {
                    "name": enrollment.section.course.name,
                    "teacher": f"{enrollment.section.teacher.first_name} {enrollment.section.teacher.last_name}",
                    "credit_hours": float(enrollment.section.course.credit_hours),
                    "current_grade": letter_grade,
                    "percentage": round(percentage, 1),
                    "assignments": assignments,
                }
            )

        # Calculate semester GPA for selected year using utility
        semester_gpa_data = gpa_utils.calculate_gpa_from_courses(courses_with_grades)

        # Calculate cumulative GPA across all years
        all_enrollments = Enrollment.objects.filter(
            student=student, is_active=True
        ).select_related("section__course", "section__teacher", "section__school_year")

        all_courses_data = []
        for enrollment in all_enrollments:
            # Get all grades for this enrollment
            grades = Grade.objects.filter(
                enrollment=enrollment, assignment__is_published=True
            )

            if grades.exists():
                total_points = sum(float(g.points_earned or 0) for g in grades)
                max_points = sum(float(g.assignment.max_points) for g in grades)
                percentage = (total_points / max_points * 100) if max_points > 0 else 0

                all_courses_data.append(
                    {
                        "percentage": percentage,
                        "credit_hours": float(enrollment.section.course.credit_hours),
                    }
                )

        cumulative_gpa_data = gpa_utils.calculate_gpa_from_courses(all_courses_data)

        # Grade scale for reference
        grade_scale = [
            {"letter": "A", "range": "90-100", "gpa": "4.0"},
            {"letter": "B", "range": "80-89", "gpa": "3.0"},
            {"letter": "C", "range": "70-79", "gpa": "2.0"},
            {"letter": "D", "range": "60-69", "gpa": "1.0"},
            {"letter": "F", "range": "0-59", "gpa": "0.0"},
        ]

        context = {
            "student": student,
            "courses_with_grades": courses_with_grades,
            "semester_gpa4": semester_gpa_data["gpa4"],
            "semester_gpa_pct": semester_gpa_data["gpa_pct"],
            "cumulative_gpa4": cumulative_gpa_data["gpa4"],
            "cumulative_gpa_pct": cumulative_gpa_data["gpa_pct"],
            "course_count": len(courses_with_grades),
            "grade_scale": grade_scale,
            "selected_year": selected_year,
            "all_years": all_years,
            "semester": selected_year.name if selected_year else "Current Semester",
        }

    except Exception as e:
        logger.error(f"Error loading student grades: {e}")
        context = {"error": "Unable to load grades at this time."}

    return render(request, "student_portal/grades.html", context)


@login_required
@role_required(["Student"])
def schedule_view(request):
    """Student class schedule view with course details and meeting times"""
    logger.info(f"📅 SCHEDULE ACCESS: User {request.user.username} accessing schedule")
    logger.info(f"🔍 Request path: {request.path}")
    try:
        student = get_current_student(request.user)
        if not student:
            messages.error(request, "Student profile not found.")
            return redirect("student_portal:dashboard")

        # Get current school year
        current_school_year = SchoolYear.objects.filter(is_active=True).first()

        # Get real schedule data
        enrollments = Enrollment.objects.filter(
            student=student, section__school_year=current_school_year, is_active=True
        ).select_related("section__course", "section__teacher")

        # Build daily schedule from schedule objects
        day_names = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        daily_schedule = {day: [] for day in day_names}

        for enrollment in enrollments:
            schedules = Schedule.objects.filter(
                section=enrollment.section, is_active=True
            ).order_by("start_time")

            for schedule in schedules:
                day_name = schedule.get_day_of_week_display()
                time_range = f"{schedule.start_time.strftime('%H:%M')}-{schedule.end_time.strftime('%H:%M')}"

                # Determine period based on start time
                hour = schedule.start_time.hour
                if hour < 9:
                    period = "1st"
                elif hour < 10:
                    period = "2nd"
                elif hour < 11:
                    period = "3rd"
                elif hour < 12:
                    period = "4th"
                elif hour < 13:
                    period = "Lunch"
                elif hour < 14:
                    period = "5th"
                elif hour < 15:
                    period = "6th"
                else:
                    period = "7th"

                daily_schedule[day_name].append(
                    {
                        "period": period,
                        "time": time_range,
                        "course": enrollment.section.course.name,
                        "teacher": f"{enrollment.section.teacher.first_name} {enrollment.section.teacher.last_name}",
                        "room": schedule.room or enrollment.section.room or "TBA",
                    }
                )

        # Sort each day's schedule by time
        for day in daily_schedule:
            daily_schedule[day].sort(key=lambda x: x["time"])

        # Get today's schedule highlighted
        today = timezone.now().strftime("%A")
        today_schedule = daily_schedule.get(today, [])

        # Get unique teachers for contact section
        teachers_seen = set()
        teachers = []
        for enrollment in enrollments:
            teacher = enrollment.section.teacher
            teacher_key = f"{teacher.first_name} {teacher.last_name}"
            if teacher_key not in teachers_seen:
                teachers_seen.add(teacher_key)
                teachers.append(
                    {
                        "name": teacher_key,
                        "email": teacher.email,
                        "department": "Faculty",  # Could be enhanced with actual department
                        "initials": f"{teacher.first_name[0]}{teacher.last_name[0]}"
                        if teacher.first_name and teacher.last_name
                        else "UN",
                    }
                )

        context = {
            "student": student,
            "daily_schedule": daily_schedule,
            "today": today,
            "today_schedule": today_schedule,
            "current_time": timezone.now().time(),
            "teachers": teachers,
        }

    except Exception as e:
        logger.error(f"Error loading student schedule: {e}")
        context = {"error": "Unable to load schedule at this time."}

    return render(request, "student_portal/schedule.html", context)


def build_schedule_csv_rows(student):
    """Helper function to build schedule data for CSV export."""
    try:
        # Get current school year
        current_school_year = SchoolYear.objects.filter(is_active=True).first()

        # Get real schedule data
        enrollments = Enrollment.objects.filter(
            student=student, section__school_year=current_school_year, is_active=True
        ).select_related("section__course", "section__teacher")

        rows = [["Period", "Course", "Teacher", "Room", "Time", "Days"]]

        for enrollment in enrollments:
            schedules = Schedule.objects.filter(
                section=enrollment.section, is_active=True
            ).order_by("start_time")

            for schedule in schedules:
                day_name = schedule.get_day_of_week_display()
                time_range = f"{schedule.start_time.strftime('%H:%M')}-{schedule.end_time.strftime('%H:%M')}"

                # Determine period based on start time
                hour = schedule.start_time.hour
                if hour < 9:
                    period = "1st"
                elif hour < 10:
                    period = "2nd"
                elif hour < 11:
                    period = "3rd"
                elif hour < 12:
                    period = "4th"
                elif hour < 13:
                    period = "Lunch"
                elif hour < 14:
                    period = "5th"
                elif hour < 15:
                    period = "6th"
                else:
                    period = "7th"

                rows.append(
                    [
                        period,
                        enrollment.section.course.name,
                        f"{enrollment.section.teacher.first_name} {enrollment.section.teacher.last_name}",
                        schedule.room or enrollment.section.room or "TBA",
                        time_range,
                        day_name,
                    ]
                )

        return rows
    except Exception as e:
        logger.error(f"Error building schedule CSV rows: {e}")
        return [["Error", "Unable to load schedule data", "", "", "", ""]]


@login_required
@role_required(["Student"])
def schedule_export_view(request):
    """Return schedule as CSV or PDF based on ?format= param."""
    format_ = request.GET.get("format", "csv")
    student = get_current_student(request.user)

    if not student:
        messages.error(request, "Student profile not found.")
        return redirect("student_portal:schedule")

    # Build schedule data
    rows = build_schedule_csv_rows(student)

    if format_ == "pdf":
        # For now, return CSV - PDF implementation can be added later with WeasyPrint
        messages.info(request, "PDF export coming soon. Downloading CSV instead.")
        format_ = "csv"

    if format_ == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            f'attachment; filename="schedule_{student.first_name}_{student.last_name}.csv"'
        )
        writer = csv.writer(response)
        writer.writerows(rows)
        return response

    return redirect("student_portal:schedule")


@login_required
@role_required(["Student"])
def schedule_print_view(request):
    """Render a print-optimised HTML view of the schedule."""
    student = get_current_student(request.user)

    if not student:
        messages.error(request, "Student profile not found.")
        return redirect("student_portal:schedule")

    rows = build_schedule_csv_rows(student)

    context = {
        "student": student,
        "rows": rows,
        "current_date": timezone.now().date(),
    }

    return render(request, "student_portal/schedule_print.html", context)


@login_required
@role_required(["Student"])
def attendance_view(request):
    """Student attendance records with detailed history"""
    try:
        student = get_current_student(request.user)
        if not student:
            messages.error(request, "Student profile not found.")
            return redirect("student_portal:dashboard")

        # Get current school year for consistency with dashboard
        current_school_year = SchoolYear.objects.get(is_current=True)
        
        # Use same attendance calculation as dashboard for consistency
        attendance_records_db = Attendance.objects.filter(
            enrollment__student=student,
            enrollment__section__school_year=current_school_year,
        )

        total_days = attendance_records_db.count()
        present_days = attendance_records_db.filter(status="P").count()
        absent_days = attendance_records_db.filter(status="A").count()
        tardy_days = attendance_records_db.filter(status="T").count()

        # If no real data, generate mock data for display
        if total_days == 0:
            attendance_records = []
            start_date = date(2024, 8, 15)  # Start of school year
            current_date = start_date

            # Generate mock attendance for the past 60 school days
            for i in range(60):
                if current_date.weekday() < 5:  # Monday to Friday
                    status = "Present"
                    if i % 15 == 0:  # Occasional absence
                        status = "Absent"
                    elif i % 10 == 0:  # Occasional tardy
                        status = "Tardy"

                    attendance_records.append(
                        {
                            "date": current_date,
                            "status": status,
                            "period": "Full Day",
                            "notes": "Excused"
                            if status == "Absent" and i % 30 == 0
                            else "",
                        }
                    )
                current_date += timedelta(days=1)

            # Reverse to show most recent first
            attendance_records.reverse()

            # Use mock data statistics
            total_days = len(attendance_records)
            present_days = len([r for r in attendance_records if r["status"] == "Present"])
            absent_days = len([r for r in attendance_records if r["status"] == "Absent"])
            tardy_days = len([r for r in attendance_records if r["status"] == "Tardy"])
        else:
            # Convert database records to display format
            attendance_records = []
            for record in attendance_records_db.order_by('-date_taken'):
                status_map = {"P": "Present", "A": "Absent", "T": "Tardy", "E": "Excused"}
                attendance_records.append({
                    "date": record.date_taken,
                    "status": status_map.get(record.status, record.status),
                    "period": f"Period {record.enrollment.section.period}" if hasattr(record.enrollment.section, 'period') else "Full Day",
                    "notes": record.notes or "",
                })

        # Calculate both rates consistently with dashboard
        present_rate = (
            (present_days / total_days * 100) if total_days > 0 else 100
        )
        
        days_attending = present_days + tardy_days
        attendance_rate = (
            (days_attending / total_days * 100) if total_days > 0 else 100
        )

        # Paginate attendance records
        paginator = Paginator(attendance_records, 20)  # Show 20 records per page
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context = {
            "student": student,
            "page_obj": page_obj,
            "total_days": total_days,
            "present_days": present_days,
            "absent_days": absent_days,
            "tardy_days": tardy_days,
            "present_rate": round(present_rate, 1),
            "attendance_rate": round(attendance_rate, 1),
        }

    except Exception as e:
        logger.error(f"Error loading student attendance: {e}")
        context = {"error": "Unable to load attendance records at this time."}

    return render(request, "student_portal/attendance.html", context)


@login_required
@role_required(["Student"])
def profile_view(request):
    """Student profile management with emergency contact information"""
    try:
        student = get_current_student(request.user)
        if not student:
            messages.error(request, "Student profile not found.")
            return redirect("student_portal:dashboard")

        if request.method == "POST":
            # Handle profile updates - students can edit personal information
            user = request.user
            profile = user.profile

            # Update User fields
            first_name = request.POST.get("first_name", "").strip()
            last_name = request.POST.get("last_name", "").strip()
            email = request.POST.get("email", "").strip()

            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            if email:
                user.email = email

            user.save()

            # Update Profile fields
            date_of_birth = request.POST.get("date_of_birth")
            phone_number = request.POST.get("phone_number", "").strip()
            address = request.POST.get("address", "").strip()

            # Emergency contact information
            emergency_contact_1_name = request.POST.get(
                "emergency_contact_1_name", ""
            ).strip()
            emergency_contact_1_relationship = request.POST.get(
                "emergency_contact_1_relationship", ""
            ).strip()
            emergency_contact_1_phone = request.POST.get(
                "emergency_contact_1_phone", ""
            ).strip()
            emergency_contact_2_name = request.POST.get(
                "emergency_contact_2_name", ""
            ).strip()
            emergency_contact_2_relationship = request.POST.get(
                "emergency_contact_2_relationship", ""
            ).strip()
            emergency_contact_2_phone = request.POST.get(
                "emergency_contact_2_phone", ""
            ).strip()
            emergency_address = request.POST.get("emergency_address", "").strip()

            # Account settings
            email_notifications = request.POST.get("email_notifications") == "on"
            sms_notifications = request.POST.get("sms_notifications") == "on"
            parent_portal_access = request.POST.get("parent_portal_access") == "on"

            # Save date of birth if provided
            if date_of_birth:
                from datetime import datetime

                try:
                    profile.date_of_birth = datetime.strptime(
                        date_of_birth, "%Y-%m-%d"
                    ).date()
                except ValueError:
                    pass  # Invalid date format, skip

            # Update profile fields
            profile.phone_number = phone_number
            profile.address = address
            profile.emergency_contact_1_name = emergency_contact_1_name
            profile.emergency_contact_1_relationship = emergency_contact_1_relationship
            profile.emergency_contact_1_phone = emergency_contact_1_phone
            profile.emergency_contact_2_name = emergency_contact_2_name
            profile.emergency_contact_2_relationship = emergency_contact_2_relationship
            profile.emergency_contact_2_phone = emergency_contact_2_phone
            profile.emergency_address = emergency_address
            profile.email_notifications = email_notifications
            profile.sms_notifications = sms_notifications
            profile.parent_portal_access = parent_portal_access

            profile.save()

            messages.success(request, "Profile updated successfully!")
            return redirect("student_portal:profile")

        # Get consistent academic data
        academic_data = get_student_academic_data(student)

        # Get emergency contacts
        emergency_contacts = student.emergency_contacts.all().order_by(
            "is_primary", "relationship"
        )

        context = {
            "student": student,
            "emergency_contacts": emergency_contacts,
            "age": student.get_age(),
            "years_enrolled": (timezone.now().date() - student.enrollment_date).days
            // 365,
            "gpa4": academic_data["gpa_data"]["gpa4"],
            "gpa_pct": academic_data["gpa_data"]["gpa_pct"],
            "weighted_gpa4": academic_data["gpa_data"]["weighted_gpa4"],
            "current_courses": academic_data["current_courses"],
            "course_count": academic_data["course_count"],
            "total_credits": academic_data["total_credits"],
            "attendance_percentage": academic_data["attendance_summary"][
                "attendance_percentage"
            ],
        }

    except Exception as e:
        logger.error(f"Error loading student profile: {e}")
        context = {"error": "Unable to load profile at this time."}

    return render(request, "student_portal/profile.html", context)


@login_required
def profile_edit_view(request: HttpRequest) -> HttpResponse:
    """Student profile edit page with full access to personal information"""
    try:
        student = get_current_student(request.user)
        if not student:
            messages.error(request, "Student profile not found.")
            return redirect("student_portal:dashboard")

        user = request.user
        profile = user.profile

        # Prepare initial data for the form
        initial_data = {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "date_of_birth": profile.date_of_birth,
            "phone_number": profile.phone_number,
            "address": profile.address,
            "emergency_contact_1_name": profile.emergency_contact_1_name,
            "emergency_contact_1_relationship": profile.emergency_contact_1_relationship,
            "emergency_contact_1_phone": profile.emergency_contact_1_phone,
            "emergency_contact_2_name": profile.emergency_contact_2_name,
            "emergency_contact_2_relationship": profile.emergency_contact_2_relationship,
            "emergency_contact_2_phone": profile.emergency_contact_2_phone,
            "emergency_address": profile.emergency_address,
            "email_notifications": profile.email_notifications,
            "sms_notifications": profile.sms_notifications,
            "parent_portal_access": profile.parent_portal_access,
        }

        if request.method == "POST":
            form = StudentProfileForm(request.POST)
            # Set user pk for email uniqueness validation
            form.user_pk = user.pk

            if form.is_valid():
                # Update User fields
                user.first_name = form.cleaned_data["first_name"]
                user.last_name = form.cleaned_data["last_name"]
                user.email = form.cleaned_data["email"]
                user.save()

                # Update Profile fields
                if form.cleaned_data["date_of_birth"]:
                    profile.date_of_birth = form.cleaned_data["date_of_birth"]

                profile.phone_number = form.cleaned_data["phone_number"] or ""
                profile.address = form.cleaned_data["address"] or ""
                profile.emergency_contact_1_name = (
                    form.cleaned_data["emergency_contact_1_name"] or ""
                )
                profile.emergency_contact_1_relationship = (
                    form.cleaned_data["emergency_contact_1_relationship"] or ""
                )
                profile.emergency_contact_1_phone = (
                    form.cleaned_data["emergency_contact_1_phone"] or ""
                )
                profile.emergency_contact_2_name = (
                    form.cleaned_data["emergency_contact_2_name"] or ""
                )
                profile.emergency_contact_2_relationship = (
                    form.cleaned_data["emergency_contact_2_relationship"] or ""
                )
                profile.emergency_contact_2_phone = (
                    form.cleaned_data["emergency_contact_2_phone"] or ""
                )
                profile.emergency_address = form.cleaned_data["emergency_address"] or ""
                profile.email_notifications = form.cleaned_data["email_notifications"]
                profile.sms_notifications = form.cleaned_data["sms_notifications"]
                profile.parent_portal_access = form.cleaned_data["parent_portal_access"]

                profile.save()

                # Clear student cache since profile data might affect dashboard
                invalidate_student_cache(student.id if student else user.id)

                messages.success(request, "Profile updated successfully!")
                return redirect("student_portal:profile")
            else:
                # Form has validation errors
                messages.error(request, "Please correct the errors below.")
        else:
            # GET request - initialize form with current data
            form = StudentProfileForm(initial=initial_data)

        context = {
            "student": student,
            "form": form,
        }

    except Exception as e:
        logger.error(f"Error loading student profile edit: {e}")
        messages.error(request, "Unable to load edit profile at this time.")
        return redirect("student_portal:profile")

    return render(request, "student_portal/profile_edit.html", context)


@login_required
@role_required(["Student"])
def assignments_view(request):
    """List assignments for the logged-in student with filtering capabilities."""
    try:
        student = get_current_student(request.user)
        if not student:
            messages.error(request, "Student profile not found.")
            return redirect("student_portal:dashboard")

        current_year = SchoolYear.objects.filter(is_active=True).first()
        status_filter = request.GET.get(
            "status", "all"
        )  # all | upcoming | missing | done
        today = timezone.now().date()

        # Optimized base query with prefetch_related
        assignments = (
            Assignment.objects.filter(
                section__enrollments__student=student,
                section__school_year=current_year,
                is_published=True,
            )
            .select_related("section__course", "section__teacher", "category")
            .prefetch_related("grades__enrollment")
        )

        # Apply status filter
        if status_filter == "upcoming":
            # Upcoming = due today or future AND not submitted yet
            assignments = assignments.filter(due_date__gte=today).exclude(
                grades__enrollment__student=student
            )
        elif status_filter == "missing":
            # Missing = past due date AND no grade submitted
            assignments = assignments.filter(due_date__lt=today).exclude(
                grades__enrollment__student=student
            )
        elif status_filter == "done":
            # Done = has a grade (submitted or graded)
            assignments = assignments.filter(grades__enrollment__student=student)

        assignments = assignments.order_by("due_date")

        # Add status to each assignment using prefetched data
        assignments_with_status = []
        for assignment in assignments:
            # Use prefetched grades instead of separate query
            grade = None
            for g in assignment.grades.all():
                if g.enrollment.student == student:
                    grade = g
                    break

            if grade:
                if grade.points_earned is not None:
                    status = "Graded"  # Grade received (has points)
                else:
                    status = "Submitted"  # Awaiting grade (no points yet)
            elif assignment.due_date < timezone.now().date():
                status = "Overdue"
            else:
                status = "Pending"

            assignments_with_status.append(
                {"assignment": assignment, "status": status, "grade": grade}
            )

        context = {
            "student": student,
            "assignments": assignments_with_status,
            "current_year": current_year,
            "status_filter": status_filter,
            "assignment_count": len(assignments_with_status),
        }

    except Exception as e:
        logger.error(f"Error loading assignments: {e}")
        context = {"error": "Unable to load assignments at this time."}

    return render(request, "student_portal/assignments.html", context)


@login_required
@role_required(["Student"])
def assignment_detail_view(request, assignment_id):
    """Show grade & teacher feedback for a single assignment."""
    try:
        student = get_current_student(request.user)
        if not student:
            messages.error(request, "Student profile not found.")
            return redirect("student_portal:dashboard")

        assignment = get_object_or_404(
            Assignment,
            pk=assignment_id,
            section__enrollments__student=student,
            is_published=True,
        )
        grade = Grade.objects.filter(
            assignment=assignment, enrollment__student=student
        ).first()

        context = {"student": student, "assignment": assignment, "grade": grade}

    except Exception as e:
        logger.error(f"Error loading assignment detail: {e}")
        context = {"error": "Unable to load assignment details at this time."}

    return render(request, "student_portal/assignment_detail.html", context)
