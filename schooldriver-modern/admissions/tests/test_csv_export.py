from django.urls import reverse
from django.test import TestCase, Client
from students.models import Student, EmergencyContact, GradeLevel, SchoolYear
from admissions.models import Applicant, ApplicationDecision, AdmissionLevel
from datetime import date


class CSVExportTests(TestCase):
    def setUp(self):
        self.client = Client()
        # Create test data
        self.grade_level = GradeLevel.objects.create(name="1st Grade", order=1)
        self.school_year = SchoolYear.objects.create(
            name="2024-2025", 
            start_date=date(2024, 8, 15), 
            end_date=date(2025, 6, 15),
            is_active=True
        )
        self.contact = EmergencyContact.objects.create(
            first_name="John", 
            last_name="Doe", 
            relationship="father",
            email="john@example.com",
            phone_primary="555-1234"
        )
        self.student = Student.objects.create(
            student_id="241001",
            first_name="Jane",
            last_name="Doe", 
            date_of_birth=date(2010, 5, 15),
            grade_level=self.grade_level,
            enrollment_date=date(2024, 8, 15)
        )
        
        self.decision = ApplicationDecision.objects.create(
            name="Accepted", 
            is_positive=True, 
            order=1
        )
        self.level = AdmissionLevel.objects.create(
            name="Application Review", 
            order=1
        )
        self.applicant = Applicant.objects.create(
            applicant_id="A241001",
            first_name="Bob",
            last_name="Smith",
            date_of_birth=date(2011, 3, 20),
            applying_for_grade=self.grade_level,
            school_year=self.school_year,
            level=self.level,
            decision=self.decision
        )

    def test_admissions_csv_download_success(self):
        url = reverse("dashboard_csv_export")
        resp = self.client.get(url)
        assert resp.status_code == 200
        assert resp["Content-Type"] == "text/csv"
        assert "attachment;" in resp["Content-Disposition"]
        assert "admissions_analytics_detailed.csv" in resp["Content-Disposition"]
        # Should have header + at least 1 data row
        assert resp.content.count(b"\n") >= 2
        # Check for applicant data
        content = resp.content.decode('utf-8')
        assert "A241001" in content
        assert "Bob" in content
        assert "Smith" in content

    def test_students_csv_download_success(self):
        url = reverse("students_csv_export")
        resp = self.client.get(url)
        assert resp.status_code == 200
        assert resp["Content-Type"] == "text/csv"
        assert "students_detailed.csv" in resp["Content-Disposition"]
        assert resp.content.count(b"\n") >= 2
        # Check for student data
        content = resp.content.decode('utf-8')
        assert "241001" in content
        assert "Jane" in content
        assert "Doe" in content

    def test_contacts_csv_download_success(self):
        url = reverse("contacts_csv_export")
        resp = self.client.get(url)
        assert resp.status_code == 200
        assert resp["Content-Type"] == "text/csv"
        assert "emergency_contacts.csv" in resp["Content-Disposition"]
        assert resp.content.count(b"\n") >= 2
        # Check for contact data
        content = resp.content.decode('utf-8')
        assert "John" in content
        assert "john@example.com" in content

    def test_documents_csv_download_success(self):
        url = reverse("documents_csv_export")
        resp = self.client.get(url)
        assert resp.status_code == 200
        assert resp["Content-Type"] == "text/csv"
        assert "applicant_documents.csv" in resp["Content-Disposition"]
        # Even if no documents, should have header
        assert resp.content.count(b"\n") >= 1

    def test_contact_logs_csv_download_success(self):
        url = reverse("contact_logs_csv_export")
        resp = self.client.get(url)
        assert resp.status_code == 200
        assert resp["Content-Type"] == "text/csv"
        assert "contact_logs.csv" in resp["Content-Disposition"]
        # Even if no logs, should have header
        assert resp.content.count(b"\n") >= 1
