from rest_framework import viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view
from .models import Student, GradeLevel, SchoolYear, EmergencyContact
from .serializers import (
    StudentSerializer, StudentCreateSerializer, GradeLevelSerializer,
    SchoolYearSerializer, EmergencyContactSerializer
)


@extend_schema_view(
    list=extend_schema(description="List all grade levels", tags=["students"]),
    retrieve=extend_schema(description="Get a specific grade level", tags=["students"]),
    create=extend_schema(description="Create a new grade level", tags=["students"]),
    update=extend_schema(description="Update a grade level", tags=["students"]),
    destroy=extend_schema(description="Delete a grade level", tags=["students"])
)
class GradeLevelViewSet(viewsets.ModelViewSet):
    """ViewSet for managing grade levels (K, 1st, 2nd, etc.)."""
    
    queryset = GradeLevel.objects.all()
    serializer_class = GradeLevelSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['order', 'name']
    ordering = ['order']


@extend_schema_view(
    list=extend_schema(description="List all school years", tags=["students"]),
    retrieve=extend_schema(description="Get a specific school year", tags=["students"]),
    create=extend_schema(description="Create a new school year", tags=["students"]),
    update=extend_schema(description="Update a school year", tags=["students"]),
    destroy=extend_schema(description="Delete a school year", tags=["students"])
)
class SchoolYearViewSet(viewsets.ModelViewSet):
    """ViewSet for managing academic years (2024-2025, etc.)."""
    
    queryset = SchoolYear.objects.all()
    serializer_class = SchoolYearSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['is_active']
    ordering_fields = ['start_date', 'name']
    ordering = ['-start_date']
    
    @extend_schema(description="Get the currently active school year", tags=["students"])
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Return the currently active school year."""
        try:
            current_year = SchoolYear.objects.get(is_active=True)
            serializer = self.get_serializer(current_year)
            return Response(serializer.data)
        except SchoolYear.DoesNotExist:
            return Response({'error': 'No active school year found'}, status=404)


@extend_schema_view(
    list=extend_schema(description="List all students with filtering and search", tags=["students"]),
    retrieve=extend_schema(description="Get detailed student information", tags=["students"]),
    create=extend_schema(description="Create a new student record", tags=["students"]),
    update=extend_schema(description="Update student information", tags=["students"]),
    destroy=extend_schema(description="Remove a student record", tags=["students"])
)
class StudentViewSet(viewsets.ModelViewSet):
    """ViewSet for managing student records."""
    
    queryset = Student.objects.select_related('grade_level', 'school_year').prefetch_related('emergency_contacts')
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['first_name', 'last_name', 'student_id']
    filterset_fields = ['grade_level', 'school_year', 'is_active', 'gender']
    ordering_fields = ['last_name', 'first_name', 'enrollment_date', 'created_at']
    ordering = ['last_name', 'first_name']
    
    def get_serializer_class(self):
        """Use different serializers for create vs other actions."""
        if self.action == 'create':
            return StudentCreateSerializer
        return StudentSerializer
    
    @extend_schema(
        description="Get students by grade level",
        tags=["students"],
        parameters=[
            {
                'name': 'grade_level_id',
                'in': 'path',
                'required': True,
                'schema': {'type': 'string', 'format': 'uuid'}
            }
        ]
    )
    @action(detail=False, methods=['get'], url_path='by-grade/(?P<grade_level_id>[^/.]+)')
    def by_grade(self, request, grade_level_id=None):
        """Get all students in a specific grade level."""
        students = self.get_queryset().filter(grade_level_id=grade_level_id)
        serializer = self.get_serializer(students, many=True)
        return Response(serializer.data)
    
    @extend_schema(description="Get student statistics", tags=["students"])
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get statistics about students."""
        queryset = self.get_queryset()
        stats = {
            'total_students': queryset.count(),
            'active_students': queryset.filter(is_active=True).count(),
            'by_grade': {}
        }
        
        # Count by grade level
        for grade in GradeLevel.objects.all():
            count = queryset.filter(grade_level=grade).count()
            stats['by_grade'][grade.name] = count
        
        return Response(stats)


@extend_schema_view(
    list=extend_schema(description="List emergency contacts", tags=["students"]),
    retrieve=extend_schema(description="Get emergency contact details", tags=["students"]),
    create=extend_schema(description="Add new emergency contact", tags=["students"]),
    update=extend_schema(description="Update emergency contact", tags=["students"]),
    destroy=extend_schema(description="Remove emergency contact", tags=["students"])
)
class EmergencyContactViewSet(viewsets.ModelViewSet):
    """ViewSet for managing student emergency contacts."""
    
    queryset = EmergencyContact.objects.select_related('student')
    serializer_class = EmergencyContactSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['student', 'is_primary', 'relationship']
    ordering_fields = ['last_name', 'first_name']
    ordering = ['last_name', 'first_name']
