import csv
from django.http import HttpResponse
from .models import Student, EmergencyContact


def students_csv_export(request):
    """Return a detailed CSV of all student data."""
    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="students_detailed.csv"'},
    )
    writer = csv.writer(response)
    
    # Comprehensive header row
    writer.writerow([
        "Student ID", "First Name", "Last Name", "Full Name", "Preferred Name",
        "Date of Birth", "Age", "Gender", "Grade Level", "Graduation Year",
        "Enrollment Date", "Graduation Date", "Is Active", "Withdrawal Date", "Withdrawal Reason",
        "Primary Contact Name", "Primary Contact Email", "Primary Contact Phone",
        "Special Needs", "Notes", "Created Date", "Last Updated"
    ])
    
    # Get detailed data with related objects
    qs = Student.objects.select_related("grade_level").prefetch_related("emergency_contacts").all()
    
    for s in qs:
        writer.writerow([
            s.student_id,
            s.first_name,
            s.last_name,
            s.full_name,
            s.preferred_name,
            s.date_of_birth.strftime('%Y-%m-%d'),
            s.get_age(),
            s.get_gender_display() if s.gender else "",
            s.grade_level.name if s.grade_level else "",
            s.graduation_year or "",
            s.enrollment_date.strftime('%Y-%m-%d'),
            s.graduation_date.strftime('%Y-%m-%d') if s.graduation_date else "",
            "Yes" if s.is_active else "No",
            s.withdrawal_date.strftime('%Y-%m-%d') if s.withdrawal_date else "",
            s.withdrawal_reason.replace('\n', ' ').replace('\r', ' ') if s.withdrawal_reason else "",
            s.primary_contact_name,
            s.primary_contact_email,
            s.primary_contact_phone,
            s.special_needs.replace('\n', ' ').replace('\r', ' ') if s.special_needs else "",
            s.notes.replace('\n', ' ').replace('\r', ' ') if s.notes else "",
            s.created_at.strftime('%Y-%m-%d'),
            s.updated_at.strftime('%Y-%m-%d'),
        ])
    return response


def emergency_contacts_csv_export(request):
    """Return a detailed CSV of all emergency contacts."""
    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="emergency_contacts.csv"'},
    )
    writer = csv.writer(response)
    
    writer.writerow([
        "First Name", "Last Name", "Full Name", "Relationship", "Email",
        "Primary Phone", "Secondary Phone", "Street", "City", "State", "Zip Code",
        "Is Primary Contact", "Created Date", "Last Updated"
    ])
    
    qs = EmergencyContact.objects.all()
    
    for contact in qs:
        writer.writerow([
            contact.first_name,
            contact.last_name,
            contact.full_name,
            contact.get_relationship_display(),
            contact.email,
            contact.phone_primary,
            contact.phone_secondary,
            contact.street,
            contact.city,
            contact.state,
            contact.zip_code,
            "Yes" if contact.is_primary else "No",
            contact.created_at.strftime('%Y-%m-%d'),
            contact.updated_at.strftime('%Y-%m-%d'),
        ])
    return response


def admissions_documents_csv_export(request):
    """Return a detailed CSV of all applicant documents."""
    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="applicant_documents.csv"'},
    )
    writer = csv.writer(response)
    
    # Import here to avoid circular imports
    from admissions.models import ApplicantDocument
    
    writer.writerow([
        "Applicant ID", "Applicant Name", "Document Type", "Title", "File Name",
        "File Size (MB)", "Is Verified", "Verified By", "Verified Date",
        "Uploaded By", "Upload Date", "Notes"
    ])
    
    qs = ApplicantDocument.objects.select_related("applicant").all()
    
    for doc in qs:
        writer.writerow([
            doc.applicant.applicant_id,
            doc.applicant.full_name,
            doc.get_document_type_display(),
            doc.title,
            doc.file.name.split('/')[-1] if doc.file else "",
            doc.file_size_mb(),
            "Yes" if doc.is_verified else "No",
            doc.verified_by,
            doc.verified_date.strftime('%Y-%m-%d') if doc.verified_date else "",
            doc.uploaded_by,
            doc.uploaded_at.strftime('%Y-%m-%d'),
            doc.notes.replace('\n', ' ').replace('\r', ' ') if doc.notes else "",
        ])
    return response


def contact_logs_csv_export(request):
    """Return a detailed CSV of all contact logs."""
    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="contact_logs.csv"'},
    )
    writer = csv.writer(response)
    
    # Import here to avoid circular imports
    from admissions.models import ContactLog
    
    writer.writerow([
        "Applicant ID", "Applicant Name", "Contact Date", "Contact Type",
        "Contacted By", "Summary", "Follow Up Needed", "Follow Up Date"
    ])
    
    qs = ContactLog.objects.select_related("applicant").all()
    
    for log in qs:
        writer.writerow([
            log.applicant.applicant_id,
            log.applicant.full_name,
            log.contact_date.strftime('%Y-%m-%d %H:%M'),
            log.get_contact_type_display(),
            log.contacted_by,
            log.summary.replace('\n', ' ').replace('\r', ' ') if log.summary else "",
            "Yes" if log.follow_up_needed else "No",
            log.follow_up_date.strftime('%Y-%m-%d') if log.follow_up_date else "",
        ])
    return response


# Create your views here.
