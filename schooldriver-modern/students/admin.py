from django.contrib import admin
from django.utils.html import format_html
from .models import GradeLevel, SchoolYear, EmergencyContact, Student


@admin.register(GradeLevel)
class GradeLevelAdmin(admin.ModelAdmin):
    list_display = ["name", "order"]
    list_editable = ["order"]
    ordering = ["order"]
    search_fields = ["name"]


@admin.register(SchoolYear)
class SchoolYearAdmin(admin.ModelAdmin):
    list_display = ["name", "start_date", "end_date", "is_active"]
    list_filter = ["is_active"]
    list_editable = ["is_active"]
    ordering = ["-start_date"]
    date_hierarchy = "start_date"


@admin.register(EmergencyContact)
class EmergencyContactAdmin(admin.ModelAdmin):
    list_display = [
        "full_name",
        "relationship",
        "email",
        "phone_primary",
        "is_primary",
        "created_at",
    ]
    list_filter = ["relationship", "is_primary", "state"]
    search_fields = ["first_name", "last_name", "email", "phone_primary"]
    readonly_fields = ["created_at", "updated_at"]

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("first_name", "last_name", "relationship", "is_primary")},
        ),
        (
            "Contact Information",
            {"fields": ("email", "phone_primary", "phone_secondary")},
        ),
        ("Address", {"fields": ("street", "city", "state", "zip_code")}),
        (
            "System Information",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    def full_name(self, obj):
        return obj.full_name

    full_name.short_description = "Name"


class EmergencyContactInline(admin.TabularInline):
    model = Student.emergency_contacts.through
    extra = 1
    verbose_name = "Emergency Contact"
    verbose_name_plural = "Emergency Contacts"


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = [
        "student_id",
        "display_name",
        "grade_level",
        "get_age",
        "is_active",
        "enrollment_date",
        "primary_contact_name",
    ]
    list_filter = ["is_active", "grade_level", "graduation_year", "enrollment_date"]
    search_fields = [
        "first_name",
        "last_name",
        "preferred_name",
        "student_id",
        "primary_contact_name",
        "primary_contact_email",
    ]
    readonly_fields = [
        "student_id",
        "primary_contact_name",
        "primary_contact_email",
        "primary_contact_phone",
        "created_at",
        "updated_at",
        "get_age",
    ]

    fieldsets = (
        (
            "Student Information",
            {
                "fields": (
                    ("first_name", "middle_name", "last_name"),
                    "preferred_name",
                    ("date_of_birth", "gender"),
                    "photo",
                )
            },
        ),
        (
            "Academic Information",
            {
                "fields": (
                    "student_id",
                    ("grade_level", "graduation_year"),
                    ("enrollment_date", "graduation_date"),
                )
            },
        ),
        ("Status", {"fields": ("is_active", ("withdrawal_date", "withdrawal_reason"))}),
        (
            "Additional Information",
            {"fields": ("special_needs", "notes"), "classes": ("collapse",)},
        ),
        (
            "Contact Information (Cached)",
            {
                "fields": (
                    "primary_contact_name",
                    "primary_contact_email",
                    "primary_contact_phone",
                ),
                "classes": ("collapse",),
                "description": "This information is automatically updated from emergency contacts.",
            },
        ),
        (
            "System Information",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    filter_horizontal = ["emergency_contacts"]
    date_hierarchy = "enrollment_date"

    def get_age(self, obj):
        return f"{obj.get_age()} years"

    get_age.short_description = "Age"

    def display_name(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="width: 30px; height: 30px; border-radius: 50%; margin-right: 10px; vertical-align: middle;">'
                "<span>{}</span>",
                obj.photo.url,
                obj.display_name,
            )
        return obj.display_name

    display_name.short_description = "Name"

    def save_model(self, request, obj, form, change):
        """Override save to ensure cached contact info is updated"""
        super().save_model(request, obj, form, change)
        # The model's save method will handle updating cached contact info


# Customize admin site
admin.site.site_header = "SchoolDriver Modern - Administration"
admin.site.site_title = "SchoolDriver Modern Admin"
admin.site.index_title = "Welcome to SchoolDriver Modern"
