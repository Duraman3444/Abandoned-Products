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

def test_notification_system():
    print('🔔 Testing Notification System')
    print('=' * 50)
    
    # Use existing test user
    user = User.objects.filter(username='testparent').first()
    if not user:
        print('❌ Test user not found')
        return
    
    print(f'✅ Testing with user: {user.username}')
    
    client = Client()
    login_success = client.login(username=user.username, password='testpass123')
    if not login_success:
        print('❌ Login failed')
        return
    
    print('✅ User logged in successfully')
    
    # Test notification system endpoints
    endpoints = [
        ('/notifications/', 'Notification Dashboard'),
        ('/notifications/preferences/', 'Notification Preferences'),
        ('/notifications/list/', 'Notification List'),
        ('/notifications/conferences/', 'Conference Scheduling'),
    ]
    
    for url, name in endpoints:
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
    
    # Test data models
    try:
        from notification_system.models import (
            Notification, NotificationPreference, NotificationTemplate,
            NotificationLog, ConferenceSchedule
        )
        
        notifications = Notification.objects.count()
        preferences = NotificationPreference.objects.count()
        templates = NotificationTemplate.objects.count()
        logs = NotificationLog.objects.count()
        conferences = ConferenceSchedule.objects.count()
        
        print(f'\n📊 Notification System Data:')
        print(f'   Notifications: {notifications}')
        print(f'   Preferences: {preferences}')
        print(f'   Templates: {templates}')
        print(f'   Logs: {logs}')
        print(f'   Conference Schedules: {conferences}')
        
    except Exception as e:
        print(f'❌ Data check error: {str(e)}')
    
    # Test notification service
    try:
        from notification_system.services import NotificationService
        service = NotificationService()
        print('✅ NotificationService instantiated successfully')
        
        # Test creating a sample notification
        from students.models import Student
        student = Student.objects.first()
        if student:
            result = service.send_grade_notification(
                student=student,
                assignment_name="Test Assignment",
                grade="A",
                message="Your child received an A on Test Assignment"
            )
            print(f'✅ Grade notification test: {result}')
        
    except Exception as e:
        print(f'❌ Service test error: {str(e)[:100]}...')
    
    print('\n🎉 Notification system testing completed!')

if __name__ == '__main__':
    test_notification_system()
