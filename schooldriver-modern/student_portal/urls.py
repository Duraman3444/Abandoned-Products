from django.urls import path
from . import views

app_name = 'student_portal'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('grades/', views.grades_view, name='grades'),
    path('schedule/', views.schedule_view, name='schedule'),
    path('attendance/', views.attendance_view, name='attendance'),
    path('profile/', views.profile_view, name='profile'),
    path('assignments/', views.assignments_view, name='assignments'),
    path('assignments/<int:assignment_id>/', views.assignment_detail_view, name='assignment_detail'),
]
