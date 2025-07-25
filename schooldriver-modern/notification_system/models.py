from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import json
from datetime import datetime, timedelta


class NotificationPreference(models.Model):
    """User notification preferences"""
    FREQUENCY_CHOICES = [
        ('immediate', 'Immediate'),
        ('daily', 'Daily Digest'),
        ('weekly', 'Weekly Summary'),
        ('disabled', 'Disabled'),
    ]
    
    DELIVERY_CHOICES = [
        ('email', 'Email Only'),
        ('sms', 'SMS Only'),
        ('push', 'Push Notification Only'),
        ('email_sms', 'Email + SMS'),
        ('email_push', 'Email + Push'),
        ('sms_push', 'SMS + Push'),
        ('all', 'All Methods'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_prefs')
    
    # Grade-related notifications
    grade_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='immediate')
    grade_delivery = models.CharField(max_length=20, choices=DELIVERY_CHOICES, default='email_push')
    
    # Attendance notifications
    attendance_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='immediate')
    attendance_delivery = models.CharField(max_length=20, choices=DELIVERY_CHOICES, default='email_sms')
    
    # Assignment notifications
    assignment_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='daily')
    assignment_delivery = models.CharField(max_length=20, choices=DELIVERY_CHOICES, default='email')
    
    # Emergency notifications
    emergency_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='immediate')
    emergency_delivery = models.CharField(max_length=20, choices=DELIVERY_CHOICES, default='all')
    
    # Announcement notifications
    announcement_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='daily')
    announcement_delivery = models.CharField(max_length=20, choices=DELIVERY_CHOICES, default='email')
    
    # Message notifications
    message_frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES, default='immediate')
    message_delivery = models.CharField(max_length=20, choices=DELIVERY_CHOICES, default='email_push')
    
    # Phone number for SMS
    phone_number = models.CharField(max_length=20, blank=True, null=True, help_text="Format: +1234567890")
    
    # Push notification settings
    push_token = models.TextField(blank=True, null=True, help_text="Device push notification token")
    
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Notification preferences for {self.user.username}"


class NotificationTemplate(models.Model):
    """Reusable notification templates"""
    CATEGORY_CHOICES = [
        ('grade', 'Grade Related'),
        ('attendance', 'Attendance'),
        ('assignment', 'Assignment'),
        ('emergency', 'Emergency'),
        ('announcement', 'Announcement'),
        ('message', 'Message'),
        ('reminder', 'Reminder'),
        ('conference', 'Conference'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    
    # Email template
    email_subject = models.CharField(max_length=200)
    email_body = models.TextField()
    email_html_body = models.TextField(blank=True, null=True)
    
    # SMS template
    sms_body = models.TextField(max_length=160, help_text="Keep under 160 characters")
    
    # Push notification template
    push_title = models.CharField(max_length=100)
    push_body = models.CharField(max_length=200)
    
    # Template variables (JSON)
    variables = models.JSONField(default=list, help_text="List of variables used in templates")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.category})"


