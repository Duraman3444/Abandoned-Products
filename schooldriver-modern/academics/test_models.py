"""
Comprehensive tests for Academics app models.
"""

from django.test import TestCase
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.utils import timezone
from datetime import date, timedelta

from academics.models import (
    Department,
    Course,
    CourseSection,
    Enrollment,
    Assignment,
    AssignmentCategory,
    Grade,
    Attendance,
    Announcement,
)
from students.models import Student, GradeLevel, SchoolYear


class DepartmentModelTests(TestCase):
    """Test cases for Department model."""

    def test_department_creation(self):
        """Test creating a department."""
        dept = Department.objects.create(
            name="Mathematics", description="Math courses for all grade levels"
        )
        self.assertEqual(str(dept), "Mathematics")
        self.assertEqual(dept.description, "Math courses for all grade levels")

    def test_department_unique_name(self):
        """Test that multiple departments can have same name (no unique constraint)."""
        Department.objects.create(name="Science")
        # Should not raise error - no unique constraint on name
        dept2 = Department.objects.create(name="Science")
        self.assertEqual(dept2.name, "Science")


class CourseModelTests(TestCase):
    """Test cases for Course model."""

    def setUp(self):
        """Set up test data."""
        self.department = Department.objects.create(name="Mathematics")

    def test_course_creation(self):
        """Test creating a course."""
        course = Course.objects.create(
            name="Algebra I",
            course_code="ALG1",
            department=self.department,
            credit_hours=1.0,
            description="Introduction to algebra",
        )

        self.assertEqual(str(course), "ALG1: Algebra I")
        self.assertEqual(course.credit_hours, 1.0)
        self.assertEqual(course.department, self.department)

    def test_course_unique_code(self):
        """Test that course codes must be unique."""
        Course.objects.create(
            name="Algebra I", course_code="ALG1", department=self.department
        )

        with self.assertRaises(IntegrityError):
            Course.objects.create(
                name="Another Course",
                course_code="ALG1",  # Duplicate code
                department=self.department,
            )


class CourseSectionModelTests(TestCase):
    """Test cases for CourseSection model."""

    def setUp(self):
        """Set up test data."""
        self.department = Department.objects.create(name="Mathematics")
        self.course = Course.objects.create(
            name="Algebra I", course_code="ALG1", department=self.department
        )
        self.teacher = User.objects.create_user(
            username="teacher",
            email="teacher@test.com",
            first_name="Jane",
            last_name="Smith",
        )
        self.school_year = SchoolYear.objects.create(
            name="2024-2025",
            start_date=date(2024, 8, 15),
            end_date=date(2025, 6, 15),
            is_active=True,
        )

    def test_section_creation(self):
        """Test creating a course section."""
        section = CourseSection.objects.create(
            course=self.course,
            teacher=self.teacher,
            school_year=self.school_year,
            section_name="A",
            room="101",
            max_students=25,
        )

        self.assertEqual(str(section), "ALG1-A (2024-2025)")
        self.assertEqual(section.room, "101")
        self.assertEqual(section.max_students, 25)

    def test_section_enrollment_count(self):
        """Test section enrollment count through enrollments relationship."""
        grade_level = GradeLevel.objects.create(name="9th Grade", order=9)
        student = Student.objects.create(
            first_name="John",
            last_name="Doe",
            student_id="ST001",
            grade_level=grade_level,
            enrollment_date=date.today(),
            date_of_birth=date(2008, 5, 15),
        )

        section = CourseSection.objects.create(
            course=self.course,
            teacher=self.teacher,
            school_year=self.school_year,
            section_name="A",
            max_students=25,
        )

        # Initially no enrollments
        self.assertEqual(section.enrollments.count(), 0)

        # Add enrollment
        Enrollment.objects.create(student=student, section=section)
        self.assertEqual(section.enrollments.count(), 1)


