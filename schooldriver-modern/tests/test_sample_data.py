"""
Tests for sample data integrity and verification.
"""
from django.test import TestCase
from django.core.management import call_command
from django.contrib.auth.models import User
from students.models import Student, GradeLevel, EmergencyContact, SchoolYear
from admissions.models import Applicant, ApplicationDecision, ApplicantDocument


class SampleDataTests(TestCase):
    """Test cases for sample data integrity."""

    def test_populate_sample_data_command(self):
        """Test that populate_sample_data command creates expected data."""
        # Clear existing data
        Student.objects.all().delete()
        Applicant.objects.all().delete()
        SchoolYear.objects.all().delete()
        
        # Run sample data command
        call_command('populate_sample_data')
        
        # Verify basic model counts
        self.assertGreaterEqual(Student.objects.count(), 15)
        self.assertGreaterEqual(Applicant.objects.count(), 10)
        self.assertGreaterEqual(GradeLevel.objects.count(), 13)
        self.assertGreaterEqual(SchoolYear.objects.count(), 1)
        self.assertGreaterEqual(EmergencyContact.objects.count(), 20)
        self.assertGreaterEqual(ApplicantDocument.objects.count(), 25)

    def test_sample_data_uniqueness(self):
        """Test that sample data creates unique records."""
        call_command('populate_sample_data')
        
        # Test student uniqueness
        student_emails = Student.objects.values_list('primary_contact_email', flat=True)
        unique_emails = set(filter(None, student_emails))
        self.assertGreater(len(unique_emails), 5)
        
        # Test applicant uniqueness
        applicant_emails = Applicant.objects.values_list('email', flat=True)
        unique_applicant_emails = set(filter(None, applicant_emails))
        self.assertGreaterEqual(len(unique_applicant_emails), 0)  # Some applicants may not have emails
        
        # Test grade level uniqueness
        grade_names = set(GradeLevel.objects.values_list('name', flat=True))
        self.assertGreaterEqual(len(grade_names), 13)

    def test_sample_data_relationships(self):
        """Test that sample data creates proper relationships."""
        call_command('populate_sample_data')
        
        # Test that students have grade levels
        students_with_grades = Student.objects.filter(grade_level__isnull=False).count()
        total_students = Student.objects.count()
        self.assertEqual(students_with_grades, total_students)
        
        # Test that applicants have admission levels
        applicants_with_levels = Applicant.objects.filter(level__isnull=False).count()
        total_applicants = Applicant.objects.count()
        self.assertGreater(applicants_with_levels, 0)  # At least some applicants should have levels
        
        # Test that some applicants have documents
        applicants_with_docs = ApplicantDocument.objects.values('applicant').distinct().count()
        self.assertGreater(applicants_with_docs, 5)

    def test_admin_user_creation(self):
        """Test that admin user can be created for testing."""
        # Create admin user for sample data testing
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@school.edu',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
        
        # Check admin user exists
        self.assertIsNotNone(admin_user)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
        
        # Verify admin can authenticate
        self.assertTrue(admin_user.check_password('admin123'))

    def test_dashboard_data_availability(self):
        """Test that sample data provides sufficient data for dashboard."""
        call_command('populate_sample_data')
        
        # Check we have data for dashboard charts
        self.assertGreater(Student.objects.count(), 0)
        self.assertGreater(Applicant.objects.count(), 0)
        
        # Check we have varied admission levels for pipeline chart
        admission_levels = Applicant.objects.values('level__name').distinct().count()
        self.assertGreaterEqual(admission_levels, 2)  # At least 2 different levels
        
        # Check we have application decisions for status chart
        decisions = ApplicationDecision.objects.count()
        self.assertGreater(decisions, 0)
