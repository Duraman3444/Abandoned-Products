from django.urls import path
from . import views
from students.views import (
    students_csv_export, emergency_contacts_csv_export, 
    admissions_documents_csv_export, contact_logs_csv_export
)

urlpatterns = [
    # Main dashboard CSV export
    path("export/csv/", views.applicant_csv_export, name="dashboard_csv_export"),
    
    # Additional detailed CSV exports
    path("export/students/csv/", students_csv_export, name="students_csv_export"),
    path("export/contacts/csv/", emergency_contacts_csv_export, name="contacts_csv_export"),
    path("export/documents/csv/", admissions_documents_csv_export, name="documents_csv_export"),
    path("export/contact-logs/csv/", contact_logs_csv_export, name="contact_logs_csv_export"),
]
