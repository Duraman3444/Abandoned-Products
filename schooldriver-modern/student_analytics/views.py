from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Avg, Q, Count
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
import json

from students.models import Student
from .models import (
    AcademicProgress, ClassAverage, StudyRecommendation, 
    AchievementBadge, StudentBadge, AcademicGoal, GoalProgress,
    ParentEngagement, EngagementSummary
)


def track_engagement(user, student, activity_type, activity_data=None):
    """Helper function to track parent engagement"""
    if activity_data is None:
        activity_data = {}
    
    ParentEngagement.objects.create(
        parent=user,
        student=student,
        activity_type=activity_type,
        activity_data=activity_data
    )


@login_required
def analytics_dashboard(request, student_id):
    """Main analytics dashboard view"""
    student = get_object_or_404(Student, id=student_id)
    
    # Track engagement
    track_engagement(request.user, student, 'analytics_view')
    
    # Get recent progress data
    recent_progress = AcademicProgress.objects.filter(
        student=student
    ).order_by('-recorded_date')[:10]
    
    # Get active goals
    active_goals = AcademicGoal.objects.filter(
        student=student,
        status='active'
    ).order_by('-created_date')
    
    # Get recent badges
    recent_badges = StudentBadge.objects.filter(
        student=student
    ).order_by('-earned_date')[:5]
    
    # Get study recommendations
    recommendations = StudyRecommendation.objects.filter(
        student=student,
        is_active=True
    ).order_by('-priority', '-created_date')[:5]
    
    context = {
        'student': student,
        'recent_progress': recent_progress,
        'active_goals': active_goals,
        'recent_badges': recent_badges,
        'recommendations': recommendations,
    }
    
    return render(request, 'student_analytics/minimal_test.html', context)


@login_required
def progress_over_time(request, student_id):
    """Academic progress over time view with charts"""
    student = get_object_or_404(Student, id=student_id)
    
    # Track engagement
    track_engagement(request.user, student, 'analytics_view', {'section': 'progress'})
    
    # Get progress data for the last 2 years
    two_years_ago = timezone.now().year - 2
    progress_data = AcademicProgress.objects.filter(
        student=student,
        year__gte=two_years_ago
    ).order_by('year', 'subject')
    
    # Organize data by subject for charting
    subjects = {}
    for progress in progress_data:
        if progress.subject not in subjects:
            subjects[progress.subject] = []
        subjects[progress.subject].append({
            'period': f"{progress.period} {progress.year}",
            'grade': progress.grade_value,
            'date': progress.recorded_date.isoformat()
        })
    
    # Calculate trends
    trends = {}
    for subject, data in subjects.items():
        if len(data) >= 2:
            recent_avg = sum(d['grade'] for d in data[-3:]) / min(3, len(data))
            older_avg = sum(d['grade'] for d in data[:3]) / min(3, len(data))
            trends[subject] = {
                'direction': 'improving' if recent_avg > older_avg else 'declining' if recent_avg < older_avg else 'stable',
                'change': round(recent_avg - older_avg, 2)
            }
    
    context = {
        'student': student,
        'subjects_data': json.dumps(subjects),
        'trends': trends,
        'progress_data': progress_data,
    }
    
    return render(request, 'student_analytics/progress_over_time.html', context)


@login_required
def class_comparisons(request, student_id):
    """View for comparing student performance with class averages"""
    student = get_object_or_404(Student, id=student_id)
    
    # Track engagement
    track_engagement(request.user, student, 'analytics_view', {'section': 'comparisons'})
    
    current_year = timezone.now().year
    current_period = "Q2"  # This would be calculated based on current date
    
    # Get student's current grades
    student_grades = AcademicProgress.objects.filter(
        student=student,
        year=current_year,
        period=current_period
    )
    
    # Get class averages
    comparisons = []
    for grade in student_grades:
        try:
            class_avg = ClassAverage.objects.get(
                subject=grade.subject,
                grade_level=student.grade_level,
                period=grade.period,
                year=grade.year
            )
            
            comparison = {
                'subject': grade.subject,
                'student_grade': grade.grade_value,
                'class_average': class_avg.class_average,
                'grade_level_average': class_avg.grade_level_average,
                'performance': 'above' if grade.grade_value > class_avg.class_average else 'below' if grade.grade_value < class_avg.class_average else 'at',
                'difference': round(grade.grade_value - class_avg.class_average, 2)
            }
            comparisons.append(comparison)
        except ClassAverage.DoesNotExist:
            continue
    
    context = {
        'student': student,
        'comparisons': comparisons,
        'current_period': current_period,
        'current_year': current_year,
    }
    
    return render(request, 'student_analytics/class_comparisons.html', context)


