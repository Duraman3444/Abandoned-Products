#!/usr/bin/env python3

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schooldriver_modern.settings')
sys.path.append('./schooldriver-modern')
django.setup()

from django.contrib.auth.models import User
from schooldriver_modern.roles import UserRoles, assign_role_to_user, create_default_groups
from students.models import Student, SchoolYear, GradeLevel
from academics.models import Department, Course, CourseSection, Enrollment, AssignmentCategory, Assignment, Grade
from datetime import date, timedelta

def create_linked_accounts():
    print('👥 Creating Linked Student, Parent, and Teacher Accounts')
    print('=' * 60)
    
    # Create default groups first
    create_default_groups()
    
    # Get or create current school year
    school_year, created = SchoolYear.objects.get_or_create(
        name="2024-2025",
        defaults={
            'start_date': date(2024, 9, 1),
            'end_date': date(2025, 6, 15),
            'is_active': True
        }
    )
    if created:
        print(f'✅ Created school year: {school_year.name}')
    
    # Get or create grade level
    grade_level, created = GradeLevel.objects.get_or_create(
        name="10",
        defaults={'display_name': '10th Grade'}
    )
    if created:
        print(f'✅ Created grade level: {grade_level.display_name}')
    
    # 1. Create Teacher Account
    teacher_user, created = User.objects.get_or_create(
        username='teacher1',
        defaults={
            'email': 'teacher1@school.edu',
            'first_name': 'Sarah',
            'last_name': 'Johnson',
            'is_staff': True
        }
    )
    if created:
        teacher_user.set_password('password123')
        teacher_user.save()
        print(f'✅ Created teacher user: {teacher_user.username}')
    
    assign_role_to_user(teacher_user, UserRoles.STAFF)
    print(f'✅ Assigned Staff role to {teacher_user.username}')
    
    # 2. Create Parent Account
    parent_user, created = User.objects.get_or_create(
        username='parent1',
        defaults={
            'email': 'parent1@email.com',
            'first_name': 'Michael',
            'last_name': 'Smith'
        }
    )
    if created:
        parent_user.set_password('password123')
        parent_user.save()
        print(f'✅ Created parent user: {parent_user.username}')
    
    assign_role_to_user(parent_user, UserRoles.PARENT)
    print(f'✅ Assigned Parent role to {parent_user.username}')
    
    # 3. Create Student Account
    student_user, created = User.objects.get_or_create(
        username='student1',
        defaults={
            'email': 'student1@school.edu',
            'first_name': 'Emma',
            'last_name': 'Smith'
        }
    )
    if created:
        student_user.set_password('password123')
        student_user.save()
        print(f'✅ Created student user: {student_user.username}')
    
    assign_role_to_user(student_user, UserRoles.STUDENT)
    print(f'✅ Assigned Student role to {student_user.username}')
    
    # 4. Create Student Record
    student, created = Student.objects.get_or_create(
        student_id='STU001',
        defaults={
            'first_name': student_user.first_name,
            'last_name': student_user.last_name,
            'grade_level': grade_level,
            'date_of_birth': date(2008, 5, 15),
            'enrollment_date': date(2024, 9, 1),
            'is_active': True
        }
    )
    if created:
        print(f'✅ Created student record: {student.first_name} {student.last_name}')
    
    # 5. Link Parent to Student
    student.family_access_users.add(parent_user)
    print(f'✅ Linked parent {parent_user.username} to student {student.first_name} {student.last_name}')
    
    # 6. Create Department and Course
    department, created = Department.objects.get_or_create(
        name='Mathematics',
        defaults={
            'description': 'Mathematics Department',
            'head': teacher_user,
            'is_active': True
        }
    )
    if created:
        print(f'✅ Created department: {department.name}')
    
    course, created = Course.objects.get_or_create(
        course_code='MATH101',
        defaults={
            'name': 'Algebra II',
            'description': 'Advanced Algebra course',
            'department': department,
            'credit_hours': 1.0,
            'is_active': True
        }
    )
    if created:
        print(f'✅ Created course: {course.name}')
    
    # 7. Create Course Section taught by teacher
    section, created = CourseSection.objects.get_or_create(
        course=course,
        school_year=school_year,
        section_name='A',
        defaults={
            'teacher': teacher_user,
            'room': 'Room 101',
            'max_students': 25,
            'is_active': True
        }
    )
    if created:
        print(f'✅ Created course section: {section}')
    
    # 8. Enroll Student in Course
    enrollment, created = Enrollment.objects.get_or_create(
        student=student,
        section=section,
        defaults={
            'is_active': True,
            'final_grade': 'A',
            'final_percentage': 92.5
        }
    )
    if created:
        print(f'✅ Enrolled {student.first_name} {student.last_name} in {section}')
    
    # Create some sample assignments and grades to make the connections meaningful
    print('\n📚 Creating Sample Assignments and Grades...')
    
    # Create assignment categories
    category_test, _ = AssignmentCategory.objects.get_or_create(
        name='Tests',
        defaults={'description': 'Major tests and exams', 'default_weight': 0.4}
    )
    category_quiz, _ = AssignmentCategory.objects.get_or_create(
        name='Quizzes', 
        defaults={'description': 'Weekly quizzes', 'default_weight': 0.3}
    )
    category_homework, _ = AssignmentCategory.objects.get_or_create(
        name='Homework',
        defaults={'description': 'Daily homework assignments', 'default_weight': 0.3}
    )
    
    # Create sample assignments
    today = date.today()
    
    # Test assignment
    test_assignment, test_created = Assignment.objects.get_or_create(
        section=section,
        name='Unit 1 Test - Linear Equations',
        defaults={
            'category': category_test,
            'description': 'Test covering linear equations and graphing',
            'assigned_date': today - timedelta(days=10),
            'due_date': today - timedelta(days=3),
            'max_points': 100.0,
            'weight': 1.0,
            'is_published': True
        }
    )
    
    # Quiz assignment  
    quiz_assignment, quiz_created = Assignment.objects.get_or_create(
        section=section,
        name='Quiz 2 - Slope-Intercept Form',
        defaults={
            'category': category_quiz,
            'description': 'Quiz on slope-intercept form equations',
            'assigned_date': today - timedelta(days=5),
            'due_date': today - timedelta(days=1),
            'max_points': 50.0,
            'weight': 1.0,
            'is_published': True
        }
    )
    
    # Homework assignment
    hw_assignment, hw_created = Assignment.objects.get_or_create(
        section=section,
        name='Homework 5 - Practice Problems',
        defaults={
            'category': category_homework,
            'description': 'Practice problems on linear equations',
            'assigned_date': today - timedelta(days=2),
            'due_date': today + timedelta(days=1),
            'max_points': 25.0,
            'weight': 1.0,
            'is_published': True
        }
    )
    
    if test_created:
        print(f'✅ Created test assignment: {test_assignment.name}')
    if quiz_created:
        print(f'✅ Created quiz assignment: {quiz_assignment.name}') 
    if hw_created:
        print(f'✅ Created homework assignment: {hw_assignment.name}')
    
    # Create grades for both students
    # Grades for student1 (Emma) - A student
    Grade.objects.get_or_create(
        enrollment=enrollment,
        assignment=test_assignment,
        defaults={
            'points_earned': 92.0,
            'percentage': 92.0,
            'letter_grade': 'A-',
            'graded_by': teacher_user,
            'graded_date': today - timedelta(days=2)
        }
    )
    
    Grade.objects.get_or_create(
        enrollment=enrollment,
        assignment=quiz_assignment,
        defaults={
            'points_earned': 48.0,
            'percentage': 96.0,
            'letter_grade': 'A+',
            'graded_by': teacher_user,
            'graded_date': today - timedelta(days=1)
        }
    )
    
    print(f'✅ Created grades for {student.first_name} {student.last_name}')
    
    # 9. Create additional test accounts
    print('\n📝 Creating Additional Test Accounts...')
    
    # Additional parent
    parent2_user, created = User.objects.get_or_create(
        username='parent2',
        defaults={
            'email': 'parent2@email.com',
            'first_name': 'Jennifer',
            'last_name': 'Davis'
        }
    )
    if created:
        parent2_user.set_password('password123')
        parent2_user.save()
        assign_role_to_user(parent2_user, UserRoles.PARENT)
        print(f'✅ Created additional parent: {parent2_user.username}')
    
    # Additional student
    student2_user, created = User.objects.get_or_create(
        username='student2',
        defaults={
            'email': 'student2@school.edu',
            'first_name': 'James',
            'last_name': 'Davis'
        }
    )
    if created:
        student2_user.set_password('password123')
        student2_user.save()
        assign_role_to_user(student2_user, UserRoles.STUDENT)
        
        # Create student record
        student2, created_record = Student.objects.get_or_create(
            student_id='STU002',
            defaults={
                'first_name': student2_user.first_name,
                'last_name': student2_user.last_name,
                'grade_level': grade_level,
                'date_of_birth': date(2008, 8, 22),
                'enrollment_date': date(2024, 9, 1),
                'is_active': True
            }
        )
        
        if created_record:
            # Link to parent2
            student2.family_access_users.add(parent2_user)
            
            # Enroll student2 in the same class as student1 (same teacher)
            enrollment2, created_enrollment = Enrollment.objects.get_or_create(
                student=student2,
                section=section,  # Same section as student1
                defaults={
                    'is_active': True,
                    'final_grade': 'B+',
                    'final_percentage': 87.3
                }
            )
            if created_enrollment:
                print(f'✅ Enrolled {student2.first_name} {student2.last_name} in {section}')
                
                # Create grades for student2 (James) - B student  
                Grade.objects.get_or_create(
                    enrollment=enrollment2,
                    assignment=test_assignment,
                    defaults={
                        'points_earned': 85.0,
                        'percentage': 85.0,
                        'letter_grade': 'B',
                        'graded_by': teacher_user,
                        'graded_date': today - timedelta(days=2)
                    }
                )
                
                Grade.objects.get_or_create(
                    enrollment=enrollment2,
                    assignment=quiz_assignment,
                    defaults={
                        'points_earned': 44.0,
                        'percentage': 88.0,
                        'letter_grade': 'B+',
                        'graded_by': teacher_user,
                        'graded_date': today - timedelta(days=1)
                    }
                )
                
                print(f'✅ Created grades for {student2.first_name} {student2.last_name}')
            
            print(f'✅ Created additional student: {student2_user.username} linked to {parent2_user.username}')
    
    # Create admin account
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@school.edu',
            'first_name': 'System',
            'last_name': 'Administrator',
            'is_staff': True,
            'is_superuser': True
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        assign_role_to_user(admin_user, UserRoles.ADMIN)
        print(f'✅ Created admin user: {admin_user.username}')
    
    print('\n🎉 Account Creation Complete!')
    print('\n📋 Account Summary:')
    print('=' * 40)
    print('👨‍🏫 TEACHER ACCOUNTS:')
    print('   Username: teacher1')
    print('   Password: password123')
    print('   Role: Staff (Teacher)')
    print('   URL: http://localhost:8000/teacher/')
    print()
    print('👨‍👩‍👧‍👦 PARENT ACCOUNTS:')
    print('   Username: parent1')
    print('   Password: password123') 
    print('   Role: Parent')
    print('   Child: Emma Smith')
    print('   URL: http://localhost:8000/parent/')
    print()
    print('   Username: parent2')
    print('   Password: password123')
    print('   Role: Parent') 
    print('   Child: James Davis')
    print('   URL: http://localhost:8000/parent/')
    print()
    print('🎓 STUDENT ACCOUNTS:')
    print('   Username: student1')
    print('   Password: password123')
    print('   Role: Student')
    print('   Name: Emma Smith')
    print('   URL: http://localhost:8000/student/')
    print()
    print('   Username: student2')
    print('   Password: password123')
    print('   Role: Student')
    print('   Name: James Davis')
    print('   URL: http://localhost:8000/student/')
    print()
    print('🔧 ADMIN ACCOUNT:')
    print('   Username: admin')
    print('   Password: admin123')
    print('   Role: Admin')
    print('   URL: http://localhost:8000/admin/')
    print()
    print('🔗 RELATIONSHIP SUMMARY:')
    print('========================================')
    print('👨‍🏫 Teacher: Sarah Johnson (teacher1)')
    print('   📚 Teaches: MATH101-A (Algebra II)')
    print('   🎓 Students: Emma Smith, James Davis')
    print('')
    print('👨‍👩‍👧‍👦 Parent: Michael Smith (parent1)')
    print('   👧 Child: Emma Smith (A student)')
    print('   📊 Can see grades in Sarah Johnson\'s class')
    print('')
    print('👨‍👩‍👧‍👦 Parent: Jennifer Davis (parent2)')
    print('   👦 Child: James Davis (B student)')
    print('   📊 Can see grades in Sarah Johnson\'s class')
    print('')
    print('🎓 Student: Emma Smith (student1)')
    print('   📚 Enrolled in: MATH101-A with Sarah Johnson')
    print('   👨‍👩‍👧‍👦 Parent: Michael Smith')
    print('   📊 Recent grades: A- on test, A+ on quiz')
    print('')
    print('🎓 Student: James Davis (student2)')
    print('   📚 Enrolled in: MATH101-A with Sarah Johnson')
    print('   👨‍👩‍👧‍👦 Parent: Jennifer Davis')
    print('   📊 Recent grades: B on test, B+ on quiz')
    print('')
    print('🌐 TEST THE SYSTEM:')
    print('   1. Start server: python3 schooldriver-modern/manage.py runserver')
    print('   2. Visit: http://localhost:8000')
    print('   3. Login with any of the accounts above')
    print('   4. Each role will redirect to their appropriate dashboard')
    print('   5. Teachers can see both students in their gradebook')
    print('   6. Parents can see their child\'s progress with the teacher')
    print('   7. Students can see their assignments and grades')

if __name__ == '__main__':
    create_linked_accounts()
