"""
Comprehensive tests for Student Portal views.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from datetime import date, timedelta
import json

from students.models import Student, GradeLevel, SchoolYear
from academics.models import (
    Department,
    Course,
    CourseSection,
    Enrollment,
    Assignment,
    AssignmentCategory,
    Grade,
    Announcement,
)


class StudentPortalViewTests(TestCase):
    """Test cases for Student Portal views."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()

        # Create users
        self.student_user = User.objects.create_user(
            username="student",
            email="student@test.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
        )

        self.teacher_user = User.objects.create_user(
            username="teacher",
            email="teacher@test.com",
            password="testpass123",
            first_name="Jane",
            last_name="Smith",
        )

        # Create school structure
        self.grade_level = GradeLevel.objects.create(name="10th Grade", order=10)
        self.school_year = SchoolYear.objects.create(
            name="2024-2025",
            start_date=date(2024, 8, 15),
            end_date=date(2025, 6, 15),
            is_active=True,
        )

        self.student = Student.objects.create(
            user=self.student_user,
            student_id="ST001",
            grade_level=self.grade_level,
            date_of_birth=date(2008, 5, 15),
            is_active=True,
        )

        # Create academic structure
        self.department = Department.objects.create(name="Mathematics")
        self.course = Course.objects.create(
            name="Algebra II", course_code="ALG2", department=self.department
        )
        self.section = CourseSection.objects.create(
            course=self.course,
            teacher=self.teacher_user,
            school_year=self.school_year,
            section_name="A",
        )
        self.enrollment = Enrollment.objects.create(
            student=self.student, section=self.section
        )

        # Create assignments and grades
        self.category = AssignmentCategory.objects.create(name="Homework", weight=0.3)
        self.assignment1 = Assignment.objects.create(
            section=self.section,
            category=self.category,
            name="Chapter 1 Problems",
            assigned_date=date.today() - timedelta(days=5),
            due_date=date.today() + timedelta(days=2),
            max_points=100,
            is_published=True,
        )

        self.assignment2 = Assignment.objects.create(
            section=self.section,
            category=self.category,
            name="Chapter 2 Quiz",
            assigned_date=date.today() - timedelta(days=10),
            due_date=date.today() - timedelta(days=3),
            max_points=50,
            is_published=True,
        )

        # Grade for assignment2 (completed)
        self.grade = Grade.objects.create(
            enrollment=self.enrollment,
            assignment=self.assignment2,
            points_earned=45.0,
            graded_by=self.teacher_user,
            graded_date=timezone.now(),
        )

    def test_dashboard_view_requires_login(self):
        """Test that dashboard requires authentication."""
        response = self.client.get(reverse("student_portal:dashboard"))
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_dashboard_view_with_student_login(self):
        """Test dashboard view with student login."""
        self.client.login(username="student", password="testpass123")
        response = self.client.get(reverse("student_portal:dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "John Doe")
        self.assertContains(response, "Student Dashboard")

        # Check context variables
        self.assertEqual(response.context["student"], self.student)
        self.assertIn("upcoming_assignments", response.context)
        self.assertIn("recent_grades", response.context)

    def test_dashboard_view_with_non_student_user(self):
        """Test dashboard view with non-student user."""
        # Create user without student profile
        non_student = User.objects.create_user(
            username="notstudent", password="testpass123"
        )
        self.client.login(username="notstudent", password="testpass123")

        response = self.client.get(reverse("student_portal:dashboard"))
        self.assertEqual(response.status_code, 302)  # Redirect with error

    def test_assignments_view(self):
        """Test assignments list view."""
        self.client.login(username="student", password="testpass123")
        response = self.client.get(reverse("student_portal:assignments"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My Assignments")
        self.assertContains(response, "Chapter 1 Problems")
        self.assertContains(response, "Chapter 2 Quiz")

        # Check that assignments have status
        assignments = response.context["assignments"]
        self.assertTrue(len(assignments) >= 2)

        # Assignment1 should be pending (no grade)
        assignment1_data = next(
            item
            for item in assignments
            if item["assignment"].name == "Chapter 1 Problems"
        )
        self.assertEqual(assignment1_data["status"], "Pending")

        # Assignment2 should be graded (has grade)
        assignment2_data = next(
            item for item in assignments if item["assignment"].name == "Chapter 2 Quiz"
        )
        self.assertEqual(assignment2_data["status"], "Graded")

    def test_assignments_view_with_filters(self):
        """Test assignments view with status filters."""
        self.client.login(username="student", password="testpass123")

        # Test upcoming filter
        response = self.client.get(
            reverse("student_portal:assignments") + "?status=upcoming"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["status_filter"], "upcoming")

        # Should only show upcoming assignments (assignment1)
        assignments = response.context["assignments"]
        assignment_names = [item["assignment"].name for item in assignments]
        self.assertIn("Chapter 1 Problems", assignment_names)
        self.assertNotIn("Chapter 2 Quiz", assignment_names)  # Past due

        # Test done filter
        response = self.client.get(
            reverse("student_portal:assignments") + "?status=done"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["status_filter"], "done")

        # Should only show completed assignments (assignment2)
        assignments = response.context["assignments"]
        assignment_names = [item["assignment"].name for item in assignments]
        self.assertNotIn("Chapter 1 Problems", assignment_names)  # Not completed
        self.assertIn("Chapter 2 Quiz", assignment_names)

    def test_assignment_detail_view(self):
        """Test assignment detail view."""
        self.client.login(username="student", password="testpass123")
        response = self.client.get(
            reverse("student_portal:assignment_detail", args=[self.assignment1.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Chapter 1 Problems")
        self.assertContains(response, "Algebra II")
        self.assertEqual(response.context["assignment"], self.assignment1)

    def test_assignment_detail_view_with_grade(self):
        """Test assignment detail view for graded assignment."""
        self.client.login(username="student", password="testpass123")
        response = self.client.get(
            reverse("student_portal:assignment_detail", args=[self.assignment2.id])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Chapter 2 Quiz")
        self.assertContains(response, "45.0")  # Grade points
        self.assertContains(response, "90.0%")  # Grade percentage
        self.assertEqual(response.context["grade"], self.grade)

    def test_assignment_detail_view_unauthorized(self):
        """Test assignment detail view for unauthorized student."""
        # Create another student
        other_user = User.objects.create_user(
            username="otherstudent", password="testpass123"
        )
        other_student = Student.objects.create(
            user=other_user,
            student_id="ST002",
            grade_level=self.grade_level,
            date_of_birth=date(2008, 3, 10),
        )

        self.client.login(username="otherstudent", password="testpass123")
        response = self.client.get(
            reverse("student_portal:assignment_detail", args=[self.assignment1.id])
        )

        # Should redirect or show 403 since student not enrolled in section
        self.assertIn(response.status_code, [302, 403])

    def test_grades_view(self):
        """Test grades view."""
        self.client.login(username="student", password="testpass123")
        response = self.client.get(reverse("student_portal:grades"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My Grades")
        self.assertContains(response, "Algebra II")

        # Check that grades are displayed
        self.assertContains(response, "45.0")  # Points earned
        self.assertContains(response, "90.0%")  # Percentage

    def test_schedule_view(self):
        """Test schedule view."""
        self.client.login(username="student", password="testpass123")
        response = self.client.get(reverse("student_portal:schedule"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My Schedule")
        self.assertContains(response, "Algebra II")

        # Check that enrollments are shown
        enrollments = response.context["enrollments"]
        self.assertIn(self.enrollment, enrollments)

    def test_profile_view(self):
        """Test profile view."""
        self.client.login(username="student", password="testpass123")
        response = self.client.get(reverse("student_portal:profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My Profile")
        self.assertContains(response, "John Doe")
        self.assertContains(response, "ST001")  # Student ID
        self.assertContains(response, "10th Grade")

    def test_announcements_view(self):
        """Test announcements view."""
        # Create announcement
        announcement = Announcement.objects.create(
            title="Important Notice",
            content="Remember to bring textbooks.",
            audience="STUDENTS",
            is_published=True,
            created_by=self.teacher_user,
            publish_date=timezone.now(),
        )

        self.client.login(username="student", password="testpass123")
        response = self.client.get(reverse("student_portal:announcements"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Announcements")
        self.assertContains(response, "Important Notice")
        self.assertContains(response, "Remember to bring textbooks.")

    def test_ajax_grade_details(self):
        """Test AJAX grade details endpoint."""
        self.client.login(username="student", password="testpass123")
        response = self.client.get(
            reverse("student_portal:grade_details", args=[self.grade.id]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        data = json.loads(response.content)
        self.assertEqual(data["assignment_name"], "Chapter 2 Quiz")
        self.assertEqual(data["points_earned"], 45.0)
        self.assertEqual(data["max_points"], 50)
        self.assertEqual(data["percentage"], 90.0)

    def test_navigation_context(self):
        """Test that navigation context is properly set."""
        self.client.login(username="student", password="testpass123")
        response = self.client.get(reverse("student_portal:dashboard"))

        # Check navigation items
        self.assertContains(response, "Dashboard")
        self.assertContains(response, "Assignments")
        self.assertContains(response, "Grades")
        self.assertContains(response, "Schedule")
        self.assertContains(response, "My Profile")

    def test_responsive_design_elements(self):
        """Test that responsive design elements are present."""
        self.client.login(username="student", password="testpass123")
        response = self.client.get(reverse("student_portal:dashboard"))

        # Check for Bootstrap classes
        self.assertContains(response, "container-fluid")
        self.assertContains(response, "row")
        self.assertContains(response, "col-")

        # Check for mobile navigation
        self.assertContains(response, "navbar-toggler")

    def test_error_handling(self):
        """Test error handling for invalid requests."""
        self.client.login(username="student", password="testpass123")

        # Test invalid assignment ID
        response = self.client.get(
            reverse("student_portal:assignment_detail", args=[99999])
        )
        self.assertEqual(response.status_code, 404)

        # Test invalid grade ID for AJAX
        response = self.client.get(
            reverse("student_portal:grade_details", args=[99999]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 404)


class StudentPortalSecurityTests(TestCase):
    """Test security aspects of Student Portal."""

    def setUp(self):
        """Set up test data for security tests."""
        self.client = Client()

        # Create two students
        self.student1_user = User.objects.create_user(
            username="student1", password="testpass123"
        )
        self.student2_user = User.objects.create_user(
            username="student2", password="testpass123"
        )

        self.grade_level = GradeLevel.objects.create(name="10th Grade", order=10)

        self.student1 = Student.objects.create(
            user=self.student1_user,
            student_id="ST001",
            grade_level=self.grade_level,
            date_of_birth=date(2008, 5, 15),
        )

        self.student2 = Student.objects.create(
            user=self.student2_user,
            student_id="ST002",
            grade_level=self.grade_level,
            date_of_birth=date(2008, 3, 10),
        )

    def test_student_data_isolation(self):
        """Test that students can only see their own data."""
        self.client.login(username="student1", password="testpass123")
        response = self.client.get(reverse("student_portal:profile"))

        # Should see own student ID but not other student's
        self.assertContains(response, "ST001")
        self.assertNotContains(response, "ST002")

    def test_csrf_protection(self):
        """Test CSRF protection on forms."""
        self.client.login(username="student1", password="testpass123")
        response = self.client.get(reverse("student_portal:profile"))

        # Check for CSRF token
        self.assertContains(response, "csrfmiddlewaretoken")

    def test_authentication_required(self):
        """Test that all views require authentication."""
        protected_urls = [
            reverse("student_portal:dashboard"),
            reverse("student_portal:assignments"),
            reverse("student_portal:grades"),
            reverse("student_portal:schedule"),
            reverse("student_portal:profile"),
        ]

        for url in protected_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_sql_injection_protection(self):
        """Test protection against SQL injection."""
        self.client.login(username="student1", password="testpass123")

        # Try SQL injection in assignment filter
        malicious_params = [
            "'; DROP TABLE students_student; --",
            "1' OR '1'='1",
            "1'; DELETE FROM academics_grade; --",
        ]

        for param in malicious_params:
            response = self.client.get(
                reverse("student_portal:assignments"), {"status": param}
            )
            # Should not crash and should return safe response
            self.assertIn(response.status_code, [200, 400])
