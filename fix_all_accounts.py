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
from students.models import Student

def fix_all_accounts():
    print('🔧 Fixing All Existing Accounts')
    print('=' * 50)
    
    # Fix parent accounts
    parent_users = User.objects.filter(username__startswith='parent')
    students = Student.objects.all()
    
    fixed_count = 0
    
    for i, parent_user in enumerate(parent_users):
        current_role = get_user_role(parent_user)
        
        if not current_role:
            # Assign Parent role
            assign_role_to_user(parent_user, UserRoles.PARENT)
            print(f'✅ Assigned Parent role to {parent_user.username}')
            fixed_count += 1
            
        # Link to a student if not already linked
        if not parent_user.accessible_students.exists() and students:
            # Try to find a student without a parent first
            unlinked_students = [s for s in students if not s.family_access_users.exists()]
            
            if unlinked_students:
                student = unlinked_students[0]
                student.family_access_users.add(parent_user)
                print(f'✅ Linked {parent_user.username} to student {student.first_name} {student.last_name}')
    
    # Fix student accounts that might exist
    student_users = User.objects.filter(username__startswith='student')
    for student_user in student_users:
        current_role = get_user_role(student_user)
        if not current_role:
            assign_role_to_user(student_user, UserRoles.STUDENT)
            print(f'✅ Assigned Student role to {student_user.username}')
            fixed_count += 1
    
    # Fix teacher accounts
    teacher_emails = ['@school.edu']
    for email_pattern in teacher_emails:
        teachers = User.objects.filter(email__contains=email_pattern).exclude(username__in=['admin', 'test_admin'])
        for teacher in teachers:
            current_role = get_user_role(teacher)
            if not current_role:
                assign_role_to_user(teacher, UserRoles.STAFF)
                print(f'✅ Assigned Staff role to {teacher.username}')
                fixed_count += 1
    
    print(f'\n🎉 Fixed {fixed_count} accounts!')
    
    # Create some easy test accounts
    print('\n📝 Creating Easy Test Accounts...')
    
    # Simple test accounts with easy passwords
    test_accounts = [
        ('parent_test', 'test', 'Test', 'Parent', 'parent@test.com', UserRoles.PARENT),
        ('teacher_test', 'test', 'Test', 'Teacher', 'teacher@test.com', UserRoles.STAFF),
        ('student_test', 'test', 'Test', 'Student', 'student@test.com', UserRoles.STUDENT),
    ]
    
    for username, password, first_name, last_name, email, role in test_accounts:
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'email': email
            }
        )
        if created:
            user.set_password(password)
            user.save()
            print(f'✅ Created {username}')
        
        assign_role_to_user(user, role)
        
        # Link parent to first available student
        if role == UserRoles.PARENT:
            unlinked_students = [s for s in students if not s.family_access_users.filter(username=username).exists()]
            if unlinked_students:
                student = unlinked_students[0]
                student.family_access_users.add(user)
                print(f'✅ Linked {username} to {student.first_name} {student.last_name}')

def show_easy_logins():
    print('\n🎯 EASY LOGIN ACCOUNTS')
    print('=' * 40)
    print('Username: test1')
    print('Password: test123')
    print('Role: Parent')
    print()
    print('Username: parent_test')
    print('Password: test')
    print('Role: Parent')
    print()
    print('Username: teacher_test')
    print('Password: test')
    print('Role: Teacher')
    print()
    print('Username: student_test')
    print('Password: test')
    print('Role: Student')
    print()
    print('Username: teacher1')
    print('Password: password123')
    print('Role: Teacher (with real class data)')
    print()
    print('Username: parent1')
    print('Password: password123')
    print('Role: Parent (with real student data)')

if __name__ == '__main__':
    fix_all_accounts()
    show_easy_logins()
