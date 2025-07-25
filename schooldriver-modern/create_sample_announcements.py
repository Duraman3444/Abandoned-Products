#!/usr/bin/env python3
"""
Create sample announcements for testing parent portal
"""
import os
import sys
import django
from datetime import datetime, timedelta

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schooldriver_modern.settings')
django.setup()

from django.contrib.auth.models import User
from academics.models import Announcement
from django.utils import timezone

def create_sample_announcements():
    """Create sample announcements for testing"""
    
    # Get or create admin user
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@school.edu',
            'first_name': 'Admin',
            'is_staff': True,
            'is_superuser': True
        }
    )
    
    # Sample announcements
    announcements_data = [
        {
            'title': 'Parent-Teacher Conference Sign-ups Open',
            'content': 'Parent-teacher conferences are scheduled for November 15-16, 2024. Please sign up for your preferred time slot through the parent portal. Conference slots are 15 minutes each and will be held in classrooms.',
            'audience': 'PARENTS',
            'priority': 'HIGH',
            'is_published': True,
            'publish_date': timezone.now() - timedelta(days=1),
            'expire_date': timezone.now() + timedelta(days=14),
            'send_email_notification': True,
        },
        {
            'title': 'School Closed - Teacher Work Day',
            'content': 'School will be closed on Friday, November 8th for a teacher professional development day. There will be no classes. After-school activities are also cancelled.',
            'audience': 'ALL',
            'priority': 'URGENT',
            'is_published': True,
            'publish_date': timezone.now() - timedelta(hours=6),
            'expire_date': timezone.now() + timedelta(days=7),
            'send_email_notification': True,
            'send_sms_notification': True,
        },
        {
            'title': 'Fall Fundraiser - Book Fair',
            'content': 'Our annual Fall Book Fair is coming up from November 18-22. Students can browse and purchase books during their library time. Parent volunteers needed - sign up in the main office.',
            'audience': 'PARENTS',
            'priority': 'NORMAL',
            'is_published': True,
            'publish_date': timezone.now() - timedelta(days=3),
            'expire_date': timezone.now() + timedelta(days=20),
        },
        {
            'title': 'Winter Sports Registration',
            'content': 'Registration for winter sports (basketball, wrestling, swimming) is now open. Forms must be submitted by November 30th along with physical examination forms.',
            'audience': 'ALL',
            'priority': 'NORMAL',
            'is_published': True,
            'publish_date': timezone.now() - timedelta(days=5),
            'expire_date': timezone.now() + timedelta(days=25),
        },
        {
            'title': 'Early Dismissal - November 20th',
            'content': 'URGENT: Due to severe weather forecast, school will dismiss 2 hours early on Wednesday, November 20th. Buses will run on early dismissal schedule. Please make arrangements for your child.',
            'audience': 'PARENTS',
            'priority': 'URGENT', 
            'is_published': True,
            'publish_date': timezone.now() - timedelta(minutes=30),
            'expire_date': timezone.now() + timedelta(days=3),
            'send_email_notification': True,
            'send_sms_notification': True,
            'send_push_notification': True,
        }
    ]
    
    created_count = 0
    for announcement_data in announcements_data:
        announcement, created = Announcement.objects.get_or_create(
            title=announcement_data['title'],
            defaults={
                **announcement_data,
                'created_by': admin_user
            }
        )
        if created:
            created_count += 1
            print(f"Created announcement: {announcement.title}")
        else:
            print(f"Announcement already exists: {announcement.title}")
    
    print(f"\nCreated {created_count} new announcements")
    print(f"Total announcements: {Announcement.objects.count()}")

if __name__ == '__main__':
    create_sample_announcements()
