from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

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
    ApplicantFileViewSet,
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
router.register(r"applicant-files", ApplicantFileViewSet, basename="applicantfile")

urlpatterns = [
    # API documentation endpoints
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    # DRF auth endpoints
    path("auth/", include("rest_framework.urls")),
    # All API endpoints
    path("", include(router.urls)),
]
