from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime, timedelta
import json


class AcademicProgress(models.Model):
    """Track student academic progress over time"""
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='progress_records')
    subject = models.CharField(max_length=100)
    grade_value = models.FloatField()
    period = models.CharField(max_length=50)  # Quarter, Semester, Year
    year = models.IntegerField()
    recorded_date = models.DateTimeField(default=timezone.now)
    
    class Meta:
        unique_together = ['student', 'subject', 'period', 'year']
        ordering = ['-year', '-recorded_date']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.subject} ({self.period} {self.year}): {self.grade_value}"


class ClassAverage(models.Model):
    """Store class and grade level averages for comparison"""
    subject = models.CharField(max_length=100)
    grade_level = models.IntegerField()
    period = models.CharField(max_length=50)
    year = models.IntegerField()
    class_average = models.FloatField()
    grade_level_average = models.FloatField()
    school_average = models.FloatField(null=True, blank=True)
    
    class Meta:
        unique_together = ['subject', 'grade_level', 'period', 'year']
    
    def __str__(self):
        return f"Grade {self.grade_level} {self.subject} ({self.period} {self.year}): {self.class_average}"


class StudyRecommendation(models.Model):
    """AI-generated study recommendations for students"""
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='study_recommendations')
    subject = models.CharField(max_length=100)
    recommendation_type = models.CharField(max_length=50, choices=[
        ('improvement', 'Improvement Area'),
        ('strength', 'Strength Building'),
        ('resource', 'Resource Recommendation'),
        ('strategy', 'Study Strategy'),
    ])
    title = models.CharField(max_length=200)
    description = models.TextField()
    resources = models.JSONField(default=list)  # List of recommended resources
    priority = models.CharField(max_length=20, choices=[
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ], default='medium')
    created_date = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    parent_acknowledged = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-priority', '-created_date']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.title}"


class AchievementBadge(models.Model):
    """Achievement badges for students"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    icon = models.CharField(max_length=50)  # Icon class or emoji
    category = models.CharField(max_length=50, choices=[
        ('academic', 'Academic'),
        ('behavior', 'Behavior'),
        ('participation', 'Participation'),
        ('improvement', 'Improvement'),
        ('leadership', 'Leadership'),
    ])
    criteria = models.JSONField()  # Criteria for earning the badge
    points = models.IntegerField(default=10)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name


class StudentBadge(models.Model):
    """Badges earned by students"""
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='earned_badges')
    badge = models.ForeignKey(AchievementBadge, on_delete=models.CASCADE)
    earned_date = models.DateTimeField(default=timezone.now)
    notes = models.TextField(blank=True)
    shared_with_family = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ['student', 'badge']
        ordering = ['-earned_date']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.badge.name}"


class AcademicGoal(models.Model):
    """Academic goals set by students/parents"""
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='academic_goals')
    title = models.CharField(max_length=200)
    description = models.TextField()
    goal_type = models.CharField(max_length=50, choices=[
        ('gpa', 'GPA Target'),
        ('grade', 'Grade Improvement'),
        ('subject', 'Subject Mastery'),
        ('behavior', 'Behavior Goal'),
        ('attendance', 'Attendance Goal'),
    ])
    target_value = models.FloatField()
    current_value = models.FloatField(default=0)
    target_date = models.DateField()
    created_date = models.DateTimeField(default=timezone.now)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('achieved', 'Achieved'),
        ('paused', 'Paused'),
        ('cancelled', 'Cancelled'),
    ], default='active')
    is_shared = models.BooleanField(default=True)  # Share with family
    
    class Meta:
        ordering = ['-created_date']
    
    @property
    def progress_percentage(self):
        if self.target_value == 0:
            return 0
        return min(100, (self.current_value / self.target_value) * 100)
    
    def __str__(self):
        return f"{self.student.full_name} - {self.title}"


class GoalProgress(models.Model):
    """Track progress towards academic goals"""
    goal = models.ForeignKey(AcademicGoal, on_delete=models.CASCADE, related_name='progress_records')
    recorded_value = models.FloatField()
    notes = models.TextField(blank=True)
    recorded_date = models.DateTimeField(default=timezone.now)
    recorded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        ordering = ['-recorded_date']
    
    def __str__(self):
        return f"{self.goal.title} - {self.recorded_value} on {self.recorded_date.date()}"


class ParentEngagement(models.Model):
    """Track parent portal engagement metrics"""
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='engagement_metrics')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='parent_engagement')
    activity_type = models.CharField(max_length=50, choices=[
        ('login', 'Portal Login'),
        ('grade_view', 'Grade Check'),
        ('message_read', 'Message Read'),
        ('message_sent', 'Message Sent'),
        ('document_view', 'Document View'),
        ('goal_set', 'Goal Setting'),
        ('badge_view', 'Badge View'),
        ('analytics_view', 'Analytics View'),
    ])
    activity_data = models.JSONField(default=dict)  # Store additional activity details
    timestamp = models.DateTimeField(default=timezone.now)
    session_duration = models.DurationField(null=True, blank=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.parent.username} - {self.activity_type} for {self.student.full_name}"


class EngagementSummary(models.Model):
    """Weekly/monthly engagement summaries"""
    parent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='engagement_summaries')
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE)
    period_start = models.DateField()
    period_end = models.DateField()
    total_logins = models.IntegerField(default=0)
    total_time_spent = models.DurationField(default=timedelta(0))
    grade_checks = models.IntegerField(default=0)
    messages_read = models.IntegerField(default=0)
    documents_viewed = models.IntegerField(default=0)
    engagement_score = models.FloatField(default=0)  # 0-100 engagement score
    
    class Meta:
        unique_together = ['parent', 'student', 'period_start', 'period_end']
        ordering = ['-period_start']
    
    def __str__(self):
        return f"{self.parent.username} engagement for {self.student.full_name} ({self.period_start} - {self.period_end})"
