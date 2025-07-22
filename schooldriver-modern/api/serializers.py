from rest_framework import serializers
from django.contrib.auth.models import User
from students.models import Student, SchoolYear, GradeLevel, EmergencyContact
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


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model (teachers, staff)."""

    full_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "is_active",
            "date_joined",
        ]
        read_only_fields = ["id", "date_joined"]

    def get_full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()


class GradeLevelSerializer(serializers.ModelSerializer):
    """Serializer for GradeLevel model."""

    class Meta:
        model = GradeLevel
        fields = ["id", "name", "order"]


class SchoolYearSerializer(serializers.ModelSerializer):
    """Serializer for SchoolYear model."""

    class Meta:
        model = SchoolYear
        fields = ["id", "name", "start_date", "end_date", "is_active"]


class EmergencyContactSerializer(serializers.ModelSerializer):
    """Serializer for EmergencyContact model."""

    class Meta:
        model = EmergencyContact
        fields = [
            "id",
            "first_name",
            "last_name",
            "relationship",
            "phone_number",
            "email",
            "is_primary",
        ]


class StudentSerializer(serializers.ModelSerializer):
    """Serializer for Student model."""

    grade_level = GradeLevelSerializer(read_only=True)
    emergency_contacts = EmergencyContactSerializer(many=True, read_only=True)
    age = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = [
            "id",
            "student_id",
            "first_name",
            "last_name",
            "date_of_birth",
            "grade_level",
            "primary_contact_email",
            "phone_number",
            "address",
            "enrollment_date",
            "expected_graduation_year",
            "is_active",
            "emergency_contacts",
            "age",
        ]
        read_only_fields = ["id", "student_id", "age"]

    def get_age(self, obj):
        return obj.get_age()


class StudentSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for Student model (for lists)."""

    grade_level_name = serializers.CharField(source="grade_level.name", read_only=True)

    class Meta:
        model = Student
        fields = [
            "id",
            "student_id",
            "first_name",
            "last_name",
            "grade_level_name",
            "is_active",
        ]


class CourseSerializer(serializers.ModelSerializer):
    """Serializer for Course model."""

    class Meta:
        model = Course
        fields = ["id", "name", "subject", "description", "credit_hours", "is_active"]


class CourseSectionSerializer(serializers.ModelSerializer):
    """Serializer for CourseSection model."""

    course = CourseSerializer(read_only=True)
    teacher = UserSerializer(read_only=True)
    school_year = SchoolYearSerializer(read_only=True)
    student_count = serializers.SerializerMethodField()

    class Meta:
        model = CourseSection
        fields = [
            "id",
            "course",
            "teacher",
            "school_year",
            "section_number",
            "room",
            "max_students",
            "student_count",
            "is_active",
        ]

    def get_student_count(self, obj):
        return obj.enrollments.filter(is_active=True).count()


class EnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for Enrollment model."""

    student = StudentSummarySerializer(read_only=True)
    section = CourseSectionSerializer(read_only=True)
    current_grade = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = [
            "id",
            "student",
            "section",
            "enrollment_date",
            "is_active",
            "current_grade",
        ]

    def get_current_grade(self, obj):
        # Calculate current grade from assignments
        grades = Grade.objects.filter(enrollment=obj, assignment__is_published=True)
        if grades.exists():
            total_points = sum(float(g.points_earned or 0) for g in grades)
            max_points = sum(float(g.assignment.max_points) for g in grades)
            percentage = (total_points / max_points * 100) if max_points > 0 else 0
            return round(percentage, 2)
        return None


class AssignmentSerializer(serializers.ModelSerializer):
    """Serializer for Assignment model."""

    section = CourseSectionSerializer(read_only=True)
    course_name = serializers.CharField(source="section.course.name", read_only=True)

    class Meta:
        model = Assignment
        fields = [
            "id",
            "name",
            "description",
            "due_date",
            "max_points",
            "category",
            "is_published",
            "section",
            "course_name",
            "created_at",
        ]


class GradeSerializer(serializers.ModelSerializer):
    """Serializer for Grade model."""

    assignment = AssignmentSerializer(read_only=True)
    enrollment = EnrollmentSerializer(read_only=True)
    letter_grade = serializers.SerializerMethodField()

    class Meta:
        model = Grade
        fields = [
            "id",
            "assignment",
            "enrollment",
            "points_earned",
            "percentage",
            "letter_grade",
            "is_late",
            "is_excused",
            "comments",
            "created_at",
        ]

    def get_letter_grade(self, obj):
        from student_portal.utils import gpa as gpa_utils

        percentage = float(obj.percentage) if obj.percentage else 0
        return gpa_utils.get_letter_grade(percentage)


class ScheduleSerializer(serializers.ModelSerializer):
    """Serializer for Schedule model."""

    section = CourseSectionSerializer(read_only=True)
    day_name = serializers.CharField(source="get_day_of_week_display", read_only=True)

    class Meta:
        model = Schedule
        fields = [
            "id",
            "section",
            "day_of_week",
            "day_name",
            "start_time",
            "end_time",
            "room",
            "is_active",
        ]


class AttendanceSerializer(serializers.ModelSerializer):
    """Serializer for Attendance model."""

    enrollment = EnrollmentSerializer(read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Attendance
        fields = ["id", "enrollment", "date", "status", "status_display", "notes"]


class ApplicantSerializer(serializers.ModelSerializer):
    """Serializer for Applicant model."""

    class Meta:
        model = Applicant
        fields = [
            "id",
            "first_name",
            "last_name",
            "date_of_birth",
            "email",
            "primary_parent_phone",
            "street",
            "applying_for_grade",
            "created_at",
        ]


# Note: Application model doesn't exist in this codebase
# Using Applicant model which contains the application information


# Summary serializers for analytics and dashboards
class StudentStatsSerializer(serializers.Serializer):
    """Serializer for student statistics."""

    total_students = serializers.IntegerField()
    active_students = serializers.IntegerField()
    by_grade_level = serializers.DictField()
    recent_enrollments = serializers.IntegerField()


class CourseStatsSerializer(serializers.Serializer):
    """Serializer for course statistics."""

    total_courses = serializers.IntegerField()
    active_courses = serializers.IntegerField()
    by_subject = serializers.DictField()
    average_enrollment = serializers.FloatField()


class AcademicStatsSerializer(serializers.Serializer):
    """Serializer for academic statistics."""

    total_assignments = serializers.IntegerField()
    published_assignments = serializers.IntegerField()
    average_grade = serializers.FloatField()
    attendance_rate = serializers.FloatField()
