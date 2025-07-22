from django.contrib import admin
from .models import (
    Department, Course, CourseSection, Enrollment, AssignmentCategory,
    Assignment, Grade, Schedule, Attendance, Announcement, Message
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'head', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name']


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['course_code', 'name', 'department', 'credit_hours', 'is_active']
    list_filter = ['department', 'is_active', 'credit_hours']
    search_fields = ['course_code', 'name']
    filter_horizontal = ['prerequisites']


class ScheduleInline(admin.TabularInline):
    model = Schedule
    extra = 1


class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 0
    readonly_fields = ['enrollment_date']


@admin.register(CourseSection)
class CourseSectionAdmin(admin.ModelAdmin):
    list_display = ['course', 'section_name', 'teacher', 'school_year', 'room', 'is_active']
    list_filter = ['school_year', 'course__department', 'is_active']
    search_fields = ['course__course_code', 'course__name', 'teacher__username']
    inlines = [ScheduleInline, EnrollmentInline]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'section', 'final_grade', 'final_percentage', 'is_active']
    list_filter = ['section__school_year', 'section__course__department', 'is_active', 'final_grade']
    search_fields = ['student__first_name', 'student__last_name', 'section__course__course_code']
    readonly_fields = ['enrollment_date']


@admin.register(AssignmentCategory)
class AssignmentCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'default_weight', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']


class GradeInline(admin.TabularInline):
    model = Grade
    extra = 0
    readonly_fields = ['percentage', 'created_at']


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'section', 'category', 'due_date', 'max_points', 'is_published']
    list_filter = ['section__school_year', 'category', 'is_published', 'due_date']
    search_fields = ['name', 'section__course__course_code']
    date_hierarchy = 'due_date'
    inlines = [GradeInline]


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'assignment', 'points_earned', 'percentage', 'letter_grade', 'is_excused']
    list_filter = [
        'assignment__section__school_year', 
        'assignment__category', 
        'letter_grade', 
        'is_excused', 
        'is_late'
    ]
    search_fields = [
        'enrollment__student__first_name', 
        'enrollment__student__last_name',
        'assignment__name'
    ]
    readonly_fields = ['percentage', 'created_at']


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ['section', 'day_of_week', 'start_time', 'end_time', 'room', 'is_active']
    list_filter = ['day_of_week', 'is_active', 'section__school_year']
    search_fields = ['section__course__course_code', 'room']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'date', 'status', 'recorded_by', 'recorded_at']
    list_filter = ['status', 'date', 'enrollment__section__school_year']
    search_fields = [
        'enrollment__student__first_name', 
        'enrollment__student__last_name',
        'enrollment__section__course__course_code'
    ]
    date_hierarchy = 'date'


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'audience', 'is_published', 'is_urgent', 'publish_date', 'created_by']
    list_filter = ['audience', 'is_published', 'is_urgent', 'publish_date']
    search_fields = ['title', 'content']
    date_hierarchy = 'publish_date'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['subject', 'sender', 'recipient', 'is_read', 'is_urgent', 'sent_at']
    list_filter = ['is_read', 'is_urgent', 'sent_at']
    search_fields = ['subject', 'sender__username', 'recipient__username']
    date_hierarchy = 'sent_at'
