"""
Analytics URLs
"""
from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Main analytics views
    path('class-performance/', views.ClassPerformanceView.as_view(), name='class_performance'),
    path('student-progress/', views.StudentProgressView.as_view(), name='student_progress'),
    path('grade-distribution/', views.GradeDistributionView.as_view(), name='grade_distribution'),
    path('attendance-trends/', views.AttendanceTrendsView.as_view(), name='attendance_trends'),
    path('failing-alerts/', views.FailingStudentAlertsView.as_view(), name='failing_alerts'),
    path('report-builder/', views.CustomReportBuilderView.as_view(), name='report_builder'),
    
    # API endpoints
    path('api/student/<uuid:student_id>/', views.api_student_analytics, name='api_student_analytics'),
    path('api/class/<int:course_id>/', views.api_class_analytics, name='api_class_analytics'),
    path('api/alert/<int:alert_id>/resolve/', views.resolve_alert, name='resolve_alert'),
]
