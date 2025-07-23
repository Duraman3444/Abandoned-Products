from rest_framework import serializers
from .models import (
    Applicant,
    FeederSchool,
    AdmissionLevel,
    AdmissionCheck,
    ApplicantDocument,
)


class FeederSchoolSerializer(serializers.ModelSerializer):
    """Serializer for feeder schools."""

    class Meta:
        model = FeederSchool
        fields = [
            "id",
            "name",
            "school_type",
            "city",
            "state",
            "is_active",
            "created_at",
        ]


class AdmissionLevelSerializer(serializers.ModelSerializer):
    """Serializer for admission process levels."""

    class Meta:
        model = AdmissionLevel
        fields = ["id", "name", "order", "description", "is_active"]


class AdmissionCheckSerializer(serializers.ModelSerializer):
    """Serializer for admission requirements/checks."""

    level_name = serializers.CharField(source="level.name", read_only=True)

    class Meta:
        model = AdmissionCheck
        fields = ["id", "name", "level", "level_name", "is_required", "description", "is_active"]



class ApplicantDocumentSerializer(serializers.ModelSerializer):
    """Serializer for applicant document files."""

    class Meta:
        model = ApplicantDocument
        fields = ["id", "applicant", "file", "title", "document_type", "uploaded_at"]


class ApplicantSerializer(serializers.ModelSerializer):
    """Serializer for applicant information."""

    # Related field display names
    level_name = serializers.CharField(
        source="level.name", read_only=True
    )
    school_year_name = serializers.CharField(source="school_year.name", read_only=True)
    current_school_name = serializers.CharField(
        source="current_school.name", read_only=True
    )

    # Related objects
    completed_checks = AdmissionCheckSerializer(many=True, read_only=True)
    documents = ApplicantDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = Applicant
        fields = [
            "id",
            "first_name",
            "last_name",
            "date_of_birth",
            "gender",
            "level",
            "level_name",
            "school_year",
            "school_year_name",
            "applying_for_grade",
            "current_school",
            "current_school_name",
            "email",
            "street",
            "city",
            "state",
            "zip_code",
            "primary_parent_name",
            "primary_parent_email",
            "primary_parent_phone",
            "notes",
            "completed_checks",
            "documents",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class ApplicantCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new applicants with required fields only."""

    class Meta:
        model = Applicant
        fields = [
            "first_name",
            "last_name",
            "date_of_birth",
            "school_year",
            "applying_for_grade",
            "primary_parent_name",
            "primary_parent_phone",
        ]


class ApplicantSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for applicant lists."""

    level_name = serializers.CharField(
        source="level.name", read_only=True
    )

    class Meta:
        model = Applicant
        fields = [
            "id",
            "first_name",
            "last_name",
            "created_at",
            "level",
            "level_name",
            "primary_parent_phone",
        ]
