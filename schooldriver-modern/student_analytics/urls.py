from django.urls import path
from . import views

app_name = 'student_analytics'

urlpatterns = [
    # Main analytics dashboard
    path('student/<uuid:student_id>/', views.analytics_dashboard, name='dashboard'),
    
    # Academic progress tracking
    path('student/<uuid:student_id>/progress/', views.progress_over_time, name='progress_over_time'),
    path('student/<uuid:student_id>/comparisons/', views.class_comparisons, name='class_comparisons'),
    
    # Study recommendations
    path('student/<uuid:student_id>/recommendations/', views.study_recommendations_view, name='study_recommendations'),
    path('recommendation/<int:recommendation_id>/acknowledge/', views.acknowledge_recommendation, name='acknowledge_recommendation'),
    
    # Achievement badges
    path('student/<uuid:student_id>/badges/', views.achievement_badges_view, name='achievement_badges'),
    path('badge/<int:badge_id>/share/', views.share_badge, name='share_badge'),
    
    # Goal tracking
    path('student/<uuid:student_id>/goals/', views.goal_tracking_view, name='goal_tracking'),
    path('student/<uuid:student_id>/goals/create/', views.create_goal, name='create_goal'),
    path('goal/<int:goal_id>/update/', views.update_goal_progress, name='update_goal_progress'),
    
    # Engagement metrics
    path('student/<uuid:student_id>/engagement/', views.engagement_metrics_view, name='engagement_metrics'),
    
    # API endpoints
    path('api/student/<uuid:student_id>/progress/', views.progress_api, name='progress_api'),
]
