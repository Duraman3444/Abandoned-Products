"""
Tests for sample data integrity from populate_sample_data management command.
"""

from django.test import TestCase
from django.core.management import call_command
from django.db import transaction
from students.models import Student, GradeLevel, SchoolYear, EmergencyContact
from admissions.models import (
    Applicant,
    ApplicantDocument,
    FeederSchool,
    AdmissionLevel,
    AdmissionCheck,
    ApplicationDecision,
)


class SampleDataIntegrityTest(TestCase):
    """Test that populate_sample_data command creates expected data structure."""

    @classmethod
    def setUpClass(cls):
        """Set up test data by running populate_sample_data command."""
        super().setUpClass()

        # Run the populate_sample_data command to create test data
        with transaction.atomic():
            call_command("populate_sample_data")

    def test_student_count_and_uniqueness(self):
        """Test that 16+ students are created with unique IDs."""
        students = Student.objects.all()
        student_count = students.count()

        # Should have 16+ students as specified from command output
        self.assertGreaterEqual(
            student_count, 16, f"Expected 16+ students, got {student_count}"
        )

        # Verify no duplicate student IDs (UUIDs should be unique by default)
        student_ids = list(students.values_list("id", flat=True))
        self.assertEqual(
            len(student_ids), len(set(student_ids)), "Student IDs should be unique"
        )

        # Verify students have required fields populated
        for student in students[:5]:  # Check first 5 students
            self.assertIsNotNone(student.first_name, "Student should have first_name")
            self.assertIsNotNone(student.last_name, "Student should have last_name")
            self.assertIsNotNone(
                student.date_of_birth, "Student should have date_of_birth"
            )
            self.assertIsNotNone(student.grade_level, "Student should have grade_level")

    def test_applicant_count_and_data_quality(self):
        """Test that 10+ applicants are created with proper data."""
        applicants = Applicant.objects.all()
        applicant_count = applicants.count()

        # Should have 10+ applicants as specified from command output
        self.assertGreaterEqual(
            applicant_count, 10, f"Expected 10+ applicants, got {applicant_count}"
        )

        # Verify no duplicate applicant IDs
        applicant_ids = list(applicants.values_list("id", flat=True))
        self.assertEqual(
            len(applicant_ids),
            len(set(applicant_ids)),
            "Applicant IDs should be unique",
        )

        # Verify applicants have required fields
        for applicant in applicants[:5]:  # Check first 5 applicants
            self.assertIsNotNone(
                applicant.first_name, "Applicant should have first_name"
            )
            self.assertIsNotNone(applicant.last_name, "Applicant should have last_name")
            self.assertIsNotNone(
                applicant.date_of_birth, "Applicant should have date_of_birth"
            )
            self.assertIsNotNone(
                applicant.applying_for_grade, "Applicant should have applying_for_grade"
            )

    def test_grade_level_count_and_structure(self):
        """Test that 13+ grade levels are created with proper ordering."""
        grade_levels = GradeLevel.objects.all()
        grade_count = grade_levels.count()

        # Should have 13+ grade levels as specified
        self.assertGreaterEqual(
            grade_count, 13, f"Expected 13+ grade levels, got {grade_count}"
        )

        # Verify grade levels are properly ordered
        ordered_grades = grade_levels.order_by("order")
        previous_order = 0
        for grade in ordered_grades:
            self.assertGreater(
                grade.order, previous_order, "Grade levels should be properly ordered"
            )
            self.assertIsNotNone(grade.name, "Grade level should have a name")
            previous_order = grade.order

        # Verify no duplicate grade names
        grade_names = list(grade_levels.values_list("name", flat=True))
        self.assertEqual(
            len(grade_names),
            len(set(grade_names)),
            "Grade level names should be unique",
        )

    def test_grade_level_assignments(self):
        """Test that students and applicants are properly assigned to grade levels."""
        # Test student grade assignments
        students_with_grades = Student.objects.filter(grade_level__isnull=False)
        self.assertGreater(
            students_with_grades.count(),
            0,
            "Students should be assigned to grade levels",
        )

        # Verify all assigned grades exist in GradeLevel table
        assigned_grade_ids = set(
            students_with_grades.values_list("grade_level_id", flat=True)
        )
        existing_grade_ids = set(GradeLevel.objects.values_list("id", flat=True))
        self.assertTrue(
            assigned_grade_ids.issubset(existing_grade_ids),
            "All student grade assignments should reference valid grade levels",
        )

        # Test applicant grade assignments
        applicants_with_grades = Applicant.objects.filter(
            applying_for_grade__isnull=False
        )
        self.assertGreater(
            applicants_with_grades.count(),
            0,
            "Applicants should be assigned to grade levels",
        )

        # Verify all applicant grade assignments are valid
        applicant_grade_ids = set(
            applicants_with_grades.values_list("applying_for_grade_id", flat=True)
        )
        self.assertTrue(
            applicant_grade_ids.issubset(existing_grade_ids),
            "All applicant grade assignments should reference valid grade levels",
        )

    def test_applicant_document_associations(self):
        """Test that applicant documents are properly associated with applicants."""
        documents = ApplicantDocument.objects.all()
        document_count = documents.count()

        # Should have 20+ documents as specified from command output
        self.assertGreaterEqual(
            document_count, 20, f"Expected 20+ documents, got {document_count}"
        )

        # Verify all documents are associated with valid applicants
        document_applicant_ids = set(documents.values_list("applicant_id", flat=True))
        existing_applicant_ids = set(Applicant.objects.values_list("id", flat=True))
        self.assertTrue(
            document_applicant_ids.issubset(existing_applicant_ids),
            "All documents should be associated with valid applicants",
        )

        # Verify documents have required fields
        for document in documents[:10]:  # Check first 10 documents
            self.assertIsNotNone(
                document.applicant, "Document should be associated with an applicant"
            )
            self.assertIsNotNone(
                document.check, "Document should be associated with an admission check"
            )
            self.assertTrue(
                hasattr(document, "file"), "Document should have file field"
            )

    def test_admission_level_structure(self):
        """Test that admission levels are properly created and ordered."""
        admission_levels = AdmissionLevel.objects.all()

        # Should have multiple admission levels
        self.assertGreater(
            admission_levels.count(), 0, "Should have admission levels created"
        )

        # Verify proper ordering
        ordered_levels = admission_levels.order_by("order")
        previous_order = 0
        for level in ordered_levels:
            self.assertGreater(
                level.order,
                previous_order,
                "Admission levels should be properly ordered",
            )
            self.assertIsNotNone(level.name, "Admission level should have a name")
            previous_order = level.order

    def test_admission_checks_associations(self):
        """Test that admission checks are properly associated with levels."""
        admission_checks = AdmissionCheck.objects.all()

        # Should have admission checks
        self.assertGreater(
            admission_checks.count(), 0, "Should have admission checks created"
        )

        # Verify all checks are associated with valid admission levels
        check_level_ids = set(admission_checks.values_list("level_id", flat=True))
        existing_level_ids = set(AdmissionLevel.objects.values_list("id", flat=True))
        self.assertTrue(
            check_level_ids.issubset(existing_level_ids),
            "All admission checks should be associated with valid admission levels",
        )

    def test_emergency_contact_associations(self):
        """Test that emergency contacts are properly created and associated."""
        emergency_contacts = EmergencyContact.objects.all()

        # Should have emergency contacts
        self.assertGreater(
            emergency_contacts.count(), 0, "Should have emergency contacts created"
        )

        # Check that some students have emergency contacts
        students_with_contacts = Student.objects.filter(
            emergency_contacts__isnull=False
        ).distinct()
        self.assertGreater(
            students_with_contacts.count(),
            0,
            "Some students should have emergency contacts",
        )

        # Check that applicants model exists (simplified test)
        applicants_count = Applicant.objects.count()
        self.assertGreater(applicants_count, 0, "Should have applicants created")

    def test_school_year_structure(self):
        """Test that school years are properly created."""
        school_years = SchoolYear.objects.all()

        # Should have at least one school year
        self.assertGreater(school_years.count(), 0, "Should have school years created")

        # Verify school years have required fields
        for year in school_years:
            self.assertIsNotNone(year.name, "School year should have a name")
            self.assertIsNotNone(year.start_date, "School year should have start_date")
            self.assertIsNotNone(year.end_date, "School year should have end_date")

    def test_feeder_school_structure(self):
        """Test that feeder schools are properly created."""
        feeder_schools = FeederSchool.objects.all()

        # Should have feeder schools
        self.assertGreater(
            feeder_schools.count(), 0, "Should have feeder schools created"
        )

        # Verify feeder schools have names
        for school in feeder_schools:
            self.assertIsNotNone(school.name, "Feeder school should have a name")

    def test_application_decisions_structure(self):
        """Test that application decisions are properly created."""
        decisions = ApplicationDecision.objects.all()

        # Should have application decisions
        self.assertGreater(
            decisions.count(), 0, "Should have application decisions created"
        )

        # Verify decisions have required fields
        for decision in decisions:
            self.assertIsNotNone(
                decision.name, "Application decision should have a name"
            )
            self.assertIsInstance(
                decision.is_positive, bool, "is_positive should be boolean"
            )

    def test_data_consistency_totals(self):
        """Test overall data consistency and expected totals."""
        # Verify exact counts match expected values from command output
        self.assertEqual(Student.objects.count(), 16, "Should have exactly 16 students")
        self.assertEqual(
            Applicant.objects.count(), 10, "Should have exactly 10 applicants"
        )
        self.assertEqual(
            GradeLevel.objects.count(), 13, "Should have exactly 13 grade levels"
        )
        self.assertGreaterEqual(
            ApplicantDocument.objects.count(), 20, "Should have 20+ documents"
        )

        # Verify no orphaned records
        self.assertEqual(
            Student.objects.filter(grade_level__isnull=True).count(),
            0,
            "All students should have grade assignments",
        )
        self.assertEqual(
            Applicant.objects.filter(applying_for_grade__isnull=True).count(),
            0,
            "All applicants should have grade assignments",
        )

    def test_referential_integrity(self):
        """Test that all foreign key relationships are valid."""
        # Test student relationships
        for student in Student.objects.all()[:10]:  # Sample check
            if student.grade_level:
                self.assertTrue(
                    GradeLevel.objects.filter(id=student.grade_level.id).exists(),
                    f"Student {student.id} references non-existent grade level",
                )

        # Test applicant relationships
        for applicant in Applicant.objects.all()[:10]:  # Sample check
            if applicant.applying_for_grade:
                self.assertTrue(
                    GradeLevel.objects.filter(
                        id=applicant.applying_for_grade.id
                    ).exists(),
                    f"Applicant {applicant.id} references non-existent grade level",
                )
            if applicant.school_year:
                self.assertTrue(
                    SchoolYear.objects.filter(id=applicant.school_year.id).exists(),
                    f"Applicant {applicant.id} references non-existent school year",
                )

        # Test document relationships
        for document in ApplicantDocument.objects.all()[:10]:  # Sample check
            self.assertTrue(
                Applicant.objects.filter(id=document.applicant.id).exists(),
                f"Document {document.id} references non-existent applicant",
            )
            if hasattr(document.check, "id"):
                self.assertTrue(
                    AdmissionCheck.objects.filter(id=document.check.id).exists(),
                    f"Document {document.id} references non-existent admission check",
                )
