from rest_framework import serializers
from .models import (
    Applicant, FeederSchool, AdmissionLevel, AdmissionCheck,
    ApplicationTemplate, ApplicantFile
)


class FeederSchoolSerializer(serializers.ModelSerializer):
    """Serializer for feeder schools."""
    
    class Meta:
        model = FeederSchool
        fields = ['id', 'name', 'school_type', 'city', 'state', 'is_active', 'created_at']


class AdmissionLevelSerializer(serializers.ModelSerializer):
    """Serializer for admission process levels."""
    
    class Meta:
        model = AdmissionLevel
        fields = ['id', 'name', 'order', 'is_default_first_level', 'is_active']


class AdmissionCheckSerializer(serializers.ModelSerializer):
    """Serializer for admission requirements/checks."""
    
    class Meta:
        model = AdmissionCheck
        fields = ['id', 'name', 'required_for_level', 'is_active', 'created_at']


class ApplicationTemplateSerializer(serializers.ModelSerializer):
    """Serializer for application form templates."""
    
    class Meta:
        model = ApplicationTemplate
        fields = ['id', 'name', 'is_default', 'is_active', 'created_at']


class ApplicantFileSerializer(serializers.ModelSerializer):
    """Serializer for applicant document files."""
    
    class Meta:
        model = ApplicantFile
        fields = ['id', 'applicant', 'file', 'description', 'uploaded_at']


class ApplicantSerializer(serializers.ModelSerializer):
    """Serializer for applicant information."""
    
    # Related field display names
    current_level_name = serializers.CharField(source='current_level.name', read_only=True)
    school_year_name = serializers.CharField(source='school_year.name', read_only=True)
    feeder_school_name = serializers.CharField(source='feeder_school.name', read_only=True)
    
    # Related objects
    completed_checks = AdmissionCheckSerializer(many=True, read_only=True)
    files = ApplicantFileSerializer(many=True, read_only=True)
    
    class Meta:
        model = Applicant
        fields = [
            'id', 'first_name', 'last_name', 'date_of_birth', 'gender',
            'current_level', 'current_level_name', 'school_year', 'school_year_name',
            'application_date', 'target_grade_level', 'feeder_school',
            'feeder_school_name', 'guardian_name', 'guardian_phone', 'guardian_email',
            'address', 'city', 'state', 'zip_code', 'application_notes',
            'completed_checks', 'files', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class ApplicantCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new applicants with required fields only."""
    
    class Meta:
        model = Applicant
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'school_year',
            'target_grade_level', 'guardian_name', 'guardian_phone'
        ]


class ApplicantSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for applicant lists."""
    
    current_level_name = serializers.CharField(source='current_level.name', read_only=True)
    
    class Meta:
        model = Applicant
        fields = [
            'id', 'first_name', 'last_name', 'application_date',
            'current_level', 'current_level_name', 'guardian_phone'
        ]