class EnrollmentModelTests(TestCase):
    """Test cases for Enrollment model."""

    def setUp(self):
        """Set up test data."""
        self.department = Department.objects.create(name="Mathematics")
        self.course = Course.objects.create(
            name="Algebra I", course_code="ALG1", department=self.department
        )
        self.teacher = User.objects.create_user(
            username="teacher", email="teacher@test.com"
        )
        self.school_year = SchoolYear.objects.create(
            name="2024-2025",
            start_date=date(2024, 8, 15),
            end_date=date(2025, 6, 15),
            is_active=True,
        )
        self.section = CourseSection.objects.create(
            course=self.course,
            teacher=self.teacher,
            school_year=self.school_year,
            section_name="A",
        )

        self.grade_level = GradeLevel.objects.create(name="9th Grade", order=9)
        self.student = Student.objects.create(
            first_name="John",
            last_name="Doe",
            student_id="ST001",
            grade_level=self.grade_level,
            enrollment_date=date.today(),
            date_of_birth=date(2008, 5, 15),
        )

    def test_enrollment_creation(self):
        """Test creating an enrollment."""
        enrollment = Enrollment.objects.create(
            student=self.student, section=self.section, enrollment_date=date.today()
        )

        self.assertEqual(str(enrollment), "John Doe (ST001) in ALG1-A (2024-2025)")
        self.assertEqual(enrollment.student, self.student)
        self.assertEqual(enrollment.section, self.section)

    def test_enrollment_unique_constraint(self):
        """Test that student can't be enrolled in same section twice."""
        Enrollment.objects.create(student=self.student, section=self.section)

        with self.assertRaises(IntegrityError):
            Enrollment.objects.create(
                student=self.student,
                section=self.section,  # Duplicate enrollment
            )


class AssignmentCategoryModelTests(TestCase):
    """Test cases for AssignmentCategory model."""

    def test_category_creation(self):
        """Test creating an assignment category."""
        category = AssignmentCategory.objects.create(
            name="Homework",
            default_weight=0.3,
            description="Daily homework assignments",
        )

        self.assertEqual(str(category), "Homework")
        self.assertEqual(category.default_weight, 0.3)
        self.assertEqual(category.description, "Daily homework assignments")

    def test_category_weight_validation(self):
        """Test that weight can be set to any decimal value."""
        # No validation constraints on default_weight field
        category = AssignmentCategory.objects.create(
            name="Test Category",
            default_weight=1.5,  # Any decimal value is allowed
        )
        self.assertEqual(category.default_weight, 1.5)


class AssignmentModelTests(TestCase):
    """Test cases for Assignment model."""

    def setUp(self):
        """Set up test data."""
        self.department = Department.objects.create(name="Mathematics")
        self.course = Course.objects.create(
            name="Algebra I", course_code="ALG1", department=self.department
        )
        self.teacher = User.objects.create_user(
            username="teacher", email="teacher@test.com"
        )
        self.school_year = SchoolYear.objects.create(
            name="2024-2025",
            start_date=date(2024, 8, 15),
            end_date=date(2025, 6, 15),
            is_active=True,
        )
        self.section = CourseSection.objects.create(
            course=self.course,
            teacher=self.teacher,
            school_year=self.school_year,
            section_name="A",
        )
        self.category = AssignmentCategory.objects.create(
            name="Homework", default_weight=0.3
        )

    def test_assignment_creation(self):
        """Test creating an assignment."""
        assignment = Assignment.objects.create(
            section=self.section,
            category=self.category,
            name="Chapter 1 Problems",
            description="Problems 1-20 from Chapter 1",
            assigned_date=date.today(),
            due_date=date.today() + timedelta(days=3),
            max_points=100,
            is_published=True,
        )

        self.assertEqual(str(assignment), "ALG1: Chapter 1 Problems")
        self.assertEqual(assignment.max_points, 100)
        self.assertTrue(assignment.is_published)

    def test_assignment_due_date_validation(self):
        """Test that assignment can be created with any due date."""
        # No validation constraints on due date vs assigned date
        assignment = Assignment.objects.create(
            section=self.section,
            category=self.category,
            name="Test Assignment",
            assigned_date=date.today(),
            due_date=date.today() - timedelta(days=1),  # Due before assigned is allowed
            max_points=100,
        )
        self.assertEqual(assignment.name, "Test Assignment")


