"""
Integration tests for critical user workflows.
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
from admissions.models import Applicant, AdmissionLevel


class StudentWorkflowIntegrationTests(TestCase):
    """Integration tests for complete student workflows."""

    def setUp(self):
        """Set up comprehensive test data."""
        self.client = Client()

        # Create admin user
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@test.com", password="admin123"
        )

        # Create teacher
        self.teacher_user = User.objects.create_user(
            username="teacher",
            email="teacher@test.com",
            password="teacher123",
            first_name="Jane",
            last_name="Smith",
        )

        # Create student
        self.student_user = User.objects.create_user(
            username="student",
            email="student@test.com",
            password="student123",
            first_name="John",
            last_name="Doe",
        )

        # Create school infrastructure
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
            name="Algebra II",
            course_code="ALG2",
            department=self.department,
            credits=1.0,
        )
        self.section = CourseSection.objects.create(
            course=self.course,
            teacher=self.teacher_user,
            school_year=self.school_year,
            section_name="A",
            room="Math101",
            max_students=25,
        )

        self.enrollment = Enrollment.objects.create(
            student=self.student, section=self.section, enrollment_date=date.today()
        )

        # Create assignment categories and assignments
        self.homework_category = AssignmentCategory.objects.create(
            name="Homework", weight=0.3
        )
        self.quiz_category = AssignmentCategory.objects.create(name="Quiz", weight=0.4)
        self.test_category = AssignmentCategory.objects.create(name="Test", weight=0.3)

    def test_complete_student_login_and_dashboard_workflow(self):
        """Test complete student login and dashboard access workflow."""
        # Step 1: Login
        login_response = self.client.post(
            reverse("login"), {"username": "student", "password": "student123"}
        )
        self.assertEqual(login_response.status_code, 302)  # Redirect after login

        # Step 2: Access dashboard
        dashboard_response = self.client.get(reverse("student_portal:dashboard"))
        self.assertEqual(dashboard_response.status_code, 200)
        self.assertContains(dashboard_response, "John Doe")
        self.assertContains(dashboard_response, "Student Dashboard")

        # Step 3: Verify dashboard data
        context = dashboard_response.context
        self.assertEqual(context["student"], self.student)
        self.assertIn("upcoming_assignments", context)
        self.assertIn("recent_grades", context)
        self.assertIn("enrollment_summary", context)

        # Step 4: Check navigation links are accessible
        nav_links = [
            reverse("student_portal:assignments"),
            reverse("student_portal:grades"),
            reverse("student_portal:schedule"),
            reverse("student_portal:profile"),
        ]

        for link in nav_links:
            response = self.client.get(link)
            self.assertEqual(response.status_code, 200)

    def test_complete_assignment_lifecycle_workflow(self):
        """Test complete assignment lifecycle from creation to grading."""
        # Setup: Create assignments with different statuses
        today = date.today()

        # Assignment 1: Upcoming
        upcoming_assignment = Assignment.objects.create(
            section=self.section,
            category=self.homework_category,
            name="Chapter 5 Problems",
            description="Complete problems 1-20",
            assigned_date=today,
            due_date=today + timedelta(days=3),
            max_points=100,
            is_published=True,
        )

        # Assignment 2: Past due, submitted but not graded
        submitted_assignment = Assignment.objects.create(
            section=self.section,
            category=self.quiz_category,
            name="Quiz 1",
            assigned_date=today - timedelta(days=7),
            due_date=today - timedelta(days=3),
            max_points=50,
            is_published=True,
        )

        # Grade for submitted assignment (no points yet)
        submitted_grade = Grade.objects.create(
            enrollment=self.enrollment,
            assignment=submitted_assignment,
            points_earned=None,  # Submitted but not graded
            graded_by=None,
            graded_date=None,
        )

        # Assignment 3: Graded
        graded_assignment = Assignment.objects.create(
            section=self.section,
            category=self.test_category,
            name="Test 1",
            assigned_date=today - timedelta(days=14),
            due_date=today - timedelta(days=7),
            max_points=100,
            is_published=True,
        )

        # Grade for graded assignment
        graded_grade = Grade.objects.create(
            enrollment=self.enrollment,
            assignment=graded_assignment,
            points_earned=85.0,
            graded_by=self.teacher_user,
            graded_date=timezone.now(),
        )

        # Student login and workflow test
        self.client.login(username="student", password="student123")

        # Step 1: View all assignments
        all_response = self.client.get(reverse("student_portal:assignments"))
        self.assertEqual(all_response.status_code, 200)
        self.assertContains(all_response, "Chapter 5 Problems")
        self.assertContains(all_response, "Quiz 1")
        self.assertContains(all_response, "Test 1")

        # Step 2: Test upcoming filter
        upcoming_response = self.client.get(
            reverse("student_portal:assignments") + "?status=upcoming"
        )
        self.assertEqual(upcoming_response.status_code, 200)
        assignments = upcoming_response.context["assignments"]
        upcoming_names = [item["assignment"].name for item in assignments]
        self.assertIn("Chapter 5 Problems", upcoming_names)
        self.assertNotIn("Quiz 1", upcoming_names)  # Past due
        self.assertNotIn("Test 1", upcoming_names)  # Past due

        # Step 3: Test done filter
        done_response = self.client.get(
            reverse("student_portal:assignments") + "?status=done"
        )
        self.assertEqual(done_response.status_code, 200)
        assignments = done_response.context["assignments"]
        done_names = [item["assignment"].name for item in assignments]
        self.assertNotIn("Chapter 5 Problems", done_names)  # Not submitted
        self.assertIn("Quiz 1", done_names)  # Submitted
        self.assertIn("Test 1", done_names)  # Graded

        # Step 4: Test assignment detail views
        detail_response = self.client.get(
            reverse("student_portal:assignment_detail", args=[graded_assignment.id])
        )
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, "Test 1")
        self.assertContains(detail_response, "85.0")  # Grade points
        self.assertContains(detail_response, "85.0%")  # Percentage

        # Step 5: Verify grades view shows graded assignment
        grades_response = self.client.get(reverse("student_portal:grades"))
        self.assertEqual(grades_response.status_code, 200)
        self.assertContains(grades_response, "Test 1")
        self.assertContains(grades_response, "85.0")

    def test_grade_calculation_and_display_workflow(self):
        """Test grade calculation and display across multiple assignments."""
        self.client.login(username="student", password="student123")

        # Create multiple assignments with grades
        assignments_data = [
            ("Homework 1", self.homework_category, 20, 18.0),  # 90%
            ("Homework 2", self.homework_category, 20, 16.0),  # 80%
            ("Quiz 1", self.quiz_category, 50, 45.0),  # 90%
            ("Quiz 2", self.quiz_category, 50, 40.0),  # 80%
            ("Test 1", self.test_category, 100, 85.0),  # 85%
        ]

        for name, category, max_points, earned_points in assignments_data:
            assignment = Assignment.objects.create(
                section=self.section,
                category=category,
                name=name,
                assigned_date=date.today() - timedelta(days=10),
                due_date=date.today() - timedelta(days=5),
                max_points=max_points,
                is_published=True,
            )

            Grade.objects.create(
                enrollment=self.enrollment,
                assignment=assignment,
                points_earned=earned_points,
                graded_by=self.teacher_user,
                graded_date=timezone.now(),
            )

        # Test grades view
        response = self.client.get(reverse("student_portal:grades"))
        self.assertEqual(response.status_code, 200)

        # Verify all grades are displayed
        for name, _, max_points, earned_points in assignments_data:
            self.assertContains(response, name)
            self.assertContains(response, str(earned_points))
            percentage = (earned_points / max_points) * 100
            self.assertContains(response, f"{percentage}%")

        # Test individual grade details
        grades = Grade.objects.filter(enrollment=self.enrollment)
        for grade in grades:
            detail_response = self.client.get(
                reverse("student_portal:grade_details", args=[grade.id]),
                HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            )
            self.assertEqual(detail_response.status_code, 200)

            data = json.loads(detail_response.content)
            self.assertEqual(data["points_earned"], grade.points_earned)
            self.assertEqual(data["max_points"], grade.assignment.max_points)

    def test_schedule_and_enrollment_workflow(self):
        """Test schedule viewing and enrollment information workflow."""
        # Create additional courses and enrollments
        english_dept = Department.objects.create(name="English")
        english_course = Course.objects.create(
            name="English Literature", course_code="ENG10", department=english_dept
        )
        english_section = CourseSection.objects.create(
            course=english_course,
            teacher=self.teacher_user,
            school_year=self.school_year,
            section_name="B",
            room="Eng201",
        )
        english_enrollment = Enrollment.objects.create(
            student=self.student, section=english_section
        )

        # Login and test schedule view
        self.client.login(username="student", password="student123")
        response = self.client.get(reverse("student_portal:schedule"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My Schedule")

        # Verify both courses are shown
        self.assertContains(response, "Algebra II")
        self.assertContains(response, "English Literature")
        self.assertContains(response, "Math101")  # Room
        self.assertContains(response, "Eng201")  # Room

        # Check enrollments in context
        enrollments = response.context["enrollments"]
        self.assertEqual(len(enrollments), 2)
        self.assertIn(self.enrollment, enrollments)
        self.assertIn(english_enrollment, enrollments)

    def test_announcement_workflow(self):
        """Test announcement viewing and filtering workflow."""
        # Create announcements for different audiences
        student_announcement = Announcement.objects.create(
            title="Student Announcement",
            content="Important message for students.",
            audience="STUDENTS",
            is_published=True,
            created_by=self.teacher_user,
            publish_date=timezone.now(),
        )

        parent_announcement = Announcement.objects.create(
            title="Parent Announcement",
            content="Message for parents only.",
            audience="PARENTS",
            is_published=True,
            created_by=self.teacher_user,
            publish_date=timezone.now(),
        )

        all_announcement = Announcement.objects.create(
            title="All Announcement",
            content="Message for everyone.",
            audience="ALL",
            is_published=True,
            created_by=self.teacher_user,
            publish_date=timezone.now(),
        )

        unpublished_announcement = Announcement.objects.create(
            title="Draft Announcement",
            content="Not published yet.",
            audience="STUDENTS",
            is_published=False,
            created_by=self.teacher_user,
        )

        # Test announcements view
        self.client.login(username="student", password="student123")
        response = self.client.get(reverse("student_portal:announcements"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Announcements")

        # Should see student and all announcements
        self.assertContains(response, "Student Announcement")
        self.assertContains(response, "All Announcement")

        # Should not see parent or unpublished announcements
        self.assertNotContains(response, "Parent Announcement")
        self.assertNotContains(response, "Draft Announcement")

    def test_profile_management_workflow(self):
        """Test student profile viewing and basic information workflow."""
        self.client.login(username="student", password="student123")
        response = self.client.get(reverse("student_portal:profile"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "My Profile")

        # Verify student information is displayed
        self.assertContains(response, "John Doe")
        self.assertContains(response, "ST001")  # Student ID
        self.assertContains(response, "10th Grade")
        self.assertContains(response, "student@test.com")

        # Verify student object in context
        self.assertEqual(response.context["student"], self.student)

    def test_error_handling_workflow(self):
        """Test error handling in common user workflows."""
        # Test without login
        protected_urls = [
            reverse("student_portal:dashboard"),
            reverse("student_portal:assignments"),
            reverse("student_portal:grades"),
        ]

        for url in protected_urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)  # Redirect to login

        # Test with login but invalid data
        self.client.login(username="student", password="student123")

        # Invalid assignment ID
        response = self.client.get(
            reverse("student_portal:assignment_detail", args=[99999])
        )
        self.assertEqual(response.status_code, 404)

        # Invalid grade ID for AJAX
        response = self.client.get(
            reverse("student_portal:grade_details", args=[99999]),
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )
        self.assertEqual(response.status_code, 404)

    def test_performance_workflow(self):
        """Test performance with realistic data volumes."""
        # Create larger dataset
        categories = [self.homework_category, self.quiz_category, self.test_category]

        # Create 50 assignments
        for i in range(50):
            assignment = Assignment.objects.create(
                section=self.section,
                category=categories[i % 3],
                name=f"Assignment {i + 1}",
                assigned_date=date.today() - timedelta(days=60 - i),
                due_date=date.today() - timedelta(days=50 - i),
                max_points=100,
                is_published=True,
            )

            # Create grade for 80% of assignments
            if i % 5 != 0:  # Skip every 5th assignment
                Grade.objects.create(
                    enrollment=self.enrollment,
                    assignment=assignment,
                    points_earned=float(70 + (i % 30)),  # Vary grades
                    graded_by=self.teacher_user,
                    graded_date=timezone.now(),
                )

        # Test that views still perform well
        self.client.login(username="student", password="student123")

        # Time-sensitive test - should complete reasonably quickly
        import time

        start_time = time.time()
        response = self.client.get(reverse("student_portal:assignments"))
        end_time = time.time()

        self.assertEqual(response.status_code, 200)
        self.assertLess(
            end_time - start_time, 2.0
        )  # Should complete in under 2 seconds

        # Test grades view performance
        start_time = time.time()
        response = self.client.get(reverse("student_portal:grades"))
        end_time = time.time()

        self.assertEqual(response.status_code, 200)
        self.assertLess(
            end_time - start_time, 2.0
        )  # Should complete in under 2 seconds


class AdminWorkflowIntegrationTests(TestCase):
    """Integration tests for admin workflows."""

    def setUp(self):
        """Set up admin test data."""
        self.client = Client()
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@test.com", password="admin123"
        )

    def test_admin_dashboard_workflow(self):
        """Test admin dashboard access and functionality."""
        # Login as admin
        login_response = self.client.post(
            reverse("login"), {"username": "admin", "password": "admin123"}
        )
        self.assertEqual(login_response.status_code, 302)

        # Access admin dashboard
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Admin Dashboard")

        # Check for admin-specific content
        self.assertContains(response, "Analytics")
        self.assertContains(response, "Management")

    def test_data_management_workflow(self):
        """Test sample data population workflow."""
        self.client.login(username="admin", password="admin123")

        # This would test the populate_sample_data command workflow
        # In a real scenario, this might be triggered via admin interface
        from django.core.management import call_command

        # Test that command runs without errors
        try:
            call_command("populate_sample_data", verbosity=0)
            success = True
        except Exception:
            success = False

        self.assertTrue(success)

        # Verify data was created
        from students.models import Student
        from academics.models import Assignment

        self.assertGreater(Student.objects.count(), 0)
        self.assertGreater(Assignment.objects.count(), 0)


class AdmissionWorkflowIntegrationTests(TestCase):
    """Integration tests for admission workflows."""

    def setUp(self):
        """Set up admission test data."""
        self.client = Client()
        self.admission_level = AdmissionLevel.objects.create(
            name="Application Submitted", order=1
        )

    def test_applicant_creation_workflow(self):
        """Test applicant creation and management workflow."""
        # Create applicant
        applicant = Applicant.objects.create(
            first_name="Jane",
            last_name="Smith",
            email="jane.smith@example.com",
            date_of_birth=date(2009, 3, 15),
            current_level=self.admission_level,
            application_date=date.today(),
        )

        # Verify applicant was created correctly
        self.assertEqual(str(applicant), "Jane Smith")
        self.assertEqual(applicant.current_level, self.admission_level)
        self.assertIsNotNone(applicant.application_date)

        # Test that applicant appears in admin
        from django.contrib.admin.sites import site
        from admissions.models import Applicant

        self.assertTrue(Applicant in site._registry)
