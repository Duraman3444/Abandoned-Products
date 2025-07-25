"""
URL configuration for schooldriver_modern project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import DemoPageView
from core.explorer_views import ApiLandingView
from core.detail_views import student_detail_view, course_detail_view, teacher_detail_view, assignment_detail_view
from . import views
from .auth_views import CustomLoginView, SignUpView
from .profile_views import profile_view, ProfileEditView, CustomPasswordChangeView

urlpatterns = [
    # Public URLs (no authentication required)
    path("", include("public.urls")),
    path("demo/", DemoPageView.as_view(), name="demo"),
    # Authentication URLs
    path("accounts/login/", CustomLoginView.as_view(), name="login"),
    path("accounts/signup/", SignUpView.as_view(), name="signup"),
    path(
        "accounts/password_change/",
        CustomPasswordChangeView.as_view(),
        name="accounts_password_change",
    ),
    path("accounts/", include("django.contrib.auth.urls")),
    # Role-based portal URLs (authentication required)
    path("student/", include("student_portal.urls")),
    path("parent/", include("parent_portal.urls")),
    path("teacher/", include("teacher_portal.urls")),
    path("services/", include("school_services.urls")),
    path("analytics/", include("student_analytics.urls")),
    path("notifications/", include("notification_system.urls")),
    path("search/", include("search.urls")),
    # Admin and general authenticated areas
    path("admin/", admin.site.urls),
    path("dashboard/", views.dashboard_view, name="dashboard"),
    path("dashboard/admin/", views.admin_dashboard_view, name="admin_dashboard"),
    # Profile management
    path("profile/", profile_view, name="profile"),
    path("profile/edit/", ProfileEditView.as_view(), name="edit_profile"),
    path(
        "profile/password/", CustomPasswordChangeView.as_view(), name="password_change"
    ),
    # Legacy views (to be phased out)
    path("parent-legacy/", views.parent_view, name="parent_legacy"),
    path("student-legacy/", views.student_view, name="student_legacy"),
    # Other app URLs
    path("admissions-old/", include("admissions.urls")),
    # Health check and utilities
    path("health/", views.health_check, name="health_check"),
    # Detail views for entities
    path("student/<int:student_id>/", student_detail_view, name="student_detail"),
    path("course/<int:course_id>/", course_detail_view, name="course_detail"),
    path("teacher/<int:teacher_id>/", teacher_detail_view, name="teacher_detail"),
    path("assignment/<int:assignment_id>/", assignment_detail_view, name="assignment_detail"),
    # API landing page  
    path("api/", ApiLandingView.as_view(), name="api-landing"),
    # API endpoints - documentation and API v1
    path("api/", include("schooldriver_modern.api_urls")),
    # Legacy API v1 (disabled for now due to missing models)
    # path("api/v1/", include("api.urls")),
]

# Serve media and static files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(
        settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0]
    )