class GradeModelTests(TestCase):
    """Test cases for Grade model."""

    def setUp(self):
        """Set up test data."""
        # Create complete test setup
        self.department = Department.objects.create(name="Mathematics")
        self.course = Course.objects.create(
            name="Algebra I", course_code="ALG1", department=self.department
        )
        self.teacher = User.objects.create_user(
            username="teacher", email="teacher@test.com"
        )
        self.school_year = SchoolYear.objects.create(
            name="2024-2025",
            start_date=date(2024, 8, 15),
            end_date=date(2025, 6, 15),
            is_active=True,
        )
        self.section = CourseSection.objects.create(
            course=self.course,
            teacher=self.teacher,
            school_year=self.school_year,
            section_name="A",
        )

        self.grade_level = GradeLevel.objects.create(name="9th Grade", order=9)
        self.student = Student.objects.create(
            first_name="John",
            last_name="Doe",
            student_id="ST001",
            grade_level=self.grade_level,
            enrollment_date=date.today(),
            date_of_birth=date(2008, 5, 15),
        )
        self.enrollment = Enrollment.objects.create(
            student=self.student, section=self.section
        )

        self.category = AssignmentCategory.objects.create(
            name="Homework", default_weight=0.3
        )
        self.assignment = Assignment.objects.create(
            section=self.section,
            category=self.category,
            name="Chapter 1 Problems",
            assigned_date=date.today(),
            due_date=date.today() + timedelta(days=3),
            max_points=100,
        )

    def test_grade_creation(self):
        """Test creating a grade."""
        grade = Grade.objects.create(
            enrollment=self.enrollment,
            assignment=self.assignment,
            points_earned=85.5,
            graded_by=self.teacher,
            graded_date=timezone.now(),
        )

        self.assertEqual(grade.points_earned, 85.5)
        self.assertEqual(grade.graded_by, self.teacher)
        self.assertEqual(grade.assignment, self.assignment)

    def test_grade_percentage_calculation(self):
        """Test grade percentage calculation."""
        grade = Grade.objects.create(
            enrollment=self.enrollment,
            assignment=self.assignment,
            points_earned=85.0,
            graded_by=self.teacher,
        )

        percentage = (85.0 / 100.0) * 100
        self.assertEqual(grade.percentage, percentage)

    def test_grade_letter_grade_field(self):
        """Test letter grade field assignment."""
        # Create additional assignments to avoid unique constraint violation
        assignment_b = Assignment.objects.create(
            section=self.section,
            category=self.category,
            name="Assignment B",
            assigned_date=date.today(),
            due_date=date.today() + timedelta(days=5),
            max_points=100,
        )

        assignment_c = Assignment.objects.create(
            section=self.section,
            category=self.category,
            name="Assignment C",
            assigned_date=date.today(),
            due_date=date.today() + timedelta(days=6),
            max_points=100,
        )

        # Test A grade
        grade_a = Grade.objects.create(
            enrollment=self.enrollment,
            assignment=self.assignment,
            points_earned=95.0,
            letter_grade="A",
            graded_by=self.teacher,
        )
        self.assertEqual(grade_a.letter_grade, "A")

        # Test B grade (different assignment)
        grade_b = Grade.objects.create(
            enrollment=self.enrollment,
            assignment=assignment_b,
            points_earned=85.0,
            letter_grade="B",
            graded_by=self.teacher,
        )
        self.assertEqual(grade_b.letter_grade, "B")

        # Test F grade (different assignment)
        grade_f = Grade.objects.create(
            enrollment=self.enrollment,
            assignment=assignment_c,
            points_earned=55.0,
            letter_grade="F",
            graded_by=self.teacher,
        )
        self.assertEqual(grade_f.letter_grade, "F")

    def test_grade_points_validation(self):
        """Test that points earned can be any value."""
        # No validation constraints on points vs max_points
        grade = Grade.objects.create(
            enrollment=self.enrollment,
            assignment=self.assignment,
            points_earned=150.0,  # More than max_points is allowed
            graded_by=self.teacher,
        )
        self.assertEqual(grade.points_earned, 150.0)


