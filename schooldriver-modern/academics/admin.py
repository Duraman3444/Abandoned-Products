from django.contrib import admin
from .models import (
    Department,
    Course,
    CourseSection,
    Enrollment,
    AssignmentCategory,
    Assignment,
    Grade,
    Schedule,
    Attendance,
    EarlyDismissalRequest,
    AttendanceNotification,
    SchoolCalendarEvent,
    Announcement,
    Message,
    MessageAttachment,
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ["name", "head", "is_active", "created_at"]
    list_filter = ["is_active", "created_at"]
    search_fields = ["name"]


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ["course_code", "name", "department", "credit_hours", "is_active"]
    list_filter = ["department", "is_active", "credit_hours"]
    search_fields = ["course_code", "name"]
    filter_horizontal = ["prerequisites"]


class ScheduleInline(admin.TabularInline):
    model = Schedule
    extra = 1


class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 0
    readonly_fields = ["enrollment_date"]


@admin.register(CourseSection)
class CourseSectionAdmin(admin.ModelAdmin):
    list_display = [
        "course",
        "section_name",
        "teacher",
        "school_year",
        "room",
        "is_active",
    ]
    list_filter = ["school_year", "course__department", "is_active"]
    search_fields = ["course__course_code", "course__name", "teacher__username"]
    inlines = [ScheduleInline, EnrollmentInline]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = [
        "student",
        "section",
        "final_grade",
        "final_percentage",
        "is_active",
    ]
    list_filter = [
        "section__school_year",
        "section__course__department",
        "is_active",
        "final_grade",
    ]
    search_fields = [
        "student__first_name",
        "student__last_name",
        "section__course__course_code",
    ]
    readonly_fields = ["enrollment_date"]


@admin.register(AssignmentCategory)
class AssignmentCategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "default_weight", "is_active"]
    list_filter = ["is_active"]
    search_fields = ["name"]


class GradeInline(admin.TabularInline):
    model = Grade
    extra = 0
    readonly_fields = ["percentage", "created_at"]


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "section",
        "category",
        "due_date",
        "max_points",
        "is_published",
    ]
    list_filter = ["section__school_year", "category", "is_published", "due_date"]
    search_fields = ["name", "section__course__course_code"]
    date_hierarchy = "due_date"
    inlines = [GradeInline]


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = [
        "enrollment",
        "assignment",
        "points_earned",
        "percentage",
        "letter_grade",
        "is_excused",
    ]
    list_filter = [
        "assignment__section__school_year",
        "assignment__category",
        "letter_grade",
        "is_excused",
        "is_late",
    ]
    search_fields = [
        "enrollment__student__first_name",
        "enrollment__student__last_name",
        "assignment__name",
    ]
    readonly_fields = ["percentage", "created_at"]


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = [
        "section",
        "day_of_week",
        "start_time",
        "end_time",
        "room",
        "is_active",
    ]
    list_filter = ["day_of_week", "is_active", "section__school_year"]
    search_fields = ["section__course__course_code", "room"]


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ["enrollment", "date", "status", "recorded_by", "recorded_at"]
    list_filter = ["status", "date", "enrollment__section__school_year"]
    search_fields = [
        "enrollment__student__first_name",
        "enrollment__student__last_name",
        "enrollment__section__course__course_code",
    ]
    date_hierarchy = "date"


@admin.register(EarlyDismissalRequest)
class EarlyDismissalRequestAdmin(admin.ModelAdmin):
    list_display = ["student", "request_date", "dismissal_time", "status", "requested_by", "processed_by"]
    list_filter = ["status", "request_date", "is_recurring"]
    search_fields = ["student__first_name", "student__last_name", "reason"]
    date_hierarchy = "request_date"
    readonly_fields = ["created_at", "updated_at"]
    
    fieldsets = (
        ("Request Information", {
            "fields": ("student", "requested_by", "request_date", "dismissal_time", "reason")
        }),
        ("Pickup Details", {
            "fields": ("pickup_person", "contact_phone")
        }),
        ("Status", {
            "fields": ("status", "processed_by", "processed_at", "school_notes", "actual_dismissal_time")
        }),
        ("Recurring Options", {
            "fields": ("is_recurring", "recurring_days", "recurring_end_date"),
            "classes": ("collapse",)
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",)
        })
    )


@admin.register(AttendanceNotification)
class AttendanceNotificationAdmin(admin.ModelAdmin):
    list_display = ["student", "recipient", "notification_type", "is_sent", "sent_at", "created_at"]
    list_filter = ["notification_type", "is_sent", "delivery_method", "created_at"]
    search_fields = ["student__first_name", "student__last_name", "recipient__email"]
    readonly_fields = ["created_at", "sent_at"]
    date_hierarchy = "created_at"


@admin.register(SchoolCalendarEvent)
class SchoolCalendarEventAdmin(admin.ModelAdmin):
    list_display = ["title", "event_type", "start_date", "end_date", "is_public", "affects_all_students", "school_year"]
    list_filter = ["event_type", "is_public", "affects_all_students", "school_year", "start_date"]
    search_fields = ["title", "description"]
    date_hierarchy = "start_date"
    readonly_fields = ["created_at", "updated_at"]
    
    fieldsets = (
        ("Event Information", {
            "fields": ("title", "description", "event_type", "school_year")
        }),
        ("Schedule", {
            "fields": ("start_date", "end_date", "start_time", "end_time", "dismissal_time")
        }),
        ("Display Options", {
            "fields": ("is_public", "color")
        }),
        ("Affected Students", {
            "fields": ("affects_all_students", "specific_grades")
        }),
        ("Metadata", {
            "fields": ("created_by", "created_at", "updated_at"),
            "classes": ("collapse",)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by for new objects
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "audience",
        "is_published",
        "is_urgent",
        "publish_date",
        "created_by",
    ]
    list_filter = ["audience", "is_published", "is_urgent", "publish_date"]
    search_fields = ["title", "content"]
    date_hierarchy = "publish_date"


class MessageAttachmentInline(admin.TabularInline):
    model = MessageAttachment
    extra = 0
    readonly_fields = ["original_filename", "file_size", "content_type", "uploaded_at", "download_count"]


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ["subject", "sender", "recipient", "is_read", "is_urgent", "sent_at", "has_attachments"]
    list_filter = ["is_read", "is_urgent", "sent_at"]
    search_fields = ["subject", "content", "sender__username", "recipient__username"]
    readonly_fields = ["sent_at", "read_at", "thread_id"]
    date_hierarchy = "sent_at"
    inlines = [MessageAttachmentInline]
    
    def has_attachments(self, obj):
        return obj.attachments.exists()
    has_attachments.boolean = True
    has_attachments.short_description = "Has Attachments"


@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ["original_filename", "message", "file_size_display", "content_type", "uploaded_at", "download_count"]
    list_filter = ["content_type", "uploaded_at"]
    search_fields = ["original_filename", "message__subject"]
    readonly_fields = ["file_size", "content_type", "uploaded_at", "download_count", "last_downloaded_at"]
    
    def file_size_display(self, obj):
        return obj.get_file_size_display()
    file_size_display.short_description = "File Size"