class Notification(models.Model):
    """Individual notification record"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
        ('read', 'Read'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('emergency', 'Emergency'),
    ]
    
    DELIVERY_METHOD_CHOICES = [
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('push', 'Push Notification'),
        ('in_app', 'In-App Notification'),
    ]
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications', null=True, blank=True)
    
    title = models.CharField(max_length=200)
    message = models.TextField()
    category = models.CharField(max_length=20, choices=NotificationTemplate.CATEGORY_CHOICES)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    
    # Delivery tracking
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Metadata
    metadata = models.JSONField(default=dict, help_text="Additional data for the notification")
    
    # Related objects (optional)
    related_student = models.ForeignKey('students.Student', on_delete=models.CASCADE, null=True, blank=True)
    related_object_type = models.CharField(max_length=50, blank=True, null=True)
    related_object_id = models.PositiveIntegerField(blank=True, null=True)
    
    # Timing
    created_at = models.DateTimeField(default=timezone.now)
    scheduled_for = models.DateTimeField(null=True, blank=True, help_text="Schedule for future delivery")
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Expiration
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'status']),
            models.Index(fields=['category', 'priority']),
            models.Index(fields=['created_at']),
            models.Index(fields=['scheduled_for']),
        ]
    
    def __str__(self):
        return f"{self.title} to {self.recipient.username} via {self.delivery_method}"
    
    @property
    def is_expired(self):
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    def mark_as_read(self):
        """Mark notification as read"""
        if self.status != 'read':
            self.status = 'read'
            self.read_at = timezone.now()
            self.save(update_fields=['status', 'read_at'])


class NotificationBatch(models.Model):
    """Batch sending of notifications"""
    name = models.CharField(max_length=200)
    template = models.ForeignKey(NotificationTemplate, on_delete=models.CASCADE)
    
    # Recipients
    recipient_query = models.TextField(help_text="JSON representation of recipient query")
    estimated_recipients = models.PositiveIntegerField(default=0)
    actual_recipients = models.PositiveIntegerField(default=0)
    
    # Batch status
    status = models.CharField(max_length=20, choices=[
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='draft')
    
    # Timing
    created_at = models.DateTimeField(default=timezone.now)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Results
    sent_count = models.PositiveIntegerField(default=0)
    delivered_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"Batch: {self.name} ({self.status})"


class NotificationLog(models.Model):
    """Log of notification sending attempts"""
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='logs')
    
    action = models.CharField(max_length=50)  # 'sent', 'delivered', 'failed', 'bounced', etc.
    details = models.TextField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    
    # External service response
    external_id = models.CharField(max_length=200, blank=True, null=True)
    external_response = models.JSONField(default=dict)
    
    timestamp = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.action} - {self.notification.title}"


class ConferenceSchedule(models.Model):
    """Parent-teacher conference scheduling"""
    STATUS_CHOICES = [
        ('available', 'Available'),
        ('booked', 'Booked'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
    ]
    
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conference_slots')
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conference_bookings', null=True, blank=True)
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='conferences', null=True, blank=True)
    
    # Scheduling
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(default=30)
    
    # Conference details
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='available')
    location = models.CharField(max_length=200, blank=True, null=True)
    virtual_meeting_link = models.URLField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    
    # Cancellation/rescheduling
    cancellation_reason = models.TextField(blank=True, null=True)
    rescheduled_from = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)
    
    # Timing
    created_at = models.DateTimeField(default=timezone.now)
    booked_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    # Notifications
    confirmation_sent = models.BooleanField(default=False)
    reminder_sent = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['date', 'start_time']
        unique_together = ['teacher', 'date', 'start_time']
    
    def __str__(self):
        return f"Conference: {self.teacher.get_full_name()} - {self.date} {self.start_time}"
    
    @property
    def is_upcoming(self):
        conference_datetime = datetime.combine(self.date, self.start_time)
        return conference_datetime > datetime.now()
    
    def can_be_rescheduled(self):
        """Check if conference can be rescheduled (at least 24 hours notice)"""
        if self.status not in ['booked']:
            return False
        
        conference_datetime = datetime.combine(self.date, self.start_time)
        notice_required = timedelta(hours=24)
        
        return (conference_datetime - datetime.now()) > notice_required
    
    def reschedule_to(self, new_slot):
        """Reschedule conference to a new slot"""
        if not self.can_be_rescheduled():
            raise ValueError("Conference cannot be rescheduled (insufficient notice)")
        
        if new_slot.status != 'available':
            raise ValueError("New slot is not available")
        
        # Mark current slot as rescheduled
        self.status = 'rescheduled'
        self.save()
        
        # Update new slot
        new_slot.parent = self.parent
        new_slot.student = self.student
        new_slot.status = 'booked'
        new_slot.booked_at = timezone.now()
        new_slot.rescheduled_from = self
        new_slot.notes = self.notes
        new_slot.save()
        
        return new_slot
