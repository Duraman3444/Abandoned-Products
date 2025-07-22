from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Avg
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

from students.models import Student, SchoolYear
from academics.models import (
    Course,
    CourseSection,
    Enrollment,
    Assignment,
    Grade,
    Schedule,
    Attendance,
)
from admissions.models import Applicant

from .serializers import (
    UserSerializer,
    StudentSerializer,
    StudentSummarySerializer,
    CourseSerializer,
    CourseSectionSerializer,
    EnrollmentSerializer,
    AssignmentSerializer,
    GradeSerializer,
    ScheduleSerializer,
    AttendanceSerializer,
    ApplicantSerializer,
)


class StandardResultsSetPagination(PageNumberPagination):
    """Standard pagination for API responses."""

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class CustomAuthToken(ObtainAuthToken):
    """Custom auth token view that returns additional user info."""

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, created = Token.objects.get_or_create(user=user)
        return Response(
            {
                "token": token.key,
                "user_id": user.pk,
                "email": user.email,
                "name": f"{user.first_name} {user.last_name}".strip(),
                "is_staff": user.is_staff,
                "is_superuser": user.is_superuser,
            }
        )


class StudentViewSet(viewsets.ModelViewSet):
    """API endpoint for Student management."""

    queryset = Student.objects.all().select_related("grade_level")
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["grade_level", "is_active", "expected_graduation_year"]
    search_fields = ["first_name", "last_name", "student_id", "primary_contact_email"]
    ordering_fields = ["last_name", "first_name", "enrollment_date", "grade_level"]
    ordering = ["last_name", "first_name"]

    def get_serializer_class(self):
        if self.action == "list":
            return StudentSummarySerializer
        return StudentSerializer

    @action(detail=True, methods=["get"])
    def enrollments(self, request, pk=None):
        """Get all enrollments for a student."""
        student = self.get_object()
        enrollments = Enrollment.objects.filter(student=student).select_related(
            "section__course", "section__teacher", "section__school_year"
        )
        serializer = EnrollmentSerializer(enrollments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def grades(self, request, pk=None):
        """Get all grades for a student."""
        student = self.get_object()
        grades = Grade.objects.filter(enrollment__student=student).select_related(
            "assignment__section__course", "enrollment"
        )
        serializer = GradeSerializer(grades, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def schedule(self, request, pk=None):
        """Get current schedule for a student."""
        student = self.get_object()
        current_year = SchoolYear.objects.filter(is_active=True).first()
        schedules = Schedule.objects.filter(
            section__enrollments__student=student,
            section__school_year=current_year,
            is_active=True,
        ).select_related("section__course", "section__teacher")
        serializer = ScheduleSerializer(schedules, many=True)
        return Response(serializer.data)


class CourseViewSet(viewsets.ModelViewSet):
    """API endpoint for Course management."""

    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["subject", "is_active"]
    search_fields = ["name", "subject", "description"]
    ordering_fields = ["name", "subject", "credit_hours"]
    ordering = ["name"]

    @action(detail=True, methods=["get"])
    def sections(self, request, pk=None):
        """Get all sections for a course."""
        course = self.get_object()
        sections = CourseSection.objects.filter(course=course).select_related(
            "teacher", "school_year"
        )
        serializer = CourseSectionSerializer(sections, many=True)
        return Response(serializer.data)


class CourseSectionViewSet(viewsets.ModelViewSet):
    """API endpoint for CourseSection management."""

    queryset = CourseSection.objects.all().select_related(
        "course", "teacher", "school_year"
    )
    serializer_class = CourseSectionSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["course", "teacher", "school_year", "is_active"]
    search_fields = [
        "course__name",
        "teacher__first_name",
        "teacher__last_name",
        "room",
    ]
    ordering_fields = ["course__name", "section_number"]
    ordering = ["course__name", "section_number"]

    @action(detail=True, methods=["get"])
    def students(self, request, pk=None):
        """Get all students enrolled in this section."""
        section = self.get_object()
        enrollments = Enrollment.objects.filter(
            section=section, is_active=True
        ).select_related("student")
        students = [enrollment.student for enrollment in enrollments]
        serializer = StudentSummarySerializer(students, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def assignments(self, request, pk=None):
        """Get all assignments for this section."""
        section = self.get_object()
        assignments = Assignment.objects.filter(section=section)
        serializer = AssignmentSerializer(assignments, many=True)
        return Response(serializer.data)


class EnrollmentViewSet(viewsets.ModelViewSet):
    """API endpoint for Enrollment management."""

    queryset = Enrollment.objects.all().select_related(
        "student", "section__course", "section__teacher"
    )
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["student", "section", "section__school_year", "is_active"]
    ordering_fields = ["enrollment_date", "student__last_name"]
    ordering = ["-enrollment_date"]


class AssignmentViewSet(viewsets.ModelViewSet):
    """API endpoint for Assignment management."""

    queryset = Assignment.objects.all().select_related(
        "section__course", "section__teacher"
    )
    serializer_class = AssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["section", "section__course", "category", "is_published"]
    search_fields = ["name", "description", "section__course__name"]
    ordering_fields = ["due_date", "name", "created_at"]
    ordering = ["-due_date"]

    @action(detail=True, methods=["get"])
    def grades(self, request, pk=None):
        """Get all grades for this assignment."""
        assignment = self.get_object()
        grades = Grade.objects.filter(assignment=assignment).select_related(
            "enrollment__student"
        )
        serializer = GradeSerializer(grades, many=True)
        return Response(serializer.data)


class GradeViewSet(viewsets.ModelViewSet):
    """API endpoint for Grade management."""

    queryset = Grade.objects.all().select_related(
        "assignment__section__course", "enrollment__student"
    )
    serializer_class = GradeSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["assignment", "enrollment__student", "is_late", "is_excused"]
    ordering_fields = ["created_at", "assignment__due_date"]
    ordering = ["-created_at"]


class ScheduleViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for Schedule viewing."""

    queryset = Schedule.objects.all().select_related(
        "section__course", "section__teacher"
    )
    serializer_class = ScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["section", "section__school_year", "day_of_week", "is_active"]
    ordering_fields = ["day_of_week", "start_time"]
    ordering = ["day_of_week", "start_time"]


class AttendanceViewSet(viewsets.ModelViewSet):
    """API endpoint for Attendance management."""

    queryset = Attendance.objects.all().select_related(
        "enrollment__student", "enrollment__section__course"
    )
    serializer_class = AttendanceSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["enrollment__student", "enrollment__section", "status", "date"]
    ordering_fields = ["date"]
    ordering = ["-date"]


class ApplicantViewSet(viewsets.ModelViewSet):
    """API endpoint for Applicant management."""

    queryset = Applicant.objects.all()
    serializer_class = ApplicantSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["applying_for_grade"]
    search_fields = ["first_name", "last_name", "email"]
    ordering_fields = ["last_name", "first_name", "created_at"]
    ordering = ["last_name", "first_name"]


# ApplicationViewSet removed - using ApplicantViewSet instead
# since Application model doesn't exist in this codebase


class TeacherViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoint for Teacher (User) viewing."""

    queryset = User.objects.filter(
        is_active=True, taught_sections__isnull=False
    ).distinct()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["first_name", "last_name", "email", "username"]
    ordering_fields = ["last_name", "first_name"]
    ordering = ["last_name", "first_name"]

    @action(detail=True, methods=["get"])
    def sections(self, request, pk=None):
        """Get all sections taught by this teacher."""
        teacher = self.get_object()
        sections = CourseSection.objects.filter(teacher=teacher).select_related(
            "course", "school_year"
        )
        serializer = CourseSectionSerializer(sections, many=True)
        return Response(serializer.data)


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def api_stats(request):
    """Get overall statistics for the API dashboard."""
    # Student stats
    total_students = Student.objects.count()
    active_students = Student.objects.filter(is_active=True).count()
    students_by_grade = dict(
        Student.objects.filter(is_active=True)
        .values_list("grade_level__name")
        .annotate(count=Count("id"))
    )
    recent_enrollments = Enrollment.objects.filter(
        enrollment_date__gte=timezone.now() - timedelta(days=30)
    ).count()

    # Course stats
    total_courses = Course.objects.count()
    active_courses = Course.objects.filter(is_active=True).count()
    courses_by_subject = dict(
        Course.objects.filter(is_active=True)
        .values_list("subject")
        .annotate(count=Count("id"))
    )
    avg_enrollment = (
        Enrollment.objects.filter(is_active=True)
        .values("section")
        .annotate(student_count=Count("student"))
        .aggregate(avg=Avg("student_count"))["avg"]
        or 0
    )

    # Academic stats
    total_assignments = Assignment.objects.count()
    published_assignments = Assignment.objects.filter(is_published=True).count()
    avg_grade = (
        Grade.objects.filter(points_earned__isnull=False).aggregate(
            avg=Avg("percentage")
        )["avg"]
        or 0
    )

    total_attendance = Attendance.objects.count()
    present_attendance = Attendance.objects.filter(status="P").count()
    attendance_rate = (
        (present_attendance / total_attendance * 100) if total_attendance > 0 else 0
    )

    return Response(
        {
            "students": {
                "total_students": total_students,
                "active_students": active_students,
                "by_grade_level": students_by_grade,
                "recent_enrollments": recent_enrollments,
            },
            "courses": {
                "total_courses": total_courses,
                "active_courses": active_courses,
                "by_subject": courses_by_subject,
                "average_enrollment": round(avg_enrollment, 2),
            },
            "academics": {
                "total_assignments": total_assignments,
                "published_assignments": published_assignments,
                "average_grade": round(avg_grade, 2),
                "attendance_rate": round(attendance_rate, 2),
            },
        }
    )


@api_view(["GET"])
@permission_classes([permissions.IsAuthenticated])
def api_health(request):
    """API health check endpoint."""
    return Response(
        {
            "status": "healthy",
            "timestamp": timezone.now(),
            "version": "v1",
            "user": request.user.username if request.user.is_authenticated else None,
        }
    )
