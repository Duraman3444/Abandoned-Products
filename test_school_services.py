#!/usr/bin/env python3

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schooldriver_modern.settings')
sys.path.append('./schooldriver-modern')
django.setup()

from django.contrib.auth.models import User
from django.test import Client
from students.models import Student

def test_school_services():
    print('🚀 Testing School Services')
    print('=' * 50)
    
    # Create a test user if needed
    user, created = User.objects.get_or_create(
        username='testparent',
        defaults={
            'email': 'testparent@example.com',
            'first_name': 'Test',
            'last_name': 'Parent'
        }
    )
    
    if created:
        user.set_password('testpass123')
        user.save()
        print(f'✅ Created test user: {user.username}')
    else:
        print(f'✅ Using existing user: {user.username}')
    
    # Add user to Parent group (not Parents)
    from django.contrib.auth.models import Group
    from schooldriver_modern.roles import UserRoles, assign_role_to_user
    
    # Create default groups first
    from schooldriver_modern.roles import create_default_groups
    create_default_groups()
    
    # Assign Parent role
    assign_role_to_user(user, UserRoles.PARENT)
    print(f'✅ Added user to Parent role')
    
    client = Client()
    
    # Test without login first
    response = client.get('/services/')
    if response.status_code == 302:  # Redirect to login
        print('✅ Authentication required for school services (as expected)')
    else:
        print(f'❌ Unexpected status for unauthenticated access: {response.status_code}')
    
    # Login
    login_success = client.login(username=user.username, password='testpass123')
    if not login_success:
        print('❌ Login failed')
        return
    
    print('✅ User logged in successfully')
    
    # Test school services endpoints
    services = [
        ('/services/lunch-account/', 'Lunch Account'),
        ('/services/transportation/', 'Transportation'),
        ('/services/activities/', 'Activities'),
        ('/services/supply-lists/', 'Supply Lists'),
        ('/services/events-rsvp/', 'Events RSVP'),
        ('/services/volunteer-opportunities/', 'Volunteer Opportunities'),
    ]
    
    for url, name in services:
        try:
            response = client.get(url)
            if response.status_code == 200:
                print(f'✅ {name}: {response.status_code}')
            elif response.status_code == 302:
                print(f'⚠️  {name}: {response.status_code} (redirect)')
            else:
                print(f'❌ {name}: {response.status_code}')
        except Exception as e:
            print(f'❌ {name} error: {str(e)[:100]}...')
    
    # Test some data endpoints
    try:
        # Check if we have sample data
        from school_services.models import LunchAccount, Activity, Event
        lunch_accounts = LunchAccount.objects.count()
        activities = Activity.objects.count()
        events = Event.objects.count()
        
        print(f'\n📊 School Services Data:')
        print(f'   Lunch Accounts: {lunch_accounts}')
        print(f'   Activities: {activities}')
        print(f'   Events: {events}')
        
    except Exception as e:
        print(f'❌ Data check error: {str(e)}')
    
    print('\n🎉 School services testing completed!')

if __name__ == '__main__':
    test_school_services()
