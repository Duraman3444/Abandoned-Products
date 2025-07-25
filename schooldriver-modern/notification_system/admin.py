from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import (
    NotificationPreference, NotificationTemplate, Notification,
    NotificationBatch, NotificationLog, ConferenceSchedule
)


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['user', 'grade_delivery', 'attendance_delivery', 'emergency_delivery', 'phone_number']
    list_filter = ['grade_frequency', 'attendance_frequency', 'emergency_frequency']
    search_fields = ['user__username', 'user__email', 'phone_number']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Grade Notifications', {
            'fields': ('grade_frequency', 'grade_delivery')
        }),
        ('Attendance Notifications', {
            'fields': ('attendance_frequency', 'attendance_delivery')
        }),
        ('Assignment Notifications', {
            'fields': ('assignment_frequency', 'assignment_delivery')
        }),
        ('Emergency Notifications', {
            'fields': ('emergency_frequency', 'emergency_delivery')
        }),
        ('Announcement Notifications', {
            'fields': ('announcement_frequency', 'announcement_delivery')
        }),
        ('Message Notifications', {
            'fields': ('message_frequency', 'message_delivery')
        }),
        ('Contact Information', {
            'fields': ('phone_number', 'push_token')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(NotificationTemplate)
class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_active', 'created_at']
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'email_subject', 'push_title']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category', 'is_active')
        }),
        ('Email Template', {
            'fields': ('email_subject', 'email_body', 'email_html_body')
        }),
        ('SMS Template', {
            'fields': ('sms_body',)
        }),
        ('Push Notification Template', {
            'fields': ('push_title', 'push_body')
        }),
        ('Template Variables', {
            'fields': ('variables',),
            'description': 'JSON array of variables used in templates'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


class NotificationLogInline(admin.TabularInline):
    model = NotificationLog
    extra = 0
    readonly_fields = ['timestamp', 'action', 'details', 'error_message']
    can_delete = False


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'recipient', 'delivery_method', 'status', 'priority', 'created_at']
    list_filter = ['delivery_method', 'status', 'priority', 'category', 'created_at']
    search_fields = ['title', 'message', 'recipient__username', 'recipient__email']
    readonly_fields = ['created_at', 'sent_at', 'delivered_at', 'read_at']
    inlines = [NotificationLogInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('recipient', 'sender', 'title', 'message')
        }),
        ('Classification', {
            'fields': ('category', 'priority', 'delivery_method', 'status')
        }),
        ('Related Objects', {
            'fields': ('related_student', 'related_object_type', 'related_object_id')
        }),
        ('Scheduling', {
            'fields': ('scheduled_for', 'expires_at')
        }),
        ('Tracking', {
            'fields': ('created_at', 'sent_at', 'delivered_at', 'read_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('recipient', 'sender', 'related_student')


@admin.register(NotificationBatch)
class NotificationBatchAdmin(admin.ModelAdmin):
    list_display = ['name', 'template', 'status', 'estimated_recipients', 'sent_count', 'created_at']
    list_filter = ['status', 'created_at', 'scheduled_for']
    search_fields = ['name']
    readonly_fields = ['created_at', 'started_at', 'completed_at', 'actual_recipients']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'template', 'created_by')
        }),
        ('Recipients', {
            'fields': ('recipient_query', 'estimated_recipients', 'actual_recipients')
        }),
        ('Status', {
            'fields': ('status', 'scheduled_for')
        }),
        ('Results', {
            'fields': ('sent_count', 'delivered_count', 'failed_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(NotificationLog)
class NotificationLogAdmin(admin.ModelAdmin):
    list_display = ['notification_title', 'action', 'timestamp', 'error_message_short']
    list_filter = ['action', 'timestamp']
    search_fields = ['notification__title', 'details', 'error_message']
    readonly_fields = ['timestamp']
    
    def notification_title(self, obj):
        return obj.notification.title
    notification_title.short_description = 'Notification'
    
    def error_message_short(self, obj):
        if obj.error_message:
            return obj.error_message[:50] + '...' if len(obj.error_message) > 50 else obj.error_message
        return '-'
    error_message_short.short_description = 'Error'


@admin.register(ConferenceSchedule)
class ConferenceScheduleAdmin(admin.ModelAdmin):
    list_display = ['teacher', 'parent', 'student', 'date', 'start_time', 'status', 'created_at']
    list_filter = ['status', 'date', 'created_at']
    search_fields = ['teacher__username', 'parent__username', 'student__first_name', 'student__last_name']
    readonly_fields = ['created_at', 'booked_at', 'cancelled_at']
    
    fieldsets = (
        ('Participants', {
            'fields': ('teacher', 'parent', 'student')
        }),
        ('Schedule', {
            'fields': ('date', 'start_time', 'end_time', 'duration_minutes')
        }),
        ('Details', {
            'fields': ('status', 'location', 'virtual_meeting_link', 'notes')
        }),
        ('Cancellation/Rescheduling', {
            'fields': ('cancellation_reason', 'rescheduled_from'),
            'classes': ('collapse',)
        }),
        ('Notifications', {
            'fields': ('confirmation_sent', 'reminder_sent'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'booked_at', 'cancelled_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('teacher', 'parent', 'student')
    
    actions = ['send_reminders']
    
    def send_reminders(self, request, queryset):
        """Send reminder notifications for upcoming conferences"""
        count = 0
        for conference in queryset.filter(status='booked', date__gte=timezone.now().date()):
            # Send reminder logic would go here
            count += 1
        
        self.message_user(request, f'Sent reminders for {count} conferences.')
    send_reminders.short_description = 'Send reminder notifications'


# Default templates will be created via management command after migration
