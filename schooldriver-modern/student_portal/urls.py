from django.urls import path
from . import views

app_name = 'student_portal'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('grades/', views.grades_view, name='grades'),
    path('schedule/', views.schedule_view, name='schedule'),
    path('schedule/export/', views.schedule_export_view, name='schedule_export'),
    path('schedule/print/', views.schedule_print_view, name='schedule_print'),
    path('attendance/', views.attendance_view, name='attendance'),
    path('profile/', views.profile_view, name='profile'),
    path('assignments/', views.assignments_view, name='assignments'),
    path('assignments/<int:assignment_id>/', views.assignment_detail_view, name='assignment_detail'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
]
