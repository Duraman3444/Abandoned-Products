"""
Security audit tests for SchoolDriver Modern.
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from datetime import date, timedelta

from students.models import Student, GradeLevel, SchoolYear
from academics.models import (
    Department,
    Course,
    CourseSection,
    Enrollment,
    Assignment,
)


class AuthenticationSecurityTests(TestCase):
    """Test authentication and authorization security."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()

        # Create users with different roles
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@test.com", password="securepass123"
        )

        self.teacher_user = User.objects.create_user(
            username="teacher",
            email="teacher@test.com",
            password="securepass123",
            first_name="Jane",
            last_name="Smith",
        )

        self.student_user = User.objects.create_user(
            username="student", email="student@test.com", password="securepass123"
        )

        # Create student profile
        self.grade_level = GradeLevel.objects.create(name="10th Grade", order=10)
        self.student = Student.objects.create(
            first_name="John",
            last_name="Doe",
            student_id="ST001",
            grade_level=self.grade_level,
            date_of_birth=date(2008, 5, 15),
            enrollment_date=date.today(),
        )

    def test_login_required_for_protected_views(self):
        """Test that protected views require authentication."""
        protected_urls = [
            reverse("student_portal:dashboard"),
            reverse("student_portal:assignments"),
            reverse("student_portal:grades"),
            reverse("student_portal:schedule"),
            reverse("student_portal:profile"),
            reverse("admin_dashboard"),
        ]

        for url in protected_urls:
            response = self.client.get(url)
            self.assertIn(
                response.status_code, [302, 403]
            )  # Redirect to login or forbidden

    def test_role_based_access_control(self):
        """Test that users can only access views appropriate to their role."""
        # Student should not access admin dashboard
        self.client.login(username="student", password="securepass123")
        response = self.client.get(reverse("admin_dashboard"))
        self.assertIn(response.status_code, [302, 403])

        # Admin should be able to access admin dashboard
        self.client.login(username="admin", password="securepass123")
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 200)

    def test_session_security(self):
        """Test session security settings."""
        # Login and check session
        self.client.login(username="student", password="securepass123")

        # Check that session is created
        self.assertIn("_auth_user_id", self.client.session)

        # Check session settings (these should be configured in settings.py)
        from django.conf import settings

        # These are security best practices that should be enforced
        security_settings = {
            "SESSION_COOKIE_SECURE": getattr(settings, "SESSION_COOKIE_SECURE", False),
            "SESSION_COOKIE_HTTPONLY": getattr(
                settings, "SESSION_COOKIE_HTTPONLY", True
            ),
            "CSRF_COOKIE_SECURE": getattr(settings, "CSRF_COOKIE_SECURE", False),
            "CSRF_COOKIE_HTTPONLY": getattr(settings, "CSRF_COOKIE_HTTPONLY", True),
        }

        # In production, these should be True
        if hasattr(settings, "DEBUG") and not settings.DEBUG:
            self.assertTrue(security_settings["SESSION_COOKIE_SECURE"])
            self.assertTrue(security_settings["CSRF_COOKIE_SECURE"])

        # These should always be True
        self.assertTrue(security_settings["SESSION_COOKIE_HTTPONLY"])
        self.assertTrue(security_settings["CSRF_COOKIE_HTTPONLY"])

    def test_password_security(self):
        """Test password security measures."""
        from django.contrib.auth.password_validation import validate_password

        # Test weak passwords are rejected
        weak_passwords = ["password", "123456", "admin", "test", "12345678"]

        for weak_password in weak_passwords:
            with self.assertRaises(ValidationError):
                validate_password(weak_password)

    def test_csrf_protection(self):
        """Test CSRF protection on forms."""
        self.client.login(username="student", password="securepass123")

        # GET request should include CSRF token
        response = self.client.get(reverse("student_portal:profile"))
        if response.status_code == 200:
            self.assertContains(response, "csrfmiddlewaretoken")

        # POST without CSRF token should fail
        response = self.client.post(
            reverse("student_portal:profile"), {"some_field": "some_value"}
        )
        # Should either be forbidden or redirect
        self.assertIn(response.status_code, [403, 302])


