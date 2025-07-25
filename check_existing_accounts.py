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

def check_existing_accounts():
    print('🔍 Checking Existing User Accounts')
    print('=' * 50)
    
    # Get all users
    users = User.objects.all().order_by('username')
    
    print(f'Found {users.count()} users in the system:\n')
    
    for user in users:
        role = get_user_role(user)
        groups = list(user.groups.values_list('name', flat=True))
        
        print(f'👤 Username: {user.username}')
        print(f'   Name: {user.first_name} {user.last_name}')
        print(f'   Email: {user.email}')
        print(f'   Current Role: {role or "None"}')
        print(f'   Groups: {groups}')
        print(f'   Staff: {user.is_staff}')
        print(f'   Superuser: {user.is_superuser}')
        
        # Check if user has accessible students
        if hasattr(user, 'accessible_students'):
            accessible_students = user.accessible_students.all()
            if accessible_students:
                print(f'   Children: {[f"{s.first_name} {s.last_name}" for s in accessible_students]}')
        
        print()
    
    # Check students
    students = Student.objects.all()
    print(f'📚 Found {students.count()} students in the system:\n')
    
    for student in students:
        print(f'🎓 Student: {student.first_name} {student.last_name} (ID: {student.student_id})')
        parents = student.family_access_users.all()
        if parents:
            print(f'   Parents: {[f"{p.username} ({p.first_name} {p.last_name})" for p in parents]}')
        else:
            print('   Parents: None')
        print()

def fix_test1_account():
    print('\n🔧 Fixing test1 account...')
    
    try:
        user = User.objects.get(username='test1')
        print(f'✅ Found user: {user.username}')
        
        # Assign Parent role
        assign_role_to_user(user, UserRoles.PARENT)
        print('✅ Assigned Parent role')
        
        # Try to link to a student if one exists
        students = Student.objects.all()
        if students:
            student = students.first()
            student.family_access_users.add(user)
            print(f'✅ Linked to student: {student.first_name} {student.last_name}')
        
        print('✅ test1 account fixed!')
        
    except User.DoesNotExist:
        print('❌ test1 user not found')
        
        # Create test1 user
        user = User.objects.create_user(
            username='test1',
            password='test123',
            first_name='Test',
            last_name='Parent',
            email='test1@example.com'
        )
        assign_role_to_user(user, UserRoles.PARENT)
        
        # Link to first student if exists
        students = Student.objects.all()
        if students:
            student = students.first()
            student.family_access_users.add(user)
            print(f'✅ Created test1 and linked to student: {student.first_name} {student.last_name}')

if __name__ == '__main__':
    check_existing_accounts()
    fix_test1_account()
    print('\n🎉 Account check complete!')
    print('\nYou can now login with:')
    print('- test1 / test123 (Parent)')
    print('- teacher1 / password123 (Teacher)')  
    print('- parent1 / password123 (Parent)')
    print('- student1 / password123 (Student)')
