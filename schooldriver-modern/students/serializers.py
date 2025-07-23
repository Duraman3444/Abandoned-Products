from rest_framework import serializers
from .models import Student, GradeLevel, SchoolYear, EmergencyContact


class GradeLevelSerializer(serializers.ModelSerializer):
    """Serializer for grade levels like K, 1st, 2nd, etc."""

    class Meta:
        model = GradeLevel
        fields = ["id", "name", "order"]


class SchoolYearSerializer(serializers.ModelSerializer):
    """Serializer for academic years like 2024-2025."""

    class Meta:
        model = SchoolYear
        fields = ["id", "name", "start_date", "end_date", "is_active"]


class EmergencyContactSerializer(serializers.ModelSerializer):
    """Serializer for student emergency contacts."""

    class Meta:
        model = EmergencyContact
        fields = [
            "id",
            "first_name",
            "last_name",
            "relationship",
            "phone_primary",
            "phone_secondary",
            "email",
            "street",
            "city",
            "state",
            "zip_code",
            "is_primary",
        ]


class StudentSerializer(serializers.ModelSerializer):
    """Serializer for student information."""

    emergency_contacts = EmergencyContactSerializer(many=True, read_only=True)
    grade_level_name = serializers.CharField(source="grade_level.name", read_only=True)
    # school_year_name = serializers.CharField(source="school_year.name", read_only=True)

    class Meta:
        model = Student
        fields = [
            "id",
            "student_id",
            "first_name",
            "last_name",
            "date_of_birth",
            "gender",
            "grade_level",
            "grade_level_name",
            "enrollment_date",
            "is_active",
            "primary_contact_name",
            "primary_contact_phone",
            "primary_contact_email",
            "photo",
            "special_needs",
            "notes",
            "emergency_contacts",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class StudentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new students with required fields only."""

    class Meta:
        model = Student
        fields = [
            "first_name",
            "last_name",
            "date_of_birth",
            "gender",
            "grade_level",
            "primary_contact_name",
            "primary_contact_phone",
        ]
