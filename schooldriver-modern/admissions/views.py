import csv
from django.http import HttpResponse
from .models import Applicant


def applicant_csv_export(request):
    """Return a detailed CSV of the current admissions data."""
    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="admissions_analytics_detailed.csv"'},
    )
    writer = csv.writer(response)
    
    # Comprehensive header row
    writer.writerow([
        "Applicant ID", "First Name", "Last Name", "Full Name", "Preferred Name",
        "Date of Birth", "Gender", "Email", "Address", "City", "State", "Zip Code",
        "Applying for Grade", "School Year", "Current School", "Living Situation",
        "Admission Level", "Decision", "Decision Date", "Decision By", 
        "Completion Percentage", "Applied Date", "Last Updated",
        "Primary Parent Name", "Primary Parent Email", "Primary Parent Phone",
        "Is Ready for Enrollment", "Follow Up Date", "Notes", "Special Circumstances"
    ])
    
    # Get detailed data with related objects
    qs = Applicant.objects.select_related(
        "level", "decision", "applying_for_grade", "school_year", "current_school"
    ).prefetch_related("parent_guardians").all()
    
    for a in qs:
        # Get primary parent information
        primary_parent = a.parent_guardians.first()
        primary_parent_name = getattr(primary_parent, 'name', '') if primary_parent else a.primary_parent_name
        primary_parent_email = getattr(primary_parent, 'email', '') if primary_parent else a.primary_parent_email
        primary_parent_phone = getattr(primary_parent, 'primary_phone', '') if primary_parent else a.primary_parent_phone
        
        # Format address
        full_address = a.street if a.street else ""
        
        # Get current school name
        current_school = ""
        if a.current_school:
            current_school = a.current_school.name
        elif a.current_school_name:
            current_school = a.current_school_name
            
        writer.writerow([
            a.applicant_id or f"New-{a.id}",
            a.first_name,
            a.last_name,
            a.full_name,
            a.preferred_name,
            a.date_of_birth.strftime('%Y-%m-%d') if a.date_of_birth else "",
            a.get_gender_display() if a.gender else "",
            a.email,
            full_address,
            a.city,
            a.state,
            a.zip_code,
            a.applying_for_grade.name if a.applying_for_grade else "",
            a.school_year.name if a.school_year else "",
            current_school,
            a.get_living_situation_display() if a.living_situation else "",
            a.level.name if a.level else "Not Started",
            a.decision.name if a.decision else "Pending",
            a.decision_date.strftime('%Y-%m-%d') if a.decision_date else "",
            a.decision_by,
            f"{a.get_completion_percentage():.1f}%",
            a.created_at.strftime('%Y-%m-%d'),
            a.updated_at.strftime('%Y-%m-%d'),
            primary_parent_name,
            primary_parent_email, 
            primary_parent_phone,
            "Yes" if a.is_ready_for_enrollment else "No",
            a.follow_up_date.strftime('%Y-%m-%d') if a.follow_up_date else "",
            a.notes.replace('\n', ' ').replace('\r', ' ') if a.notes else "",
            a.special_circumstances.replace('\n', ' ').replace('\r', ' ') if a.special_circumstances else "",
        ])
    return response


# Create your views here.
