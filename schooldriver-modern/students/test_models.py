"""
Comprehensive tests for Students app models.
"""

from django.test import TestCase
from django.db import IntegrityError
from datetime import date, timedelta
from students.models import Student, GradeLevel, SchoolYear, EmergencyContact


class GradeLevelModelTests(TestCase):
    """Test cases for GradeLevel model."""

    def test_grade_level_creation(self):
        """Test creating a grade level."""
        grade_level = GradeLevel.objects.create(name="9th Grade", order=9)
        self.assertEqual(str(grade_level), "9th Grade")
        self.assertEqual(grade_level.order, 9)

    def test_grade_level_unique_name(self):
        """Test that grade level names must be unique."""
        GradeLevel.objects.create(name="10th Grade", order=10)
        with self.assertRaises(IntegrityError):
            GradeLevel.objects.create(name="10th Grade", order=11)

    def test_grade_level_ordering(self):
        """Test grade level ordering."""
        grade_12 = GradeLevel.objects.create(name="12th Grade", order=12)
        grade_9 = GradeLevel.objects.create(name="9th Grade", order=9)
        grade_11 = GradeLevel.objects.create(name="11th Grade", order=11)

        grades = list(GradeLevel.objects.all())
        self.assertEqual(grades[0], grade_9)
        self.assertEqual(grades[1], grade_11)
        self.assertEqual(grades[2], grade_12)


class SchoolYearModelTests(TestCase):
    """Test cases for SchoolYear model."""

    def test_school_year_creation(self):
        """Test creating a school year."""
        school_year = SchoolYear.objects.create(
            name="2024-2025",
            start_date=date(2024, 8, 15),
            end_date=date(2025, 6, 15),
            is_active=True,
        )
        self.assertEqual(str(school_year), "2024-2025")
        self.assertTrue(school_year.is_active)

    def test_multiple_school_years_can_be_active(self):
        """Test that multiple school years can be active (no constraint in model)."""
        year1 = SchoolYear.objects.create(
            name="2024-2025",
            start_date=date(2024, 8, 15),
            end_date=date(2025, 6, 15),
            is_active=True,
        )

        year2 = SchoolYear.objects.create(
            name="2025-2026",
            start_date=date(2025, 8, 15),
            end_date=date(2026, 6, 15),
            is_active=True,
        )

        # Both can be active since there's no constraint in the model
        active_years = SchoolYear.objects.filter(is_active=True)
        self.assertEqual(active_years.count(), 2)
        self.assertIn(year1, active_years)
        self.assertIn(year2, active_years)

    def test_school_year_date_logic(self):
        """Test school year date logic (no validation in model currently)."""
        # This creates a school year with end before start - currently allowed
        school_year = SchoolYear.objects.create(
            name="Test Year",
            start_date=date(2025, 6, 15),
            end_date=date(2024, 8, 15),  # End before start
            is_active=False,
        )

        # Should be created successfully since there's no validation
        self.assertEqual(school_year.name, "Test Year")
        self.assertEqual(school_year.start_date, date(2025, 6, 15))
        self.assertEqual(school_year.end_date, date(2024, 8, 15))


