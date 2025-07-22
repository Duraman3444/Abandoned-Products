from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import timedelta, date
from authentication.decorators import role_required
from students.models import Student, SchoolYear
import logging

logger = logging.getLogger(__name__)


# Helper function to get parent's children
def get_parent_children(user):
    """Get all students associated with the current parent user."""
    try:
        # Find students where the user's email matches emergency contact emails
        children = (
            Student.objects.filter(emergency_contacts__email=user.email, is_active=True)
            .distinct()
            .select_related("grade_level")
            .prefetch_related("emergency_contacts")
        )

        # Alternative: match by name if email doesn't work
        if not children.exists() and user.get_full_name():
            name_parts = user.get_full_name().split()
            if len(name_parts) >= 2:
                children = (
                    Student.objects.filter(
                        Q(emergency_contacts__first_name__icontains=name_parts[0])
                        & Q(emergency_contacts__last_name__icontains=name_parts[-1]),
                        is_active=True,
                    )
                    .distinct()
                    .select_related("grade_level")
                    .prefetch_related("emergency_contacts")
                )

        return children
    except Exception as e:
        logger.error(f"Error finding children for parent {user.username}: {e}")
        return Student.objects.none()


def verify_parent_access(user, student):
    """Verify that the parent has access to view this student's information."""
    parent_children = get_parent_children(user)
    return student in parent_children


