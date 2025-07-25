#!/usr/bin/env python3
"""Create comprehensive mock data for all student portal features."""

import os
import sys
import django
from datetime import date, datetime, timedelta
from decimal import Decimal

# Add the Django app directory to the Python path
sys.path.append('/Users/abdurrahmanmirza/Gauntlet Projects/Schooldriver-ModernVersion/schooldriver-modern')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schooldriver_modern.settings')
django.setup()

from django.contrib.auth.models import User
from students.models import Student, SchoolYear
from academics.models import (
    Enrollment, CourseSection, Assignment, Grade, Schedule, Attendance, 
    Course, Department, AssignmentCategory
)
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_comprehensive_data():
    """Create comprehensive mock data for student portal testing."""
    
    print("🎭 CREATING COMPREHENSIVE MOCK DATA")
    print("=" * 50)
    
    # Get current school year
    current_year = SchoolYear.objects.filter(is_active=True).first()
    if not current_year:
        print("❌ No active school year found!")
        return
    
    # Get Emma Smith and Lisa Garcia
    emma_student = Student.objects.filter(student_id='STU-EMMA-001').first()
    if not emma_student:
        print("❌ Emma Smith student not found!")
        return
    
    lisa_user = User.objects.filter(username='lisa.garcia').first()
    if not lisa_user:
        print("❌ Lisa Garcia user not found!")
        return
    
    print(f"👩‍🎓 Working with student: {emma_student.first_name} {emma_student.last_name}")
    print(f"👩‍🏫 Working with teacher: {lisa_user.first_name} {lisa_user.last_name}")
    
    # Get all current enrollments
    enrollments = Enrollment.objects.filter(
        student=emma_student,
        section__school_year=current_year,
        is_active=True
    )
    
    print(f"📚 Found {enrollments.count()} enrollments")
    
    # Create more detailed attendance records
    print("\n📋 Creating comprehensive attendance records...")
    start_date = current_year.start_date or (date.today() - timedelta(days=90))
    current_date = start_date
    total_created = 0
    
    for enrollment in enrollments:
        # Get the schedule for this enrollment to know which days to create attendance
        schedules = Schedule.objects.filter(section=enrollment.section, is_active=True)
        
        for schedule in schedules:
            # Map day names to weekday numbers
            day_mapping = {
                'MON': 0, 'TUE': 1, 'WED': 2, 'THU': 3, 'FRI': 4,
                'SAT': 5, 'SUN': 6
            }
            
            target_weekday = day_mapping.get(schedule.day_of_week)
            if target_weekday is None:
                continue
            
            # Create attendance for each occurrence of this day
            check_date = start_date
            while check_date <= date.today():
                if check_date.weekday() == target_weekday:
                    # Create attendance record if it doesn't exist
                    attendance, created = Attendance.objects.get_or_create(
                        enrollment=enrollment,
                        date_taken=check_date,
                        defaults={
                            'status': 'P' if check_date.day % 10 != 0 else ('A' if check_date.day % 20 == 0 else 'T'),
                            'notes': f'Auto-generated for {enrollment.section.course.name}'
                        }
                    )
                    if created:
                        total_created += 1
                
                check_date += timedelta(days=1)
    
    print(f"✅ Created {total_created} attendance records")
    
    # Update grades with more realistic data
    print("\n📊 Updating grades with realistic data...")
    all_grades = Grade.objects.filter(enrollment__student=emma_student)
    grade_updates = 0
    
    for grade in all_grades:
        # Create more varied grades
        assignment_name = grade.assignment.name.lower()
        if 'essay' in assignment_name:
            base_score = 85 + (hash(assignment_name) % 10)  # 85-94
        elif 'exam' in assignment_name or 'midterm' in assignment_name:
            base_score = 80 + (hash(assignment_name) % 15)  # 80-94
        elif 'project' in assignment_name:
            base_score = 88 + (hash(assignment_name) % 8)   # 88-95
        else:
            base_score = 82 + (hash(assignment_name) % 12)  # 82-93
        
        # Add some randomness based on course difficulty
        course_name = grade.assignment.section.course.name.lower()
        if 'advanced' in course_name or 'literature' in course_name:
            base_score = max(75, base_score - 5)  # Slightly harder
        
        grade.points_earned = Decimal(str(min(float(grade.assignment.max_points), 
                                       (base_score / 100) * float(grade.assignment.max_points))))
        grade.percentage = Decimal(str(base_score))
        grade.comments = f"Good work on {grade.assignment.name}"
        grade.save()
        grade_updates += 1
    
    print(f"✅ Updated {grade_updates} grades with realistic scores")
    
    # Create additional assignments with due dates spread out
    print("\n📝 Creating additional assignments...")
    assignment_count = 0
    
    for enrollment in enrollments:
        course = enrollment.section.course
        
        # Create different types of assignments based on course
        if 'literature' in course.name.lower() or 'english' in course.name.lower():
            additional_assignments = [
                ('Weekly Reading Quiz', 50, 'Test', 7),
                ('Poetry Analysis', 75, 'Homework', 14),
                ('Class Participation', 25, 'Homework', -3),  # Past due
                ('Book Report Draft', 100, 'Project', 21),
                ('Vocabulary Test', 40, 'Test', 28),
            ]
        elif 'writing' in course.name.lower():
            additional_assignments = [
                ('Grammar Exercise', 30, 'Homework', 5),
                ('Narrative Essay', 150, 'Project', 18),
                ('Peer Review Session', 20, 'Homework', -1),  # Past due
                ('Research Proposal', 80, 'Project', 25),
            ]
        else:
            additional_assignments = [
                ('Discussion Post', 25, 'Homework', 10),
                ('Critical Analysis', 100, 'Project', 20),
                ('Final Presentation', 200, 'Project', 35),
            ]
        
        for assign_name, max_points, category_name, days_offset in additional_assignments:
            # Get or create category
            category, _ = AssignmentCategory.objects.get_or_create(
                name=category_name,
                defaults={'description': f'{category_name} assignments', 'default_weight': 1.0}
            )
            
            due_date = date.today() + timedelta(days=days_offset)
            assigned_date = due_date - timedelta(days=7)  # Assigned a week before
            
            assignment, created = Assignment.objects.get_or_create(
                section=enrollment.section,
                name=f"{assign_name} - {course.name}",
                defaults={
                    'description': f'{assign_name} for {course.name} course',
                    'max_points': max_points,
                    'due_date': due_date,
                    'assigned_date': assigned_date,
                    'category': category,
                    'is_published': True
                }
            )
            
            if created:
                assignment_count += 1
                
                # Create grade if assignment is in the past
                if due_date <= date.today():
                    base_score = 85 + (hash(assign_name) % 10)
                    grade = Grade.objects.create(
                        enrollment=enrollment,
                        assignment=assignment,
                        points_earned=Decimal(str((base_score / 100) * max_points)),
                        percentage=Decimal(str(base_score)),
                        comments=f"Completed {assign_name}"
                    )
    
    print(f"✅ Created {assignment_count} additional assignments")
    
    # Create announcements
    print("\n📢 Creating school announcements...")
    from academics.models import Announcement
    
    announcements_data = [
        ("Early Dismissal Notice", "School will dismiss early on Wednesday due to professional development.", "ALL", 1),
        ("Science Fair Registration", "The annual science fair is coming up! Students interested in participating should register by Friday.", "STUDENTS", 0),
        ("Parent-Teacher Conferences", "Parent-teacher conferences are scheduled for next week. Please check your email for your assigned time slot.", "PARENTS", 2),
        ("Library Hours Extended", "The library will now be open until 6 PM on weekdays to provide more study time for students.", "STUDENTS", -1),
        ("Winter Break Reminder", "Don't forget that winter break begins December 20th. Have a wonderful holiday season!", "ALL", 5),
    ]
    
    announcement_count = 0
    for title, content, audience, days_offset in announcements_data:
        publish_date = date.today() + timedelta(days=days_offset)
        
        announcement, created = Announcement.objects.get_or_create(
            title=title,
            defaults={
                'content': content,
                'audience': audience,
                'publish_date': datetime.combine(publish_date, datetime.min.time()),
                'is_published': True,
                'created_by': lisa_user
            }
        )
        if created:
            announcement_count += 1
    
    print(f"✅ Created {announcement_count} announcements")
    
    # Verify the final state
    print("\n🔍 VERIFYING FINAL DATA STATE")
    print("=" * 50)
    
    # Check enrollments
    final_enrollments = Enrollment.objects.filter(
        student=emma_student,
        section__school_year=current_year,
        is_active=True
    )
    print(f"📚 Enrollments: {final_enrollments.count()}")
    
    # Check assignments
    all_assignments = Assignment.objects.filter(
        section__enrollments__student=emma_student,
        section__school_year=current_year
    ).distinct()
    print(f"📝 Total assignments: {all_assignments.count()}")
    
    # Check grades
    all_grades = Grade.objects.filter(
        enrollment__student=emma_student
    )
    print(f"📊 Total grades: {all_grades.count()}")
    
    # Check attendance
    all_attendance = Attendance.objects.filter(
        enrollment__student=emma_student
    )
    print(f"📋 Total attendance records: {all_attendance.count()}")
    
    # Calculate GPA
    total_points = 0
    total_possible = 0
    for grade in all_grades:
        total_points += float(grade.points_earned or 0)
        total_possible += float(grade.assignment.max_points)
    
    if total_possible > 0:
        gpa_percentage = (total_points / total_possible) * 100
        print(f"📊 Current GPA: {gpa_percentage:.1f}%")
    
    print("\n✅ COMPREHENSIVE MOCK DATA CREATION COMPLETED!")
    return True

if __name__ == '__main__':
    create_comprehensive_data()
