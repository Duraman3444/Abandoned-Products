#!/usr/bin/env python3

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schooldriver_modern.settings')
sys.path.append('./schooldriver-modern')
django.setup()

from django.contrib.auth.models import User
from schooldriver_modern.roles import get_user_role, assign_role_to_user, UserRoles
from students.models import Student, SchoolYear, GradeLevel
from academics.models import Department, Course, CourseSection, Enrollment, Assignment, Grade, AssignmentCategory
from datetime import date, timedelta

def show_all_connections():
    print('🔍 COMPREHENSIVE ACCOUNT OVERVIEW')
    print('=' * 60)
    
    # Get current school year
    school_year = SchoolYear.objects.filter(is_active=True).first()
    
    print(f'📅 Current School Year: {school_year.name if school_year else "None"}')
    print()
    
    # Show teachers with their classes
    print('👨‍🏫 TEACHERS & THEIR CLASSES:')
    print('-' * 40)
    
    teachers = User.objects.filter(groups__name='Staff').order_by('last_name', 'first_name')
    for teacher in teachers:
        print(f'🎓 {teacher.first_name} {teacher.last_name} ({teacher.username})')
        print(f'   Email: {teacher.email}')
        
        # Find sections taught by this teacher
        sections = CourseSection.objects.filter(teacher=teacher)
        if sections:
            print('   📚 Classes taught:')
            for section in sections:
                enrollments = section.enrollments.filter(is_active=True)
                print(f'      • {section.course.name} ({section.course.course_code}-{section.section_name})')
                print(f'        Students enrolled: {enrollments.count()}')
                if enrollments.count() > 0:
                    student_names = [f"{e.student.first_name} {e.student.last_name}" for e in enrollments[:3]]
                    if enrollments.count() > 3:
                        student_names.append(f"... and {enrollments.count() - 3} more")
                    print(f'        → {", ".join(student_names)}')
        else:
            print('   📚 No classes assigned')
        print()
    
    # Show parents with their children
    print('👨‍👩‍👧‍👦 PARENTS & THEIR CHILDREN:')
    print('-' * 40)
    
    parents = User.objects.filter(groups__name='Parent').order_by('username')[:10]  # Show first 10
    for parent in parents:
        children = parent.accessible_students.all()
        print(f'👤 {parent.first_name} {parent.last_name} ({parent.username})')
        if children:
            print('   👧👦 Children:')
            for child in children:
                print(f'      • {child.first_name} {child.last_name} (ID: {child.student_id})')
                # Show child's classes
                enrollments = child.enrollments.filter(is_active=True)
                if enrollments:
                    print(f'        Classes: {", ".join([f"{e.section.course.course_code} (Teacher: {e.section.teacher.first_name} {e.section.teacher.last_name})" for e in enrollments])}')
        else:
            print('   👧👦 No children linked')
        print()
    
    # Show students with their teachers
    print('🎓 STUDENTS WITH TEACHER CONNECTIONS:')
    print('-' * 40)
    
    students_with_teachers = Student.objects.filter(enrollments__isnull=False).distinct()[:10]
    for student in students_with_teachers:
        print(f'🎓 {student.first_name} {student.last_name} (ID: {student.student_id})')
        
        # Show parents
        parents = student.family_access_users.all()
        if parents:
            print(f'   👨‍👩‍👧‍👦 Parents: {", ".join([f"{p.first_name} {p.last_name} ({p.username})" for p in parents])}')
        
        # Show enrollments
        enrollments = student.enrollments.filter(is_active=True)
        if enrollments:
            print('   📚 Current Classes:')
            for enrollment in enrollments:
                section = enrollment.section
                teacher = section.teacher
                print(f'      • {section.course.name} ({section.course.course_code}-{section.section_name})')
                print(f'        Teacher: {teacher.first_name} {teacher.last_name} ({teacher.username})')
                print(f'        Final Grade: {enrollment.final_grade or "No grade"} ({enrollment.final_percentage or 0}%)')
        print()