@login_required
@role_required(["Parent"])
def dashboard_view(request):
    """Parent dashboard showing overview of all children"""
    try:
        children = get_parent_children(request.user)

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

        # Aggregate data for all children
        children_summary = []
        for child in children:
            # Mock academic data (would come from grades/courses models)
            current_gpa = 87.5  # Mock GPA
            attendance_rate = 94.2  # Mock attendance

            # Mock recent grades
            recent_grades = [
                {"course": "Mathematics", "grade": "A-", "date": "2024-10-15"},
                {"course": "English", "grade": "B+", "date": "2024-10-14"},
                {"course": "Science", "grade": "A", "date": "2024-10-13"},
            ]

            # Mock upcoming assignments
            upcoming_assignments = [
                {
                    "course": "Mathematics",
                    "title": "Quiz on Fractions",
                    "due_date": timezone.now() + timedelta(days=3),
                },
                {
                    "course": "English",
                    "title": "Book Report",
                    "due_date": timezone.now() + timedelta(days=7),
                },
            ]

            children_summary.append(
                {
                    "student": child,
                    "current_gpa": current_gpa,
                    "attendance_rate": attendance_rate,
                    "recent_grades": recent_grades[:3],  # Show last 3 grades
                    "upcoming_assignments": upcoming_assignments[
                        :2
                    ],  # Show next 2 assignments
                }
            )

        # Mock school announcements
        announcements = [
            {
                "title": "Parent-Teacher Conferences",
                "message": "Sign up for conferences scheduled for November 15-16.",
                "date": timezone.now() - timedelta(days=2),
                "urgent": True,
            },
            {
                "title": "Fall Festival",
                "message": "Join us for our annual Fall Festival on October 30th.",
                "date": timezone.now() - timedelta(days=5),
                "urgent": False,
            },
            {
                "title": "Early Dismissal",
                "message": "School will dismiss at 1:00 PM on November 8th for teacher training.",
                "date": timezone.now() - timedelta(days=1),
                "urgent": False,
            },
        ]

        context = {
            "children": children,
            "children_summary": children_summary,
            "current_school_year": current_school_year,
            "announcements": announcements,
            "total_children": children.count(),
        }

    except Exception as e:
        logger.error(f"Error loading parent dashboard: {e}")
        context = {"error": "Unable to load dashboard data at this time."}

    return render(request, "parent_portal/dashboard.html", context)


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
def child_detail_view(request, student_id):
    """Individual child detail view with comprehensive academic information"""
    try:
        student = get_object_or_404(Student, id=student_id)

        # Verify parent has access to this student
        if not verify_parent_access(request.user, student):
            messages.error(
                request, "You don't have permission to view this student's information."
            )
            return redirect("parent_portal:dashboard")

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
def grades_view(request, student_id):
    """Child's detailed grades view"""
    try:
        student = get_object_or_404(Student, id=student_id)

        # Verify parent has access to this student
        if not verify_parent_access(request.user, student):
            messages.error(
                request, "You don't have permission to view this student's information."
            )
            return redirect("parent_portal:dashboard")

        # Mock detailed grade data with assignment breakdown
        courses_with_grades = [
            {
                "name": "Mathematics",
                "teacher": "Mr. Johnson",
                "credit_hours": 1.0,
                "current_grade": "A-",
                "percentage": 88.5,
                "assignments": [
                    {
                        "name": "Quiz 1",
                        "grade": 92,
                        "max_points": 100,
                        "date": "2024-09-15",
                        "category": "Quiz",
                        "weight": 20,
                    },
                    {
                        "name": "Homework Set 1",
                        "grade": 87,
                        "max_points": 100,
                        "date": "2024-09-20",
                        "category": "Homework",
                        "weight": 15,
                    },
                    {
                        "name": "Test 1",
                        "grade": 85,
                        "max_points": 100,
                        "date": "2024-09-25",
                        "category": "Test",
                        "weight": 30,
                    },
                    {
                        "name": "Quiz 2",
                        "grade": 90,
                        "max_points": 100,
                        "date": "2024-10-01",
                        "category": "Quiz",
                        "weight": 20,
                    },
                    {
                        "name": "Project",
                        "grade": 94,
                        "max_points": 100,
                        "date": "2024-10-05",
                        "category": "Project",
                        "weight": 25,
                    },
                ],
            },
            {
                "name": "English Literature",
                "teacher": "Ms. Davis",
                "credit_hours": 1.0,
                "current_grade": "B+",
                "percentage": 86.2,
                "assignments": [
                    {
                        "name": "Essay 1",
                        "grade": 88,
                        "max_points": 100,
                        "date": "2024-09-18",
                        "category": "Essay",
                        "weight": 30,
                    },
                    {
                        "name": "Reading Quiz",
                        "grade": 82,
                        "max_points": 100,
                        "date": "2024-09-22",
                        "category": "Quiz",
                        "weight": 15,
                    },
                    {
                        "name": "Discussion Posts",
                        "grade": 90,
                        "max_points": 100,
                        "date": "2024-09-28",
                        "category": "Participation",
                        "weight": 20,
                    },
                    {
                        "name": "Vocabulary Test",
                        "grade": 85,
                        "max_points": 100,
                        "date": "2024-10-02",
                        "category": "Test",
                        "weight": 25,
                    },
                ],
            },
            {
                "name": "Science",
                "teacher": "Dr. Wilson",
                "credit_hours": 1.0,
                "current_grade": "A",
                "percentage": 92.1,
                "assignments": [
                    {
                        "name": "Lab Report 1",
                        "grade": 95,
                        "max_points": 100,
                        "date": "2024-09-16",
                        "category": "Lab",
                        "weight": 25,
                    },
                    {
                        "name": "Chapter Test",
                        "grade": 91,
                        "max_points": 100,
                        "date": "2024-09-23",
                        "category": "Test",
                        "weight": 30,
                    },
                    {
                        "name": "Lab Practical",
                        "grade": 90,
                        "max_points": 100,
                        "date": "2024-09-30",
                        "category": "Lab",
                        "weight": 25,
                    },
                    {
                        "name": "Research Project",
                        "grade": 93,
                        "max_points": 100,
                        "date": "2024-10-07",
                        "category": "Project",
                        "weight": 20,
                    },
                ],
            },
        ]

        # Calculate overall statistics
        total_points = sum(course["percentage"] for course in courses_with_grades)
        overall_gpa = (
            total_points / len(courses_with_grades) if courses_with_grades else 0
        )

        # Grade trends (mock data)
        grade_trends = [
            {"week": "Week 1", "average": 85.2},
            {"week": "Week 2", "average": 87.1},
            {"week": "Week 3", "average": 86.8},
            {"week": "Week 4", "average": 88.5},
            {"week": "Week 5", "average": 89.1},
        ]

        # Missing assignments
        missing_assignments = [
            {
                "course": "English Literature",
                "title": "Reading Log Entry",
                "due_date": timezone.now() - timedelta(days=3),
            },
        ]

        context = {
            "student": student,
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
    """Teacher communications and school messages"""
    try:
        children = get_parent_children(request.user)

        # Mock messages from teachers and school
        messages_data = [
            {
                "id": 1,
                "from": "Mr. Johnson (Mathematics Teacher)",
                "subject": "Great progress in algebra!",
                "message": "Emma is showing excellent progress in her algebra work. She has been very engaged in class discussions and her homework quality has improved significantly.",
                "date": timezone.now() - timedelta(days=2),
                "student": children.first() if children.exists() else None,
                "read": False,
                "urgent": False,
            },
            {
                "id": 2,
                "from": "School Office",
                "subject": "Reminder: Parent-Teacher Conferences",
                "message": "This is a reminder that parent-teacher conferences are scheduled for November 15-16. Please sign up for your preferred time slots.",
                "date": timezone.now() - timedelta(days=1),
                "student": None,  # School-wide message
                "read": True,
                "urgent": True,
            },
            {
                "id": 3,
                "from": "Ms. Davis (English Teacher)",
                "subject": "Missing Assignment",
                "message": "Emma has not yet submitted her reading log entry that was due on Monday. Please have her catch up on this assignment.",
                "date": timezone.now() - timedelta(hours=6),
                "student": children.first() if children.exists() else None,
                "read": False,
                "urgent": True,
            },
            {
                "id": 4,
                "from": "Nurse Williams",
                "subject": "Health Forms Update",
                "message": "Please update Emma's emergency contact information and ensure all health forms are current for the new school year.",
                "date": timezone.now() - timedelta(days=5),
                "student": children.first() if children.exists() else None,
                "read": True,
                "urgent": False,
            },
        ]

        # Paginate messages
        paginator = Paginator(messages_data, 10)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        # Count unread messages
        unread_count = len([msg for msg in messages_data if not msg["read"]])
        urgent_count = len(
            [msg for msg in messages_data if msg["urgent"] and not msg["read"]]
        )

        context = {
            "children": children,
            "page_obj": page_obj,
            "unread_count": unread_count,
            "urgent_count": urgent_count,
        }

    except Exception as e:
        logger.error(f"Error loading parent messages: {e}")
        context = {"error": "Unable to load messages at this time."}

    return render(request, "parent_portal/messages.html", context)


@login_required
@role_required(["Parent"])
def profile_view(request):
    """Parent profile management and emergency contact updates"""
    try:
        children = get_parent_children(request.user)

        if request.method == "POST":
            # Handle profile updates
            user = request.user
            user.first_name = request.POST.get("first_name", "").strip()
            user.last_name = request.POST.get("last_name", "").strip()
            user.email = request.POST.get("email", "").strip()
            user.save()

            messages.success(request, "Profile updated successfully.")
            return redirect("parent_portal:profile")

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

        # Mock family information
        family_info = {
            "primary_address": "123 Family Lane, Suburbia, CA 90210",
            "primary_phone": "(555) 123-4567",
            "secondary_phone": "(555) 987-6543",
            "preferred_contact_method": "Email",
            "emergency_contact_name": "Grandma Smith",
            "emergency_contact_phone": "(555) 555-5555",
        }

        context = {
            "children": children,
            "emergency_contacts_by_child": emergency_contacts_by_child,
            "family_info": family_info,
        }

    except Exception as e:
        logger.error(f"Error loading parent profile: {e}")
        context = {"error": "Unable to load profile information at this time."}

    return render(request, "parent_portal/profile.html", context)
