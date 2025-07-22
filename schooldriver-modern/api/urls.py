from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from . import views

# Create router and register viewsets
router = DefaultRouter()
router.register(r'students', views.StudentViewSet)
router.register(r'courses', views.CourseViewSet)
router.register(r'sections', views.CourseSectionViewSet)
router.register(r'enrollments', views.EnrollmentViewSet)
router.register(r'assignments', views.AssignmentViewSet)
router.register(r'grades', views.GradeViewSet)
router.register(r'schedules', views.ScheduleViewSet)
router.register(r'attendance', views.AttendanceViewSet)
router.register(r'applicants', views.ApplicantViewSet)
# router.register(r'applications', views.ApplicationViewSet)  # Removed - using applicants instead
router.register(r'teachers', views.TeacherViewSet)

app_name = 'api'

urlpatterns = [
    # API Authentication
    path('auth/token/', views.CustomAuthToken.as_view(), name='api_token_auth'),
    
    # API Documentation
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='api:schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='api:schema'), name='redoc'),
    
    # Utility endpoints
    path('stats/', views.api_stats, name='api_stats'),
    path('health/', views.api_health, name='api_health'),
    
    # Main API routes
    path('', include(router.urls)),
]