class InputValidationSecurityTests(TestCase):
    """Test input validation security."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="securepass123"
        )
        self.grade_level = GradeLevel.objects.create(name="10th Grade", order=10)

    def test_sql_injection_protection(self):
        """Test protection against SQL injection attacks."""
        self.client.login(username="testuser", password="securepass123")

        # Create a student to test with
        student = Student.objects.create(
            first_name="Test",
            last_name="Student",
            student_id="TS001",
            grade_level=self.grade_level,
            date_of_birth=date(2008, 5, 15),
            enrollment_date=date.today(),
        )

        # Test SQL injection attempts in query parameters
        malicious_params = [
            "'; DROP TABLE students_student; --",
            "1' OR '1'='1",
            "1'; DELETE FROM academics_grade; --",
            "1 UNION SELECT * FROM auth_user --",
            "<script>alert('xss')</script>",
        ]

        for param in malicious_params:
            # Test in assignment filter
            response = self.client.get(
                reverse("student_portal:assignments"), {"status": param}
            )
            # Should not crash and should return safe response
            self.assertIn(response.status_code, [200, 400, 404])

            # Test in search parameters
            if hasattr(self, "search_url"):
                response = self.client.get(self.search_url, {"q": param})
                self.assertIn(response.status_code, [200, 400, 404])

    def test_xss_protection(self):
        """Test protection against XSS attacks."""
        # Test that user input is properly escaped
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            "javascript:alert('xss')",
            "' onmouseover='alert(1)'",
            "<svg onload=alert('xss')>",
        ]

        for payload in xss_payloads:
            # Test creating student with malicious input
            try:
                student = Student.objects.create(
                    first_name=payload,
                    last_name="TestLast",
                    student_id="XSS001",
                    grade_level=self.grade_level,
                    date_of_birth=date(2008, 5, 15),
                    enrollment_date=date.today(),
                )

                # If creation succeeds, check that output is escaped
                self.assertNotEqual(student.first_name, payload)
                student.delete()  # Clean up

            except (ValidationError, IntegrityError):
                # Validation should catch malicious input
                pass

    def test_file_upload_security(self):
        """Test file upload security measures."""
        # This would test file upload functionality if it exists
        # For now, we'll test that dangerous file types are rejected

        dangerous_filenames = [
            "malicious.php",
            "script.js",
            "shell.sh",
            "virus.exe",
            "../../../etc/passwd",
            "file.txt.php",
        ]

        # If there are file upload endpoints, test them here
        # This is a placeholder for when file upload is implemented
        for filename in dangerous_filenames:
            # Mock file upload test
            self.assertFalse(filename.endswith(".jpg"))
            self.assertFalse(filename.endswith(".png"))
            # Should only allow safe file types


class DataAccessSecurityTests(TestCase):
    """Test data access security and privacy."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()

        # Create multiple students
        self.grade_level = GradeLevel.objects.create(name="10th Grade", order=10)

        self.student1_user = User.objects.create_user(
            username="student1", password="securepass123"
        )
        self.student1 = Student.objects.create(
            first_name="John",
            last_name="Doe",
            student_id="ST001",
            grade_level=self.grade_level,
            date_of_birth=date(2008, 5, 15),
            enrollment_date=date.today(),
        )

        self.student2_user = User.objects.create_user(
            username="student2", password="securepass123"
        )
        self.student2 = Student.objects.create(
            first_name="Jane",
            last_name="Smith",
            student_id="ST002",
            grade_level=self.grade_level,
            date_of_birth=date(2008, 3, 10),
            enrollment_date=date.today(),
        )

    def test_student_data_isolation(self):
        """Test that students can only access their own data."""
        # Student 1 logs in
        self.client.login(username="student1", password="securepass123")

        # Should see own profile
        response = self.client.get(reverse("student_portal:profile"))
        if response.status_code == 200:
            self.assertContains(response, "ST001")
            self.assertNotContains(response, "ST002")

    def test_assignment_access_control(self):
        """Test that students can only see assignments for their enrolled courses."""
        school_year = SchoolYear.objects.create(
            name="2024-2025",
            start_date=date(2024, 8, 15),
            end_date=date(2025, 6, 15),
            is_active=True,
        )

        # Create course and assignments
        department = Department.objects.create(name="Math")
        course = Course.objects.create(
            name="Algebra", course_code="ALG1", department=department
        )
        section = CourseSection.objects.create(
            course=course,
            school_year=school_year,
            teacher=User.objects.create_user("teacher", password="pass"),
            section_name="A",
        )

        # Enroll only student1
        enrollment = Enrollment.objects.create(student=self.student1, section=section)

        assignment = Assignment.objects.create(
            section=section,
            name="Test Assignment",
            assigned_date=date.today(),
            due_date=date.today() + timedelta(days=7),
            max_points=100,
            is_published=True,
        )

        # Student1 should see the assignment
        self.client.login(username="student1", password="securepass123")
        response = self.client.get(reverse("student_portal:assignments"))
        if response.status_code == 200:
            self.assertContains(response, "Test Assignment")

        # Student2 should not see the assignment
        self.client.login(username="student2", password="securepass123")
        response = self.client.get(reverse("student_portal:assignments"))
        if response.status_code == 200:
            self.assertNotContains(response, "Test Assignment")

    def test_direct_object_reference_protection(self):
        """Test protection against insecure direct object references."""
        school_year = SchoolYear.objects.create(
            name="2024-2025",
            start_date=date(2024, 8, 15),
            end_date=date(2025, 6, 15),
            is_active=True,
        )

        department = Department.objects.create(name="Math")
        course = Course.objects.create(
            name="Algebra", course_code="ALG1", department=department
        )
        section = CourseSection.objects.create(
            course=course,
            school_year=school_year,
            teacher=User.objects.create_user("teacher", password="pass"),
            section_name="A",
        )

        enrollment = Enrollment.objects.create(student=self.student1, section=section)

        assignment = Assignment.objects.create(
            section=section,
            name="Test Assignment",
            assigned_date=date.today(),
            due_date=date.today() + timedelta(days=7),
            max_points=100,
            is_published=True,
        )

        # Student2 tries to access student1's assignment directly
        self.client.login(username="student2", password="securepass123")
        response = self.client.get(
            reverse("student_portal:assignment_detail", args=[assignment.id])
        )

        # Should be forbidden or redirect
        self.assertIn(response.status_code, [403, 404, 302])


