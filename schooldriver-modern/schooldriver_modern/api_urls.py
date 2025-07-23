from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from core.explorer_views import ApiLandingView

from students.api_views import (
    StudentViewSet,
    GradeLevelViewSet,
    SchoolYearViewSet,
    EmergencyContactViewSet,
)
from admissions.api_views import (
    ApplicantViewSet,
    FeederSchoolViewSet,
    AdmissionLevelViewSet,
    AdmissionCheckViewSet,
    ApplicantDocumentViewSet,
)

# Create a router and register our viewsets
router = DefaultRouter()

# Student endpoints
router.register(r"students", StudentViewSet, basename="student")
router.register(r"grade-levels", GradeLevelViewSet, basename="gradelevel")
router.register(r"school-years", SchoolYearViewSet, basename="schoolyear")
router.register(
    r"emergency-contacts", EmergencyContactViewSet, basename="emergencycontact"
)

# Admissions endpoints
router.register(r"applicants", ApplicantViewSet, basename="applicant")
router.register(r"feeder-schools", FeederSchoolViewSet, basename="feederschool")
router.register(r"admission-levels", AdmissionLevelViewSet, basename="admissionlevel")
router.register(r"admission-checks", AdmissionCheckViewSet, basename="admissioncheck")
router.register(r"applicant-documents", ApplicantDocumentViewSet, basename="applicantdocument")

urlpatterns = [
    # API documentation endpoints  
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("schema/swagger-ui/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("schema/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # Legacy docs endpoint (redirect to new swagger-ui)
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs-legacy"),
    # DRF auth endpoints
    path("auth/", include("rest_framework.urls")),
    # All API endpoints from router (students/, applicants/, etc.)
    path("v1/", include(router.urls)),
]
