from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import GradeLevel, SchoolYear, EmergencyContact, Student, ParentVerificationCode


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
            "Parent Portal Access",
            {
                "fields": ("family_access_users",),
                "description": "Users who can access this student's information via the parent portal."
            }
        ),
        (
            "System Information",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    filter_horizontal = ["emergency_contacts", "family_access_users"]
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


@admin.register(ParentVerificationCode)
class ParentVerificationCodeAdmin(admin.ModelAdmin):
    list_display = [
        'code',
        'student_link',
        'parent_name',
        'parent_email',
        'status',
        'expires_at',
        'created_by',
        'created_at'
    ]
    list_filter = ['is_used', 'expires_at', 'created_at', 'used_at']
    search_fields = ['code', 'parent_name', 'parent_email', 'student__first_name', 'student__last_name']
    readonly_fields = ['code', 'used_by', 'used_at', 'created_at']
    
    fieldsets = (
        ('Verification Code', {
            'fields': ('code', 'student', 'expires_at')
        }),
        ('Parent Information', {
            'fields': ('parent_name', 'parent_email')
        }),
        ('Status', {
            'fields': ('is_used', 'used_by', 'used_at')
        }),
        ('Administrative', {
            'fields': ('created_by', 'created_at', 'notes'),
            'classes': ('collapse',)
        })
    )
    
    def student_link(self, obj):
        if obj.student:
            return format_html(
                '<a href="/admin/students/student/{}/change/">{}</a>',
                obj.student.id,
                obj.student.full_name
            )
        return '-'
    student_link.short_description = 'Student'
    student_link.admin_order_field = 'student__last_name'
    
    def status(self, obj):
        if obj.is_used:
            return format_html('<span style="color: green;">✓ Used</span>')
        elif obj.is_expired():
            return format_html('<span style="color: red;">✗ Expired</span>')
        else:
            return format_html('<span style="color: blue;">⏳ Active</span>')
    status.short_description = 'Status'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by for new objects
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student', 'created_by', 'used_by')


# Customize admin site
admin.site.site_header = "SchoolDriver Modern - Administration"
admin.site.site_title = "SchoolDriver Modern Admin"
admin.site.index_title = "Welcome to SchoolDriver Modern"
