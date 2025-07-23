"""
Analytics and reporting models
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import json


class ReportTemplate(models.Model):
    """Custom report templates"""
    
    REPORT_TYPES = [
        ('CLASS_PERFORMANCE', 'Class Performance'),
        ('STUDENT_PROGRESS', 'Student Progress'),
        ('ATTENDANCE_TRENDS', 'Attendance Trends'),
        ('GRADE_DISTRIBUTION', 'Grade Distribution'),
        ('CUSTOM', 'Custom Report'),
    ]
    
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    description = models.TextField(blank=True)
    
    # Report configuration stored as JSON
    filters = models.JSONField(default=dict, help_text="Report filters and parameters")
    columns = models.JSONField(default=list, help_text="Columns to include in report")
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    is_active = models.BooleanField(default=True)
    is_shared = models.BooleanField(default=False, help_text="Share with other teachers")
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['-created_at']


class ReportExecution(models.Model):
    """Track report executions"""
    
    template = models.ForeignKey(ReportTemplate, on_delete=models.CASCADE, related_name='executions')
    executed_by = models.ForeignKey(User, on_delete=models.CASCADE)
    executed_at = models.DateTimeField(auto_now_add=True)
    
    # Parameters used for this execution
    parameters = models.JSONField(default=dict)
    
    # Results metadata
    row_count = models.IntegerField(default=0)
    execution_time_ms = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.template.name} - {self.executed_at.strftime('%Y-%m-%d %H:%M')}"
    
    class Meta:
        ordering = ['-executed_at']


class StudentAnalytics(models.Model):
    """Cached analytics data for students"""
    
    student = models.OneToOneField('students.Student', on_delete=models.CASCADE, related_name='analytics')
    
    # Academic performance metrics
    current_gpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    semester_gpa = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)
    
    # Attendance metrics
    attendance_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)  # Percentage
    total_absences = models.IntegerField(default=0)
    unexcused_absences = models.IntegerField(default=0)
    
    # Assignment metrics
    assignments_completed = models.IntegerField(default=0)
    assignments_missing = models.IntegerField(default=0)
    average_assignment_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Behavioral metrics
    progress_notes_count = models.IntegerField(default=0)
    positive_notes_count = models.IntegerField(default=0)
    concerning_notes_count = models.IntegerField(default=0)
    
    # Trends (stored as JSON for flexibility)
    grade_trend = models.JSONField(default=list, help_text="Grade trend over time")
    attendance_trend = models.JSONField(default=list, help_text="Attendance trend over time")
    
    # Meta information
    last_updated = models.DateTimeField(auto_now=True)
    data_current_as_of = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Analytics for {self.student.get_full_name()}"
    
    class Meta:
        verbose_name = "Student Analytics"
        verbose_name_plural = "Student Analytics"


class ClassAnalytics(models.Model):
    """Cached analytics data for classes/courses"""
    
    course = models.OneToOneField('academics.Course', on_delete=models.CASCADE, related_name='analytics')
    
    # Performance metrics
    class_average_grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    highest_grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    lowest_grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Grade distribution
    grade_distribution = models.JSONField(default=dict, help_text="Grade range distribution")
    
    # Attendance metrics
    average_attendance_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Assignment metrics
    total_assignments = models.IntegerField(default=0)
    average_completion_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Student performance categories
    students_excelling = models.IntegerField(default=0)  # Above 90%
    students_proficient = models.IntegerField(default=0)  # 80-90%
    students_developing = models.IntegerField(default=0)  # 70-80%
    students_struggling = models.IntegerField(default=0)  # Below 70%
    
    # Trends
    performance_trend = models.JSONField(default=list, help_text="Class performance over time")
    
    # Meta information
    last_updated = models.DateTimeField(auto_now=True)
    data_current_as_of = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"Analytics for {self.course.course_name}"
    
    class Meta:
        verbose_name = "Class Analytics"
        verbose_name_plural = "Class Analytics"


class AlertRule(models.Model):
    """Rules for automated alerts"""
    
    ALERT_TYPES = [
        ('FAILING_GRADE', 'Failing Grade'),
        ('EXCESSIVE_ABSENCES', 'Excessive Absences'),
        ('MISSING_ASSIGNMENTS', 'Missing Assignments'),
        ('GRADE_DROP', 'Significant Grade Drop'),
        ('ATTENDANCE_DROP', 'Attendance Drop'),
    ]
    
    SEVERITY_LEVELS = [
        ('LOW', 'Low Priority'),
        ('MEDIUM', 'Medium Priority'),
        ('HIGH', 'High Priority'),
        ('CRITICAL', 'Critical'),
    ]
    
    name = models.CharField(max_length=200)
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='MEDIUM')
    
    # Rule conditions (stored as JSON)
    conditions = models.JSONField(default=dict, help_text="Alert trigger conditions")
    
    # Notification settings
    notify_teachers = models.BooleanField(default=True)
    notify_parents = models.BooleanField(default=False)
    notify_admin = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class Alert(models.Model):
    """Individual alert instances"""
    
    rule = models.ForeignKey(AlertRule, on_delete=models.CASCADE, related_name='alerts')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='alerts')
    
    # Alert details
    message = models.TextField()
    severity = models.CharField(max_length=10, choices=AlertRule.SEVERITY_LEVELS)
    
    # Context data (stored as JSON)
    context_data = models.JSONField(default=dict, help_text="Relevant data that triggered alert")
    
    # Status tracking
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='resolved_alerts')
    resolution_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.rule.name} - {self.student.get_full_name()}"
    
    class Meta:
        ordering = ['-created_at']
