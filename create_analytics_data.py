#!/usr/bin/env python3
"""
Create sample analytics data for testing the analytics features
"""

import os
import sys
import django
from datetime import datetime, timedelta, date
from random import choice, randint, uniform

# Setup Django
sys.path.append('./schooldriver-modern')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schooldriver_modern.settings')
django.setup()

from django.contrib.auth.models import User
from students.models import Student
from student_analytics.models import (
    AcademicProgress, ClassAverage, StudyRecommendation,
    AchievementBadge, StudentBadge, AcademicGoal, GoalProgress,
    ParentEngagement, EngagementSummary
)


def create_sample_analytics_data():
    print("Creating sample analytics data...")
    
    # Get or create sample students
    students = list(Student.objects.all()[:5])
    if not students:
        print("No students found. Creating sample students...")
        # Create sample students if none exist
        for i in range(5):
            student = Student.objects.create(
                first_name=f"Student{i+1}",
                last_name="Doe",
                grade_level=randint(9, 12),
                student_id=f"STU{1000+i}",
                email=f"student{i+1}@example.com"
            )
            students.append(student)
    
    # Get or create users for parent engagement
    users = list(User.objects.filter(is_staff=False)[:3])
    if not users:
        print("Creating sample parent users...")
        for i in range(3):
            user = User.objects.create_user(
                username=f"parent{i+1}",
                email=f"parent{i+1}@example.com",
                password="password123",
                first_name=f"Parent{i+1}",
                last_name="Smith"
            )
            users.append(user)
    
    subjects = ["Mathematics", "English", "Science", "History", "Physical Education", "Art"]
    periods = ["Q1", "Q2", "Q3", "Q4"]
    years = [2023, 2024]
    
    # Create Academic Progress data
    print("Creating academic progress data...")
    for student in students:
        for year in years:
            for period in periods:
                for subject in subjects:
                    # Simulate grade trends (some improving, some declining)
                    base_grade = uniform(70, 95)
                    if period == "Q1":
                        grade = base_grade
                    elif period == "Q2":
                        grade = base_grade + uniform(-5, 5)
                    elif period == "Q3":
                        grade = base_grade + uniform(-3, 7)
                    else:  # Q4
                        grade = base_grade + uniform(-2, 8)
                    
                    AcademicProgress.objects.get_or_create(
                        student=student,
                        subject=subject,
                        period=period,
                        year=year,
                        defaults={
                            'grade_value': max(0, min(100, grade)),
                            'recorded_date': datetime(year, 3 + (periods.index(period) * 3), 15)
                        }
                    )
    
    # Create Class Averages
    print("Creating class average data...")
    for year in years:
        for period in periods:
            for subject in subjects:
                for grade_level in range(9, 13):
                    ClassAverage.objects.get_or_create(
                        subject=subject,
                        grade_level=grade_level,
                        period=period,
                        year=year,
                        defaults={
                            'class_average': uniform(75, 85),
                            'grade_level_average': uniform(70, 80),
                            'school_average': uniform(72, 82)
                        }
                    )
    
    # Create Achievement Badges
    print("Creating achievement badges...")
    badges_data = [
        {"name": "Honor Roll", "category": "academic", "icon": "🏆", "points": 50,
         "description": "Achieved honor roll status", "criteria": {"gpa": 3.5}},
        {"name": "Perfect Attendance", "category": "behavior", "icon": "📅", "points": 30,
         "description": "Perfect attendance for a quarter", "criteria": {"attendance": 100}},
        {"name": "Math Wizard", "category": "academic", "icon": "🧮", "points": 40,
         "description": "Excellence in mathematics", "criteria": {"subject": "Mathematics", "grade": 90}},
        {"name": "Creative Writer", "category": "academic", "icon": "✍️", "points": 35,
         "description": "Outstanding writing skills", "criteria": {"subject": "English", "grade": 85}},
        {"name": "Science Explorer", "category": "academic", "icon": "🔬", "points": 40,
         "description": "Excellence in science", "criteria": {"subject": "Science", "grade": 88}},
        {"name": "Team Player", "category": "participation", "icon": "🤝", "points": 25,
         "description": "Great teamwork and collaboration", "criteria": {"participation": True}},
        {"name": "Improvement Star", "category": "improvement", "icon": "⭐", "points": 30,
         "description": "Significant academic improvement", "criteria": {"improvement": 10}},
        {"name": "Leadership", "category": "leadership", "icon": "👑", "points": 45,
         "description": "Demonstrated leadership qualities", "criteria": {"leadership": True}},
    ]
    
    for badge_data in badges_data:
        AchievementBadge.objects.get_or_create(
            name=badge_data["name"],
            defaults=badge_data
        )
    
    # Assign some badges to students
    print("Assigning badges to students...")
    badges = list(AchievementBadge.objects.all())
    for student in students:
        # Each student gets 2-4 random badges
        student_badges = choice(badges[:randint(2, 4)])
        for i, badge in enumerate(badges[:randint(2, 4)]):
            StudentBadge.objects.get_or_create(
                student=student,
                badge=badge,
                defaults={
                    'earned_date': datetime.now() - timedelta(days=randint(1, 90)),
                    'notes': f"Earned for excellent performance in {badge.category}",
                    'shared_with_family': choice([True, False])
                }
            )
    
    # Create Study Recommendations
    print("Creating study recommendations...")
    recommendation_templates = [
        {
            "title": "Focus on Algebra Fundamentals",
            "subject": "Mathematics",
            "recommendation_type": "improvement",
            "description": "Review algebra basics to strengthen foundation for advanced topics.",
            "resources": ["Khan Academy Algebra", "Practice worksheets", "Tutoring sessions"],
            "priority": "high"
        },
        {
            "title": "Expand Reading Comprehension",
            "subject": "English",
            "recommendation_type": "improvement",
            "description": "Practice reading complex texts to improve comprehension skills.",
            "resources": ["Classic literature list", "Reading comprehension exercises"],
            "priority": "medium"
        },
        {
            "title": "Laboratory Skills Practice",
            "subject": "Science",
            "recommendation_type": "strength",
            "description": "Continue developing excellent laboratory techniques.",
            "resources": ["Advanced lab experiments", "Science fair projects"],
            "priority": "low"
        },
        {
            "title": "Essay Writing Techniques",
            "subject": "History",
            "recommendation_type": "strategy",
            "description": "Learn structured essay writing for better historical analysis.",
            "resources": ["Writing guide", "Historical essay examples"],
            "priority": "medium"
        }
    ]
    
    for student in students[:3]:  # Give recommendations to first 3 students
        for template in recommendation_templates[:randint(1, 3)]:
            StudyRecommendation.objects.get_or_create(
                student=student,
                title=template["title"],
                defaults=template
            )
    
    # Create Academic Goals
    print("Creating academic goals...")
    goal_templates = [
        {
            "title": "Improve Math Grade to B+",
            "description": "Work towards achieving a B+ grade in mathematics this semester",
            "goal_type": "grade",
            "target_value": 87.0,
            "target_date": date.today() + timedelta(days=60)
        },
        {
            "title": "Maintain 3.5 GPA",
            "description": "Maintain a GPA of 3.5 or higher throughout the year",
            "goal_type": "gpa",
            "target_value": 3.5,
            "target_date": date.today() + timedelta(days=120)
        },
        {
            "title": "Perfect Attendance",
            "description": "Achieve perfect attendance for the semester",
            "goal_type": "attendance",
            "target_value": 100.0,
            "target_date": date.today() + timedelta(days=90)
        }
    ]
    
    for student in students:
        for template in goal_templates[:randint(1, 2)]:
            goal, created = AcademicGoal.objects.get_or_create(
                student=student,
                title=template["title"],
                defaults={
                    **template,
                    'current_value': uniform(60, 85),
                    'created_by': users[0] if users else User.objects.first(),
                    'status': choice(['active', 'active', 'achieved'])
                }
            )
            
            # Create some progress records for each goal
            if created:
                for i in range(randint(1, 3)):
                    GoalProgress.objects.create(
                        goal=goal,
                        recorded_value=uniform(goal.current_value - 5, goal.target_value + 2),
                        recorded_date=datetime.now() - timedelta(days=randint(1, 30)),
                        recorded_by=users[0] if users else User.objects.first(),
                        notes=f"Progress update #{i+1}"
                    )
    
    # Create Parent Engagement data
    print("Creating parent engagement data...")
    activity_types = ['login', 'grade_view', 'message_read', 'document_view', 'goal_set', 'badge_view']
    
    for user in users:
        for student in students[:2]:  # Each parent engages with 2 students
            # Create engagement records for the last 30 days
            for day in range(30):
                date_offset = datetime.now() - timedelta(days=day)
                # Random engagement activities
                for _ in range(randint(0, 3)):
                    ParentEngagement.objects.create(
                        parent=user,
                        student=student,
                        activity_type=choice(activity_types),
                        timestamp=date_offset - timedelta(hours=randint(0, 23)),
                        activity_data={'session_id': f"session_{randint(1000, 9999)}"}
                    )
    
    # Create Engagement Summaries
    print("Creating engagement summaries...")
    for user in users:
        for student in students[:2]:
            for week in range(4):  # Last 4 weeks
                start_date = date.today() - timedelta(weeks=week+1)
                end_date = start_date + timedelta(days=6)
                
                EngagementSummary.objects.get_or_create(
                    parent=user,
                    student=student,
                    period_start=start_date,
                    period_end=end_date,
                    defaults={
                        'total_logins': randint(3, 10),
                        'total_time_spent': timedelta(hours=randint(1, 5)),
                        'grade_checks': randint(2, 8),
                        'messages_read': randint(1, 5),
                        'documents_viewed': randint(0, 3),
                        'engagement_score': uniform(60, 95)
                    }
                )
    
    print("Sample analytics data created successfully!")
    print(f"Created data for {len(students)} students")
    print(f"Academic Progress records: {AcademicProgress.objects.count()}")
    print(f"Class Averages: {ClassAverage.objects.count()}")
    print(f"Achievement Badges: {AchievementBadge.objects.count()}")
    print(f"Student Badges: {StudentBadge.objects.count()}")
    print(f"Study Recommendations: {StudyRecommendation.objects.count()}")
    print(f"Academic Goals: {AcademicGoal.objects.count()}")
    print(f"Parent Engagement records: {ParentEngagement.objects.count()}")
    print(f"Engagement Summaries: {EngagementSummary.objects.count()}")


if __name__ == "__main__":
    create_sample_analytics_data()