@login_required
def study_recommendations_view(request, student_id):
    """View for study habit recommendations"""
    student = get_object_or_404(Student, id=student_id)
    
    # Track engagement
    track_engagement(request.user, student, 'analytics_view', {'section': 'recommendations'})
    
    recommendations = StudyRecommendation.objects.filter(
        student=student,
        is_active=True
    ).order_by('-priority', '-created_date')
    
    context = {
        'student': student,
        'recommendations': recommendations,
    }
    
    return render(request, 'student_analytics/study_recommendations.html', context)


@login_required
@require_http_methods(["POST"])
def acknowledge_recommendation(request, recommendation_id):
    """Mark a recommendation as acknowledged by parent"""
    recommendation = get_object_or_404(StudyRecommendation, id=recommendation_id)
    recommendation.parent_acknowledged = True
    recommendation.save()
    
    messages.success(request, "Recommendation acknowledged!")
    return redirect('student_analytics:study_recommendations', student_id=recommendation.student.id)


@login_required
def achievement_badges_view(request, student_id):
    """View for achievement badges and recognition"""
    student = get_object_or_404(Student, id=student_id)
    
    # Track engagement
    track_engagement(request.user, student, 'badge_view')
    
    # Get earned badges
    earned_badges = StudentBadge.objects.filter(
        student=student
    ).select_related('badge').order_by('-earned_date')
    
    # Get available badges (not yet earned)
    earned_badge_ids = earned_badges.values_list('badge_id', flat=True)
    available_badges = AchievementBadge.objects.filter(
        is_active=True
    ).exclude(id__in=earned_badge_ids)
    
    # Calculate badge statistics
    total_points = sum(badge.badge.points for badge in earned_badges)
    categories = {}
    for badge in earned_badges:
        category = badge.badge.category
        if category not in categories:
            categories[category] = {'count': 0, 'points': 0}
        categories[category]['count'] += 1
        categories[category]['points'] += badge.badge.points
    
    context = {
        'student': student,
        'earned_badges': earned_badges,
        'available_badges': available_badges,
        'total_points': total_points,
        'categories': categories,
    }
    
    return render(request, 'student_analytics/achievement_badges.html', context)


@login_required
@require_http_methods(["POST"])
def share_badge(request, badge_id):
    """Share a badge with family"""
    student_badge = get_object_or_404(StudentBadge, id=badge_id)
    student_badge.shared_with_family = True
    student_badge.save()
    
    messages.success(request, f"Badge '{student_badge.badge.name}' shared with family!")
    return redirect('student_analytics:achievement_badges', student_id=student_badge.student.id)


@login_required
def goal_tracking_view(request, student_id):
    """View for goal setting and tracking"""
    student = get_object_or_404(Student, id=student_id)
    
    # Track engagement
    track_engagement(request.user, student, 'analytics_view', {'section': 'goals'})
    
    goals = AcademicGoal.objects.filter(
        student=student
    ).order_by('-created_date')
    
    context = {
        'student': student,
        'goals': goals,
    }
    
    return render(request, 'student_analytics/goal_tracking.html', context)