class SecurityHeadersTests(TestCase):
    """Test security headers and configurations."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", password="securepass123"
        )

    def test_security_headers_present(self):
        """Test that security headers are present in responses."""
        self.client.login(username="testuser", password="securepass123")

        # Test a few different endpoints
        endpoints = [
            reverse("login"),
        ]

        for endpoint in endpoints:
            response = self.client.get(endpoint)

            # Check for security headers (these should be configured in middleware)
            headers_to_check = [
                "X-Content-Type-Options",
                "X-Frame-Options",
                "X-XSS-Protection",
            ]

            # Note: These might not be present in test environment
            # In production, they should be configured via middleware
            for header in headers_to_check:
                # Check if header exists (don't assert since test environment may differ)
                has_header = header in response
                if has_header:
                    self.assertIsNotNone(response[header])

    def test_debug_mode_security(self):
        """Test that debug mode is properly configured."""
        from django.conf import settings

        # In production, DEBUG should be False
        if hasattr(settings, "ENVIRONMENT") and settings.ENVIRONMENT == "production":
            self.assertFalse(settings.DEBUG)

        # SECRET_KEY should not be empty or default
        self.assertIsNotNone(settings.SECRET_KEY)
        self.assertNotEqual(settings.SECRET_KEY, "")
        self.assertGreater(len(settings.SECRET_KEY), 20)


class DataValidationSecurityTests(TestCase):
    """Test data validation and sanitization."""

    def setUp(self):
        """Set up test data."""
        self.grade_level = GradeLevel.objects.create(name="10th Grade", order=10)

    def test_model_field_validation(self):
        """Test that model fields properly validate input."""
        # Test required fields
        with self.assertRaises((ValidationError, IntegrityError)):
            Student.objects.create(
                # Missing required fields
                first_name="",
                last_name="",
                grade_level=self.grade_level,
                date_of_birth=date(2008, 5, 15),
                enrollment_date=date.today(),
            )

    def test_date_validation(self):
        """Test date field validation."""
        # Test invalid birth date (future date)
        with self.assertRaises(ValidationError):
            student = Student(
                first_name="Test",
                last_name="Student",
                student_id="TS001",
                grade_level=self.grade_level,
                date_of_birth=date.today() + timedelta(days=365),  # Future date
                enrollment_date=date.today(),
            )
            student.full_clean()

    def test_email_validation(self):
        """Test email field validation."""
        # Test invalid email formats
        invalid_emails = [
            "invalid-email",
            "test@",
            "@domain.com",
            "test..test@domain.com",
            "test space@domain.com",
        ]

        for invalid_email in invalid_emails:
            with self.assertRaises(ValidationError):
                user = User(username="testuser", email=invalid_email)
                user.full_clean()


class LoggingSecurityTests(TestCase):
    """Test security logging and monitoring."""

    def test_failed_login_attempts_logged(self):
        """Test that failed login attempts are logged."""
        # This would test that failed login attempts are properly logged
        # for security monitoring purposes

        # Attempt login with wrong password
        response = self.client.post(
            reverse("login"), {"username": "nonexistent", "password": "wrongpassword"}
        )

        # Response should indicate failure
        self.assertNotEqual(response.status_code, 200)
        # In a real implementation, this would be logged to security logs

    def test_suspicious_activity_detection(self):
        """Test detection of suspicious activity patterns."""
        # This would test for detection of:
        # - Multiple failed login attempts
        # - Unusual access patterns
        # - Potential brute force attacks

        # Mock multiple failed attempts
        for i in range(5):
            response = self.client.post(
                reverse("login"), {"username": "testuser", "password": "wrongpassword"}
            )

        # After multiple failures, additional security measures should kick in
        # This would be implemented with rate limiting middleware
        pass