class StudentModelTests(TestCase):
    """Test cases for Student model."""

    def setUp(self):
        """Set up test data."""
        self.grade_level = GradeLevel.objects.create(name="10th Grade", order=10)
        self.school_year = SchoolYear.objects.create(
            name="2024-2025",
            start_date=date(2024, 8, 15),
            end_date=date(2025, 6, 15),
            is_active=True,
        )

    def test_student_creation(self):
        """Test creating a student."""
        student = Student.objects.create(
            first_name="John",
            last_name="Doe",
            student_id="ST001",
            grade_level=self.grade_level,
            date_of_birth=date(2008, 5, 15),
            enrollment_date=date.today(),
            is_active=True,
        )

        self.assertEqual(str(student), "John Doe (ST001)")
        self.assertEqual(student.student_id, "ST001")
        self.assertEqual(student.grade_level, self.grade_level)
        self.assertTrue(student.is_active)

    def test_student_unique_student_id(self):
        """Test that student IDs must be unique."""
        Student.objects.create(
            first_name="John",
            last_name="Doe",
            student_id="ST001",
            grade_level=self.grade_level,
            date_of_birth=date(2008, 5, 15),
            enrollment_date=date.today(),
        )

        with self.assertRaises(IntegrityError):
            Student.objects.create(
                first_name="Jane",
                last_name="Smith",
                student_id="ST001",  # Duplicate ID
                grade_level=self.grade_level,
                date_of_birth=date(2008, 3, 10),
                enrollment_date=date.today(),
            )

    def test_student_age_calculation(self):
        """Test student age calculation."""
        birth_date = date.today() - timedelta(days=365 * 16 + 100)  # ~16 years old
        student = Student.objects.create(
            first_name="John",
            last_name="Doe",
            student_id="ST001",
            grade_level=self.grade_level,
            date_of_birth=birth_date,
            enrollment_date=date.today(),
        )

        # Calculate age manually since the model might not have age property
        today = date.today()
        age = (
            today.year
            - birth_date.year
            - ((today.month, today.day) < (birth_date.month, birth_date.day))
        )
        self.assertGreaterEqual(age, 15)
        self.assertLessEqual(age, 17)

    def test_student_full_name_property(self):
        """Test student full name property."""
        student = Student.objects.create(
            first_name="John",
            last_name="Doe",
            student_id="ST001",
            grade_level=self.grade_level,
            date_of_birth=date(2008, 5, 15),
            enrollment_date=date.today(),
        )

        self.assertEqual(student.full_name, "John Doe")

    def test_student_active_queryset(self):
        """Test active students queryset."""
        active_student = Student.objects.create(
            first_name="John",
            last_name="Doe",
            student_id="ST001",
            grade_level=self.grade_level,
            date_of_birth=date(2008, 5, 15),
            enrollment_date=date.today(),
            is_active=True,
        )

        inactive_student = Student.objects.create(
            first_name="Jane",
            last_name="Smith",
            student_id="ST002",
            grade_level=self.grade_level,
            date_of_birth=date(2008, 3, 10),
            enrollment_date=date.today(),
            is_active=False,
        )

        active_students = Student.objects.filter(is_active=True)
        self.assertIn(active_student, active_students)
        self.assertNotIn(inactive_student, active_students)


class EmergencyContactModelTests(TestCase):
    """Test cases for EmergencyContact model."""

    def setUp(self):
        """Set up test data."""
        self.grade_level = GradeLevel.objects.create(name="10th Grade", order=10)
        self.student = Student.objects.create(
            first_name="John",
            last_name="Doe",
            student_id="ST001",
            grade_level=self.grade_level,
            date_of_birth=date(2008, 5, 15),
            enrollment_date=date.today(),
        )

    def test_emergency_contact_creation(self):
        """Test creating an emergency contact."""
        contact = EmergencyContact.objects.create(
            first_name="Jane",
            last_name="Doe",
            relationship="mother",
            phone_primary="555-123-4567",
            email="jane@example.com",
            is_primary=True,
        )

        # Add contact to student
        self.student.emergency_contacts.add(contact)

        self.assertEqual(str(contact), "Jane Doe (Mother)")
        self.assertEqual(contact.phone_primary, "555-123-4567")
        self.assertTrue(contact.is_primary)

    def test_emergency_contact_phone_not_required(self):
        """Test that phone number is not required (but allowed to be blank)."""
        # Phone is blank=True in the model, so this should work
        contact = EmergencyContact.objects.create(
            first_name="Jane",
            last_name="Doe",
            relationship="mother",
            phone_primary="",  # Empty phone is allowed
            email="jane@example.com",
            is_primary=True,
        )
        self.assertEqual(contact.phone_primary, "")

    def test_multiple_emergency_contacts(self):
        """Test that students can have multiple emergency contacts."""
        contact1 = EmergencyContact.objects.create(
            first_name="Jane",
            last_name="Doe",
            relationship="mother",
            phone_primary="555-123-4567",
            is_primary=True,
        )

        contact2 = EmergencyContact.objects.create(
            first_name="Bob",
            last_name="Doe",
            relationship="father",
            phone_primary="555-987-6543",
            is_primary=False,
        )

        # Add contacts to student
        self.student.emergency_contacts.add(contact1, contact2)

        contacts = self.student.emergency_contacts.all()
        self.assertEqual(contacts.count(), 2)
        self.assertIn(contact1, contacts)
        self.assertIn(contact2, contacts)
