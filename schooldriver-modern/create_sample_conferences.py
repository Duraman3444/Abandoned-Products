#!/usr/bin/env python3
"""
Create sample conference slots for testing parent portal
"""
import os
import sys
import django
from datetime import datetime, timedelta, time

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schooldriver_modern.settings')
django.setup()

from django.contrib.auth.models import User
from academics.models import ConferenceSlot
from django.utils import timezone

def create_sample_conference_slots():
    """Create sample conference slots for testing"""
    
    # Get staff users to act as teachers for demo
    teachers = User.objects.filter(is_staff=True)[:3]
    
    if not teachers.exists():
        print("No staff users found. Creating sample teachers...")
        for i in range(1, 4):
            teacher_user = User.objects.create_user(
                username=f'teacher{i}',
                email=f'teacher{i}@school.edu',
                first_name=f'Teacher{i}',
                last_name='Demo',
                password='teacher123',
                is_staff=True
            )
            print(f"Created teacher: {teacher_user.username}")
        teachers = User.objects.filter(is_staff=True)[:3]
    
    # Create conference slots for next two weeks
    created_count = 0
    today = timezone.now().date()
    
    for teacher in teachers:
        # Create slots for conference days (Mon, Wed, Fri of next week)
        for days_ahead in [7, 9, 11, 14, 16, 18]:  # Next week and week after
            conference_date = today + timedelta(days=days_ahead)
            
            # Create slots from 3:00 PM to 5:00 PM (after school hours)
            start_times = [
                time(15, 0),   # 3:00 PM
                time(15, 15),  # 3:15 PM
                time(15, 30),  # 3:30 PM
                time(15, 45),  # 3:45 PM
                time(16, 0),   # 4:00 PM
                time(16, 15),  # 4:15 PM
                time(16, 30),  # 4:30 PM
                time(16, 45),  # 4:45 PM
            ]
            
            for start_time in start_times:
                # Calculate end time (15 minutes later)
                end_minutes = start_time.minute + 15
                end_hour = start_time.hour
                if end_minutes >= 60:
                    end_minutes -= 60
                    end_hour += 1
                end_time = time(end_hour, end_minutes)
                
                slot, created = ConferenceSlot.objects.get_or_create(
                    teacher=teacher,
                    date=conference_date,
                    start_time=start_time,
                    defaults={
                        'end_time': end_time,
                        'duration_minutes': 15,
                        'status': 'AVAILABLE',
                        'location': f'Room {teacher.profile.id if hasattr(teacher, "profile") else "101"}',
                        'notes': f'Parent conference with {teacher.get_full_name()}'
                    }
                )
                
                if created:
                    created_count += 1
                    print(f"Created conference slot: {teacher.get_full_name()} - {conference_date} {start_time}")
    
    print(f"\nCreated {created_count} new conference slots")
    print(f"Total conference slots: {ConferenceSlot.objects.count()}")

if __name__ == '__main__':
    create_sample_conference_slots()
