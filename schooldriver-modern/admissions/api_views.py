from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import (
    Applicant,
    FeederSchool,
    AdmissionLevel,
    AdmissionCheck,
    ApplicantDocument,
)
from .serializers import (
    ApplicantSerializer,
    ApplicantCreateSerializer,
    ApplicantSummarySerializer,
    FeederSchoolSerializer,
    AdmissionLevelSerializer,
    AdmissionCheckSerializer,
    ApplicantDocumentSerializer,
)


@extend_schema_view(
    list=extend_schema(description="List all feeder schools", tags=["admissions"]),
    retrieve=extend_schema(
        description="Get feeder school details", tags=["admissions"]
    ),
    create=extend_schema(description="Create a new feeder school", tags=["admissions"]),
    update=extend_schema(
        description="Update feeder school information", tags=["admissions"]
    ),
    destroy=extend_schema(description="Delete a feeder school", tags=["admissions"]),
)
class FeederSchoolViewSet(viewsets.ModelViewSet):
    """ViewSet for managing feeder schools."""

    queryset = FeederSchool.objects.all()
    serializer_class = FeederSchoolSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        DjangoFilterBackend,
    ]
    search_fields = ["name", "city", "state"]
    filterset_fields = ["school_type", "is_active", "state"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]


@extend_schema_view(
    list=extend_schema(
        description="List admission process levels", tags=["admissions"]
    ),
    retrieve=extend_schema(
        description="Get admission level details", tags=["admissions"]
    ),
    create=extend_schema(description="Create new admission level", tags=["admissions"]),
    update=extend_schema(description="Update admission level", tags=["admissions"]),
    destroy=extend_schema(description="Delete admission level", tags=["admissions"]),
)
class AdmissionLevelViewSet(viewsets.ModelViewSet):
    """ViewSet for managing admission process levels."""

    queryset = AdmissionLevel.objects.all()
    serializer_class = AdmissionLevelSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ["is_active"]
    ordering_fields = ["order", "name"]
    ordering = ["order"]


@extend_schema_view(
    list=extend_schema(
        description="List admission requirements/checks", tags=["admissions"]
    ),
    retrieve=extend_schema(
        description="Get admission check details", tags=["admissions"]
    ),
    create=extend_schema(description="Create new admission check", tags=["admissions"]),
    update=extend_schema(description="Update admission check", tags=["admissions"]),
    destroy=extend_schema(description="Delete admission check", tags=["admissions"]),
)
class AdmissionCheckViewSet(viewsets.ModelViewSet):
    """ViewSet for managing admission requirements and checks."""

    queryset = AdmissionCheck.objects.all()
    serializer_class = AdmissionCheckSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        DjangoFilterBackend,
    ]
    search_fields = ["name"]
    filterset_fields = ["level", "is_required", "is_active"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]


@extend_schema_view(
    list=extend_schema(
        description="List all applicants with filtering", tags=["admissions"]
    ),
    retrieve=extend_schema(
        description="Get detailed applicant information", tags=["admissions"]
    ),
    create=extend_schema(description="Create a new applicant", tags=["admissions"]),
    update=extend_schema(
        description="Update applicant information", tags=["admissions"]
    ),
    destroy=extend_schema(description="Remove an applicant", tags=["admissions"]),
)
class ApplicantViewSet(viewsets.ModelViewSet):
    """ViewSet for managing applicant records."""

    queryset = Applicant.objects.select_related(
        "level", "school_year", "current_school", "applying_for_grade"
    ).prefetch_related("completed_checks", "documents")
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [
        filters.SearchFilter,
        filters.OrderingFilter,
        DjangoFilterBackend,
    ]
    search_fields = ["first_name", "last_name", "primary_parent_name"]
    filterset_fields = [
        "level",
        "school_year",
        "applying_for_grade",
        "current_school",
        "gender",
    ]
    ordering_fields = ["last_name", "first_name", "created_at"]
    ordering = ["-created_at", "last_name"]

    def get_serializer_class(self):
        """Use different serializers based on action."""
        if self.action == "create":
            return ApplicantCreateSerializer
        elif self.action == "list":
            return ApplicantSummarySerializer
        return ApplicantSerializer

    @extend_schema(
        description="Advance applicant to next admission level",
        tags=["admissions"],
        request=None,
        responses={200: ApplicantSerializer},
    )
    @action(detail=True, methods=["post"])
    def advance_level(self, request, pk=None):
        """Advance applicant to the next admission level."""
        applicant = self.get_object()

        try:
            applicant.advance_to_next_level()
            serializer = ApplicantSerializer(applicant)
            return Response(serializer.data)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        description="Check if applicant can advance to next level", tags=["admissions"]
    )
    @action(detail=True, methods=["get"])
    def can_advance(self, request, pk=None):
        """Check if applicant has completed requirements for current level."""
        applicant = self.get_object()
        can_advance = applicant.can_advance_to_next_level()

        return Response(
            {
                "can_advance": can_advance,
                "level": applicant.level.name
                if applicant.level
                else None,
                "completed_checks_count": applicant.completed_checks.count(),
            }
        )

    @extend_schema(
        description="Get applicants by admission level",
        tags=["admissions"],
        parameters=[
            {
                "name": "level_id",
                "in": "path",
                "required": True,
                "schema": {"type": "string", "format": "uuid"},
            }
        ],
    )
    @action(detail=False, methods=["get"], url_path="by-level/(?P<level_id>[^/.]+)")
    def by_level(self, request, level_id=None):
        """Get all applicants at a specific admission level."""
        applicants = self.get_queryset().filter(level_id=level_id)
        serializer = ApplicantSummarySerializer(applicants, many=True)
        return Response(serializer.data)

    @extend_schema(description="Get admission statistics", tags=["admissions"])
    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get statistics about the admissions process."""
        queryset = self.get_queryset()
        stats = {
            "total_applicants": queryset.count(),
            "by_level": {},
            "by_grade": {},
            "recent_applications": queryset.filter(application_date__isnull=False)
            .order_by("-application_date")[:5]
            .count(),
        }

        # Count by admission level
        for level in AdmissionLevel.objects.filter(is_active=True):
            count = queryset.filter(level=level).count()
            stats["by_level"][level.name] = count

        # Count by target grade
        grade_counts = queryset.values("applying_for_grade__name").distinct().count()
        stats["by_grade"] = grade_counts

        return Response(stats)


@extend_schema_view(
    list=extend_schema(description="List applicant files", tags=["admissions"]),
    retrieve=extend_schema(description="Get file details", tags=["admissions"]),
    create=extend_schema(description="Upload new file", tags=["admissions"]),
    destroy=extend_schema(description="Delete file", tags=["admissions"]),
)
class ApplicantDocumentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing applicant document files."""

    queryset = ApplicantDocument.objects.select_related("applicant")
    serializer_class = ApplicantDocumentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["applicant"]
    ordering_fields = ["uploaded_at", "description"]
    ordering = ["-uploaded_at"]
    http_method_names = ["get", "post", "delete"]  # No PUT/PATCH for files
