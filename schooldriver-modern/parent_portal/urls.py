from django.urls import path
from . import views
from .language_views import set_language_view

app_name = "parent_portal"

urlpatterns = [
    # Authentication and Registration
    path("register/", views.parent_register_view, name="register"),
    path("verify-code/", views.verification_code_view, name="verify_code"),
    path("request-verification/", views.request_verification_view, name="request_verification"),
    
    # Main Portal Views  
    path("", views.dashboard_view, name="dashboard"),
    path("children/", views.children_view, name="children"),
    path("child/", views.child_detail_view, name="child_detail_current"),
    path("child/<uuid:student_id>/", views.child_detail_view, name="child_detail"),
    path("grades/", views.grades_view, name="grades_current"),
    path("grades/<uuid:student_id>/", views.grades_view, name="grades"),
    path("attendance/", views.attendance_view, name="attendance_current"),
    path("attendance/<uuid:student_id>/", views.attendance_view, name="attendance"),
    path("early-dismissal-request/", views.early_dismissal_request_view, name="early_dismissal_request"),
    path("school-calendar/", views.school_calendar_view, name="school_calendar"),
    path("progress-report/", views.progress_report_view, name="progress_report_current"),
    path("progress-report/<uuid:student_id>/", views.progress_report_view, name="progress_report"),
    path("progress-report-pdf/", views.progress_report_pdf, name="progress_report_pdf_current"),
    path("progress-report-pdf/<uuid:student_id>/", views.progress_report_pdf, name="progress_report_pdf"),
    path("historical-reports/", views.historical_reports_view, name="historical_reports_current"),
    path("historical-reports/<uuid:student_id>/", views.historical_reports_view, name="historical_reports"),
    path("messages/", views.messages_view, name="messages"),
    path("messages/compose/", views.compose_message_view, name="compose_message"),
    path("messages/thread/<str:thread_id>/", views.message_thread_view, name="message_thread"),
    path("messages/attachment/<int:attachment_id>/download/", views.download_attachment_view, name="download_attachment"),
    path("profile/", views.profile_view, name="profile"),
    path("set-language/", set_language_view, name="set_language"),
    
    # Emergency Contact Management
    path("emergency-contacts/", views.emergency_contacts_view, name="emergency_contacts"),
    path("emergency-contacts/add/", views.add_emergency_contact_view, name="add_emergency_contact"),
    path("emergency-contacts/<uuid:contact_id>/edit/", views.edit_emergency_contact_view, name="edit_emergency_contact"),
    path("pickup-persons/add/", views.add_pickup_person_view, name="add_pickup_person"),
    path("pickup-persons/<uuid:person_id>/edit/", views.edit_pickup_person_view, name="edit_pickup_person"),
    path("medical-information/", views.medical_information_view, name="medical_information"),
]
