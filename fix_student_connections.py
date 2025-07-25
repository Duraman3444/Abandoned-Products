#!/usr/bin/env python3
"""Fix student data connections for proper portal display."""

import os
import sys
import django
from datetime import date, datetime, timedelta

# Add the Django app directory to the Python path
sys.path.append('/Users/abdurrahmanmirza/Gauntlet Projects/Schooldriver-ModernVersion/schooldriver-modern')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schooldriver_modern.settings')
django.setup()

from django.contrib.auth.models import User
from students.models import Student, SchoolYear
from academics.models import Enrollment, CourseSection, Assignment, Grade, Schedule, Attendance, Course, Department, AssignmentCategory
from django.contrib.auth.models import User as Teacher
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    print("🔧 FIXING STUDENT CONNECTIONS")
    print("=" * 50)
    
    # Get current school year
    current_year = SchoolYear.objects.filter(is_active=True).first()
    if not current_year:
        print("❌ No active school year found!")
        return
    
    print(f"📅 Current school year: {current_year.name}")
    
    # Find the student1 user
    try:
        student_user = User.objects.get(username='student1')
        print(f"👤 Found user: {student_user.username} ({student_user.first_name} {student_user.last_name})")
    except User.DoesNotExist:
        print("❌ Student1 user not found!")
        return
    
    # Find Emma Smith student record
    emma_students = Student.objects.filter(first_name='Emma', last_name='Smith')
    print(f"👩‍🎓 Found {emma_students.count()} Emma Smith student records:")
    
    for i, student in enumerate(emma_students):
        print(f"  {i+1}. ID: {student.student_id}, Email: {student.primary_contact_email}")
        
        # Check enrollments for this student
        enrollments = Enrollment.objects.filter(
            student=student,
            section__school_year=current_year,
            is_active=True
        )
        print(f"     Enrollments: {enrollments.count()}")
        for enrollment in enrollments:
            print(f"       - {enrollment.section.course.name} with {enrollment.section.teacher.first_name} {enrollment.section.teacher.last_name}")
    
    # Let's consolidate to one Emma Smith record and ensure it has proper courses
    if emma_students.count() > 1:
        print("\n🔄 Consolidating Emma Smith records...")
        
        # Keep the one with Lisa Garcia's course (STU-EMMA-001)
        main_student = emma_students.filter(student_id='STU-EMMA-001').first()
        if not main_student:
            main_student = emma_students.first()
        
        print(f"✅ Using student: {main_student.student_id}")
        
        # Remove other Emma Smith records
        for student in emma_students:
            if student.id != main_student.id:
                print(f"🗑️ Removing duplicate student: {student.student_id}")
                student.delete()
    else:
        main_student = emma_students.first()
    
    if not main_student:
        print("❌ No Emma Smith student found!")
        return
    
    # Update student email to match user
    main_student.primary_contact_email = student_user.email
    main_student.save()
    print(f"📧 Updated student email to: {student_user.email}")
    
    # Find Lisa Garcia teacher
    lisa_garcia = User.objects.filter(username='lisa.garcia').first()
    if not lisa_garcia:
        print("❌ Lisa Garcia teacher not found!")
        return
    
    lisa_teacher = lisa_garcia  # Use the User object directly since teachers are Users
    
    print(f"👩‍🏫 Found teacher: {lisa_garcia.first_name} {lisa_garcia.last_name}")
    
    # Ensure Emma is enrolled in multiple courses with Lisa Garcia
    courses_to_create = [
        ('English Literature', 'ENG101', 3.0),
        ('Advanced Writing', 'ENG102', 3.0),
        ('Creative Writing', 'ENG201', 2.0),
        ('World Literature', 'ENG301', 3.0),
    ]
    
    # Get or create department
    dept, created = Department.objects.get_or_create(
        name='English',
        defaults={'description': 'English and Literature Department'}
    )
    if created:
        print("📚 Created English Department")
    
    for course_name, course_code, credit_hours in courses_to_create:
        # Get or create course
        course, created = Course.objects.get_or_create(
            course_code=course_code,
            defaults={
                'name': course_name,
                'credit_hours': credit_hours,
                'description': f'{course_name} course taught by Lisa Garcia',
                'department': dept
            }
        )
        if created:
            print(f"📚 Created course: {course_name}")
        
        # Get or create section
        section, created = CourseSection.objects.get_or_create(
            course=course,
            teacher=lisa_teacher,
            school_year=current_year,
            section_name='A',
            defaults={
                'room': f'Room {200 + hash(course_code) % 50}',
                'max_students': 25,
                'is_active': True
            }
        )
        if created:
            print(f"🏫 Created section: {course_name} - {section.section_name}")
        
        # Enroll Emma in this section
        enrollment, created = Enrollment.objects.get_or_create(
            student=main_student,
            section=section,
            defaults={'is_active': True}
        )
        if created:
            print(f"✅ Enrolled Emma in: {course_name}")
        
        # Create schedule for this course
        days = ['MON', 'WED', 'FRI'] if 'Literature' in course_name else ['TUE', 'THU']
        start_hour = 9 + (hash(course_code) % 4)  # 9-12 AM
        
        for day in days:
            schedule, created = Schedule.objects.get_or_create(
                section=section,
                day_of_week=day,
                defaults={
                    'start_time': f'{start_hour:02d}:00:00',
                    'end_time': f'{start_hour+1:02d}:00:00',
                    'room': section.room,
                    'is_active': True
                }
            )
            if created:
                print(f"📅 Created schedule: {course_name} on {day} at {start_hour}:00")
        
        # Get or create assignment categories
        homework_cat, created = AssignmentCategory.objects.get_or_create(
            name='Homework',
            defaults={'description': 'Regular homework assignments', 'default_weight': 0.3}
        )
        test_cat, created = AssignmentCategory.objects.get_or_create(
            name='Test',
            defaults={'description': 'Major tests and exams', 'default_weight': 0.4}
        )
        project_cat, created = AssignmentCategory.objects.get_or_create(
            name='Project',
            defaults={'description': 'Major projects and papers', 'default_weight': 0.3}
        )
        
        # Create assignments for this course
        assignments_to_create = [
            ('Essay 1: Character Analysis', 100, date.today() + timedelta(days=7), homework_cat),
            ('Midterm Exam', 150, date.today() + timedelta(days=21), test_cat),
            ('Research Paper', 200, date.today() + timedelta(days=35), project_cat),
            ('Final Project', 250, date.today() + timedelta(days=49), project_cat),
        ]
        
        for assignment_name, max_points, due_date, category in assignments_to_create:
            assignment, created = Assignment.objects.get_or_create(
                section=section,
                name=assignment_name,
                defaults={
                    'description': f'{assignment_name} for {course_name}',
                    'max_points': max_points,
                    'due_date': due_date,
                    'assigned_date': date.today(),
                    'category': category,
                    'is_published': True
                }
            )
            if created:
                print(f"📝 Created assignment: {assignment_name}")
                
                # Create a grade for this assignment
                grade, created = Grade.objects.get_or_create(
                    enrollment=enrollment,
                    assignment=assignment,
                    defaults={
                        'points_earned': max_points * 0.85,  # 85% grade
                        'percentage': 85.0,
                        'comments': 'Good work!'
                    }
                )
                if created:
                    print(f"✅ Created grade: {grade.percentage}% for {assignment_name}")
        
        # Create attendance records
        start_date = current_year.start_date or date.today() - timedelta(days=60)
        current_date = start_date
        
        while current_date <= date.today():
            if current_date.weekday() in [0, 2, 4]:  # Mon, Wed, Fri for some courses
                if days[0] in ['MON', 'WED', 'FRI'] and current_date.strftime('%a').upper() in ['MON', 'WED', 'FRI']:
                    attendance, created = Attendance.objects.get_or_create(
                        enrollment=enrollment,
                        date_taken=current_date,
                        defaults={
                            'status': 'P' if current_date.day % 10 != 0 else 'A',  # Mostly present
                            'notes': 'Regular attendance'
                        }
                    )
            elif current_date.weekday() in [1, 3]:  # Tue, Thu for other courses
                if days[0] in ['TUE', 'THU'] and current_date.strftime('%a').upper() in ['TUE', 'THU']:
                    attendance, created = Attendance.objects.get_or_create(
                        enrollment=enrollment,
                        date_taken=current_date,
                        defaults={
                            'status': 'P' if current_date.day % 15 != 0 else 'T',  # Mostly present, occasional tardy
                            'notes': 'Regular attendance'
                        }
                    )
            current_date += timedelta(days=1)
    
    print("\n✅ STUDENT CONNECTIONS FIXED!")
    print("=" * 50)
    
    # Verify the fix
    final_enrollments = Enrollment.objects.filter(
        student=main_student,
        section__school_year=current_year,
        is_active=True
    )
    
    print(f"👩‍🎓 Emma Smith ({main_student.student_id}) is now enrolled in {final_enrollments.count()} courses:")
    for enrollment in final_enrollments:
        assignments = Assignment.objects.filter(section=enrollment.section).count()
        grades = Grade.objects.filter(enrollment=enrollment).count()
        attendance = Attendance.objects.filter(enrollment=enrollment).count()
        
        print(f"  📚 {enrollment.section.course.name}")
        print(f"      Teacher: {enrollment.section.teacher.first_name} {enrollment.section.teacher.last_name}")
        print(f"      Assignments: {assignments}, Grades: {grades}, Attendance: {attendance}")

if __name__ == '__main__':
    main()