def create_lisa_garcia_student_connection():
    print('\n🔗 CREATING LISA.GARCIA ↔ STUDENT1 CONNECTION')
    print('=' * 50)
    
    # Find lisa.garcia
    try:
        lisa = User.objects.get(username='lisa.garcia')
        print(f'✅ Found teacher: {lisa.first_name} {lisa.last_name}')
    except User.DoesNotExist:
        print('❌ lisa.garcia not found')
        return
    
    # Ensure lisa has Staff role
    if get_user_role(lisa) != UserRoles.STAFF:
        assign_role_to_user(lisa, UserRoles.STAFF)
        print('✅ Assigned Staff role to lisa.garcia')
    
    # Find or create student1 user
    student1_user, created = User.objects.get_or_create(
        username='student1',
        defaults={
            'first_name': 'Emma',
            'last_name': 'Smith',
            'email': 'emma.smith@school.edu'
        }
    )
    if created:
        student1_user.set_password('password123')
        student1_user.save()
        print(f'✅ Created user: {student1_user.username}')
    
    # Ensure student1 has Student role
    assign_role_to_user(student1_user, UserRoles.STUDENT)
    
    # Find or create student record
    student1_record, created = Student.objects.get_or_create(
        student_id='STU-EMMA-001',
        defaults={
            'first_name': student1_user.first_name,
            'last_name': student1_user.last_name,
            'enrollment_date': date(2024, 9, 1),
            'date_of_birth': date(2008, 3, 15),
            'is_active': True
        }
    )
    if created:
        print(f'✅ Created student record: {student1_record.first_name} {student1_record.last_name}')
    
    # Get or create grade level
    grade_level, _ = GradeLevel.objects.get_or_create(
        name="10", 
        defaults={'order': 10}
    )
    student1_record.grade_level = grade_level
    student1_record.save()
    
    # Get current school year
    school_year, _ = SchoolYear.objects.get_or_create(
        name="2024-2025",
        defaults={
            'start_date': date(2024, 9, 1),
            'end_date': date(2025, 6, 15),
            'is_active': True
        }
    )
    
    # Create or find department for Lisa
    department, _ = Department.objects.get_or_create(
        name='English',
        defaults={
            'description': 'English Language Arts Department',
            'head': lisa,
            'is_active': True
        }
    )
    
    # Create course for Lisa to teach
    course, _ = Course.objects.get_or_create(
        course_code='ENG101',
        defaults={
            'name': 'English Literature',
            'description': 'Introduction to English Literature',
            'department': department,
            'credit_hours': 1.0,
            'is_active': True
        }
    )
    
    # Create course section taught by Lisa
    section, _ = CourseSection.objects.get_or_create(
        course=course,
        school_year=school_year,
        section_name='A',
        teacher=lisa,
        defaults={
            'room': 'Room 201',
            'max_students': 25,
            'is_active': True
        }
    )
    print(f'✅ Created/found course section: {section}')
    
    # Enroll student1 in Lisa's class
    enrollment, created = Enrollment.objects.get_or_create(
        student=student1_record,
        section=section,
        defaults={
            'is_active': True,
            'final_grade': 'A-',
            'final_percentage': 91.5
        }
    )
    if created:
        print(f'✅ Enrolled {student1_record.first_name} {student1_record.last_name} in {lisa.first_name} {lisa.last_name}\'s class')
    
    # Create a parent for student1
    parent1_user, created = User.objects.get_or_create(
        username='parent1',
        defaults={
            'first_name': 'Michael',
            'last_name': 'Smith',
            'email': 'michael.smith@email.com'
        }
    )
    if created:
        parent1_user.set_password('password123')
        parent1_user.save()
        print(f'✅ Created parent: {parent1_user.username}')
    
    assign_role_to_user(parent1_user, UserRoles.PARENT)
    
    # Link parent to student
    student1_record.family_access_users.add(parent1_user)
    print(f'✅ Linked parent {parent1_user.first_name} {parent1_user.last_name} to student {student1_record.first_name} {student1_record.last_name}')
    
    # Create some assignments and grades
    print('\n📚 Creating Sample Assignments and Grades...')
    
    # Create assignment categories
    category_essay, _ = AssignmentCategory.objects.get_or_create(
        name='Essays',
        defaults={'description': 'Writing assignments', 'default_weight': 0.4}
    )
    category_quiz, _ = AssignmentCategory.objects.get_or_create(
        name='Quizzes',
        defaults={'description': 'Reading comprehension quizzes', 'default_weight': 0.3}
    )
    category_participation, _ = AssignmentCategory.objects.get_or_create(
        name='Participation',
        defaults={'description': 'Class participation and discussion', 'default_weight': 0.3}
    )
    
    today = date.today()
    
    # Create assignments
    assignments = [
        ('Essay 1 - Character Analysis', category_essay, 100.0, today - timedelta(days=14), today - timedelta(days=7), 94.0),
        ('Quiz 3 - Shakespeare', category_quiz, 50.0, today - timedelta(days=7), today - timedelta(days=3), 47.0),
        ('Class Discussion Participation', category_participation, 25.0, today - timedelta(days=30), today - timedelta(days=1), 23.0),
    ]
    
    for assign_name, category, max_points, assigned_date, due_date, student_points in assignments:
        assignment, assign_created = Assignment.objects.get_or_create(
            section=section,
            name=assign_name,
            defaults={
                'category': category,
                'description': f'Assignment: {assign_name}',
                'assigned_date': assigned_date,
                'due_date': due_date,
                'max_points': max_points,
                'weight': 1.0,
                'is_published': True
            }
        )
        
        if assign_created:
            print(f'✅ Created assignment: {assign_name}')
            
        # Create grade for student1
        grade, grade_created = Grade.objects.get_or_create(
            enrollment=enrollment,
            assignment=assignment,
            defaults={
                'points_earned': student_points,
                'percentage': (student_points / max_points) * 100,
                'letter_grade': 'A' if student_points >= max_points * 0.9 else 'B',
                'graded_by': lisa,
                'graded_date': due_date + timedelta(days=2)
            }
        )
        
        if grade_created:
            print(f'✅ Created grade: {student_points}/{max_points} for {assign_name}')