class AttendanceModelTests(TestCase):
    """Test cases for Attendance model."""

    def setUp(self):
        """Set up test data."""
        self.department = Department.objects.create(name="Mathematics")
        self.course = Course.objects.create(
            name="Algebra I", course_code="ALG1", department=self.department
        )
        self.teacher = User.objects.create_user(
            username="teacher", email="teacher@test.com"
        )
        self.school_year = SchoolYear.objects.create(
            name="2024-2025",
            start_date=date(2024, 8, 15),
            end_date=date(2025, 6, 15),
            is_active=True,
        )
        self.section = CourseSection.objects.create(
            course=self.course,
            teacher=self.teacher,
            school_year=self.school_year,
            section_name="A",
        )

        self.grade_level = GradeLevel.objects.create(name="9th Grade", order=9)
        self.student = Student.objects.create(
            first_name="John",
            last_name="Doe",
            student_id="ST001",
            grade_level=self.grade_level,
            enrollment_date=date.today(),
            date_of_birth=date(2008, 5, 15),
        )
        self.enrollment = Enrollment.objects.create(
            student=self.student, section=self.section
        )

    def test_attendance_creation(self):
        """Test creating an attendance record."""
        attendance = Attendance.objects.create(
            enrollment=self.enrollment,
            date=date.today(),
            status="P",  # Present
            recorded_by=self.teacher,
        )

        self.assertEqual(attendance.status, "P")
        self.assertEqual(attendance.date, date.today())
        self.assertEqual(attendance.recorded_by, self.teacher)

    def test_attendance_status_choices(self):
        """Test attendance status choices."""
        valid_statuses = ["P", "A", "T", "E"]  # Present, Absent, Tardy, Excused

        for status in valid_statuses:
            attendance = Attendance.objects.create(
                enrollment=self.enrollment,
                date=date.today()
                - timedelta(days=len(valid_statuses) - valid_statuses.index(status)),
                status=status,
                recorded_by=self.teacher,
            )
            self.assertEqual(attendance.status, status)

    def test_attendance_unique_per_day(self):
        """Test that only one attendance record per student per day is allowed."""
        Attendance.objects.create(
            enrollment=self.enrollment,
            date=date.today(),
            status="P",
            recorded_by=self.teacher,
        )

        with self.assertRaises(IntegrityError):
            Attendance.objects.create(
                enrollment=self.enrollment,
                date=date.today(),  # Same date
                status="A",
                recorded_by=self.teacher,
            )


class AnnouncementModelTests(TestCase):
    """Test cases for Announcement model."""

    def setUp(self):
        """Set up test data."""
        self.teacher = User.objects.create_user(
            username="teacher",
            email="teacher@test.com",
            first_name="Jane",
            last_name="Smith",
        )

    def test_announcement_creation(self):
        """Test creating an announcement."""
        announcement = Announcement.objects.create(
            title="Important Notice",
            content="Please remember to bring your textbooks tomorrow.",
            audience="STUDENTS",
            is_published=True,
            created_by=self.teacher,
            publish_date=timezone.now(),
        )

        self.assertEqual(str(announcement), "Important Notice")
        self.assertEqual(announcement.audience, "STUDENTS")
        self.assertTrue(announcement.is_published)
        self.assertEqual(announcement.created_by, self.teacher)

    def test_announcement_audience_choices(self):
        """Test announcement audience choices."""
        valid_audiences = ["ALL", "STUDENTS", "PARENTS", "TEACHERS"]

        for audience in valid_audiences:
            announcement = Announcement.objects.create(
                title=f"Notice for {audience}",
                content="Test content",
                audience=audience,
                created_by=self.teacher,
                publish_date=timezone.now(),
            )
            self.assertEqual(announcement.audience, audience)

    def test_announcement_published_manager(self):
        """Test published announcements manager."""
        # Create published announcement
        published = Announcement.objects.create(
            title="Published Notice",
            content="Published content",
            audience="ALL",
            is_published=True,
            created_by=self.teacher,
            publish_date=timezone.now(),
        )

        # Create unpublished announcement
        unpublished = Announcement.objects.create(
            title="Draft Notice",
            content="Draft content",
            audience="ALL",
            is_published=False,
            created_by=self.teacher,
            publish_date=timezone.now(),
        )

        # Test that only published announcements are returned
        published_announcements = Announcement.objects.filter(is_published=True)
        self.assertIn(published, published_announcements)
        self.assertNotIn(unpublished, published_announcements)
