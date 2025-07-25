from django.contrib import admin
from .models import (
    AcademicProgress, ClassAverage, StudyRecommendation, 
    AchievementBadge, StudentBadge, AcademicGoal, GoalProgress,
    ParentEngagement, EngagementSummary
)


@admin.register(AcademicProgress)
class AcademicProgressAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'grade_value', 'period', 'year', 'recorded_date']
    list_filter = ['period', 'year', 'subject', 'recorded_date']
    search_fields = ['student__first_name', 'student__last_name', 'subject']
    ordering = ['-year', '-recorded_date']


@admin.register(ClassAverage)
class ClassAverageAdmin(admin.ModelAdmin):
    list_display = ['subject', 'grade_level', 'period', 'year', 'class_average', 'grade_level_average']
    list_filter = ['period', 'year', 'grade_level', 'subject']
    ordering = ['-year', 'grade_level', 'subject']


@admin.register(StudyRecommendation)
class StudyRecommendationAdmin(admin.ModelAdmin):
    list_display = ['student', 'title', 'subject', 'recommendation_type', 'priority', 'is_active', 'parent_acknowledged']
    list_filter = ['recommendation_type', 'priority', 'is_active', 'parent_acknowledged', 'created_date']
    search_fields = ['student__first_name', 'student__last_name', 'title', 'subject']
    ordering = ['-created_date']


@admin.register(AchievementBadge)
class AchievementBadgeAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'points', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'description']


@admin.register(StudentBadge)
class StudentBadgeAdmin(admin.ModelAdmin):
    list_display = ['student', 'badge', 'earned_date', 'shared_with_family']
    list_filter = ['badge__category', 'earned_date', 'shared_with_family']
    search_fields = ['student__first_name', 'student__last_name', 'badge__name']
    ordering = ['-earned_date']


@admin.register(AcademicGoal)
class AcademicGoalAdmin(admin.ModelAdmin):
    list_display = ['student', 'title', 'goal_type', 'target_value', 'current_value', 'status', 'target_date']
    list_filter = ['goal_type', 'status', 'target_date', 'created_date']
    search_fields = ['student__first_name', 'student__last_name', 'title']
    ordering = ['-created_date']


@admin.register(GoalProgress)
class GoalProgressAdmin(admin.ModelAdmin):
    list_display = ['goal', 'recorded_value', 'recorded_date', 'recorded_by']
    list_filter = ['recorded_date']
    search_fields = ['goal__title', 'goal__student__first_name', 'goal__student__last_name']
    ordering = ['-recorded_date']


@admin.register(ParentEngagement)
class ParentEngagementAdmin(admin.ModelAdmin):
    list_display = ['parent', 'student', 'activity_type', 'timestamp']
    list_filter = ['activity_type', 'timestamp']
    search_fields = ['parent__username', 'student__first_name', 'student__last_name']
    ordering = ['-timestamp']


@admin.register(EngagementSummary)
class EngagementSummaryAdmin(admin.ModelAdmin):
    list_display = ['parent', 'student', 'period_start', 'period_end', 'engagement_score', 'total_logins']
    list_filter = ['period_start', 'engagement_score']
    search_fields = ['parent__username', 'student__first_name', 'student__last_name']
    ordering = ['-period_start']