def show_login_summary():
    print('\n🎯 READY-TO-USE LOGIN ACCOUNTS')
    print('=' * 50)
    
    accounts = [
        ('👨‍🏫 TEACHER', 'lisa.garcia', 'password', 'Lisa Garcia', 'http://localhost:8000/teacher/', 'Teaches English Literature with real students'),
        ('👨‍🏫 TEACHER', 'teacher1', 'password123', 'Sarah Johnson', 'http://localhost:8000/teacher/', 'Teaches Algebra II with real students'),
        ('👨‍👩‍👧‍👦 PARENT', 'parent1', 'password123', 'Michael Smith', 'http://localhost:8000/parent/', 'Parent of Emma Smith (student in Lisa\'s class)'),
        ('👨‍👩‍👧‍👦 PARENT', 'parent_test', 'test', 'Test Parent', 'http://localhost:8000/parent/', 'Simple test parent account'),
        ('🎓 STUDENT', 'student1', 'password123', 'Emma Smith', 'http://localhost:8000/student/', 'Student in Lisa Garcia\'s English class'),
        ('🎓 STUDENT', 'student_test', 'test', 'Test Student', 'http://localhost:8000/student/', 'Simple test student account'),
        ('🔧 ADMIN', 'admin', 'admin123', 'System Admin', 'http://localhost:8000/admin/', 'Full system administrator'),
    ]
    
    for role, username, password, name, url, description in accounts:
        print(f'{role}')
        print(f'   Username: {username}')
        print(f'   Password: {password}')
        print(f'   Name: {name}')
        print(f'   URL: {url}')
        print(f'   Description: {description}')
        print()
    
    print('🔗 KEY RELATIONSHIPS:')
    print('   • Lisa Garcia (teacher) ↔ Emma Smith (student) ↔ Michael Smith (parent)')
    print('   • Sarah Johnson (teacher) ↔ Emma Smith & James Davis (students)')
    print('   • All accounts have proper role assignments and real data')

if __name__ == '__main__':
    show_all_connections()
    create_lisa_garcia_student_connection()
    show_login_summary()
