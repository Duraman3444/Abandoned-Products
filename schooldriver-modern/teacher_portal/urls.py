from django.urls import path
from . import views

app_name = 'teacher_portal'

urlpatterns = [
    path('', views.TeacherDashboardView.as_view(), name='teacher_dashboard'),
    path('gradebook/', views.TeacherGradebookView.as_view(), name='teacher_gradebook'),
    path('attendance/', views.TeacherAttendanceView.as_view(), name='teacher_attendance'),
    path('assignments/', views.TeacherAssignmentsView.as_view(), name='teacher_assignments'),
    path('assignments/create/', views.CreateAssignmentView.as_view(), name='create_assignment'),
    path('assignments/analytics/', views.assignment_analytics, name='assignment_analytics'),
    path('students/', views.TeacherStudentsView.as_view(), name='teacher_students'),
    path('reports/', views.TeacherReportsView.as_view(), name='teacher_reports'),
    path('messages/', views.TeacherMessagesView.as_view(), name='teacher_messages'),
    path('settings/', views.TeacherSettingsView.as_view(), name='teacher_settings'),
    # AJAX endpoints
    path('api/switch-section/', views.teacher_section_switch, name='teacher_section_switch'),
    path('api/save-grade/', views.ajax_save_grade, name='ajax_save_grade'),
    path('api/save-attendance/', views.ajax_save_attendance, name='ajax_save_attendance'),
    # Export endpoints
    path('export/grades/', views.export_grades, name='export_grades'),
    path('reports/attendance/', views.attendance_reports, name='attendance_reports'),
]