@login_required
def create_goal(request, student_id):
    """Create a new academic goal"""
    student = get_object_or_404(Student, id=student_id)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        goal_type = request.POST.get('goal_type')
        target_value = float(request.POST.get('target_value'))
        target_date = request.POST.get('target_date')
        
        goal = AcademicGoal.objects.create(
            student=student,
            title=title,
            description=description,
            goal_type=goal_type,
            target_value=target_value,
            target_date=target_date,
            created_by=request.user
        )
        
        # Track engagement
        track_engagement(request.user, student, 'goal_set', {'goal_id': goal.id})
        
        messages.success(request, f"Goal '{title}' created successfully!")
        return redirect('student_analytics:goal_tracking', student_id=student.id)
    
    context = {
        'student': student,
        'goal_types': AcademicGoal._meta.get_field('goal_type').choices,
    }
    
    return render(request, 'student_analytics/create_goal.html', context)


@login_required
def update_goal_progress(request, goal_id):
    """Update progress on a goal"""
    goal = get_object_or_404(AcademicGoal, id=goal_id)
    
    if request.method == 'POST':
        recorded_value = float(request.POST.get('recorded_value'))
        notes = request.POST.get('notes', '')
        
        # Create progress record
        GoalProgress.objects.create(
            goal=goal,
            recorded_value=recorded_value,
            notes=notes,
            recorded_by=request.user
        )
        
        # Update current value on goal
        goal.current_value = recorded_value
        
        # Check if goal is achieved
        if recorded_value >= goal.target_value:
            goal.status = 'achieved'
            messages.success(request, f"Congratulations! Goal '{goal.title}' has been achieved!")
        
        goal.save()
        
        messages.success(request, "Goal progress updated!")
        return redirect('student_analytics:goal_tracking', student_id=goal.student.id)
    
    context = {
        'goal': goal,
    }
    
    return render(request, 'student_analytics/update_goal_progress.html', context)


@login_required
def engagement_metrics_view(request, student_id):
    """View for parent engagement metrics"""
    student = get_object_or_404(Student, id=student_id)
    
    # Track engagement
    track_engagement(request.user, student, 'analytics_view', {'section': 'engagement'})
    
    # Get recent engagement data
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_engagement = ParentEngagement.objects.filter(
        parent=request.user,
        student=student,
        timestamp__gte=thirty_days_ago
    ).order_by('-timestamp')
    
    # Calculate engagement statistics
    total_logins = recent_engagement.filter(activity_type='login').count()
    grade_checks = recent_engagement.filter(activity_type='grade_view').count()
    messages_read = recent_engagement.filter(activity_type='message_read').count()
    
    # Get weekly summaries
    summaries = EngagementSummary.objects.filter(
        parent=request.user,
        student=student
    ).order_by('-period_start')[:4]  # Last 4 weeks
    
    # Activity distribution
    activity_counts = {}
    for engagement in recent_engagement:
        activity_type = engagement.activity_type
        activity_counts[activity_type] = activity_counts.get(activity_type, 0) + 1
    
    context = {
        'student': student,
        'recent_engagement': recent_engagement[:20],  # Show last 20 activities
        'total_logins': total_logins,
        'grade_checks': grade_checks,
        'messages_read': messages_read,
        'summaries': summaries,
        'activity_counts': json.dumps(activity_counts),
    }
    
    return render(request, 'student_analytics/engagement_metrics.html', context)


@login_required
def progress_api(request, student_id):
    """API endpoint for progress chart data"""
    student = get_object_or_404(Student, id=student_id)
    
    subject = request.GET.get('subject', 'all')
    period = request.GET.get('period', 'all')
    
    progress_query = AcademicProgress.objects.filter(student=student)
    
    if subject != 'all':
        progress_query = progress_query.filter(subject=subject)
    
    if period != 'all':
        progress_query = progress_query.filter(period=period)
    
    progress_data = progress_query.order_by('year', 'recorded_date').values(
        'subject', 'grade_value', 'period', 'year', 'recorded_date'
    )
    
    # Convert to list for JSON serialization
    data = []
    for item in progress_data:
        data.append({
            'subject': item['subject'],
            'grade': item['grade_value'],
            'period': item['period'],
            'year': item['year'],
            'date': item['recorded_date'].isoformat()
        })
    
    return JsonResponse({'data': data})
