#!/usr/bin/env python3
import os
import sys
import django

# Add the project directory to Python path
sys.path.append('/Users/abdurrahmanmirza/Gauntlet Projects/Schooldriver-ModernVersion/schooldriver-modern')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schooldriver_modern.settings')
django.setup()

from datetime import date, time, timedelta
from academics.models import SchoolCalendarEvent
from students.models import SchoolYear

# Get current school year
current_school_year = SchoolYear.objects.filter(is_active=True).first()

if current_school_year:
    print(f"Creating sample events for {current_school_year}")
    
    # Create sample events
    events = [
        {
            'title': 'Thanksgiving Break',
            'event_type': 'holiday',
            'start_date': date(2024, 11, 28),
            'end_date': date(2024, 11, 29),
            'description': 'Thanksgiving holiday - no school',
            'color': '#28a745'
        },
        {
            'title': 'Early Dismissal - Parent Conferences',
            'event_type': 'early_dismissal',
            'start_date': date(2024, 12, 15),
            'end_date': date(2024, 12, 15),
            'dismissal_time': time(12, 30),
            'description': 'Early dismissal for parent-teacher conferences',
            'color': '#ffc107'
        },
        {
            'title': 'Winter Break',
            'event_type': 'break',
            'start_date': date(2024, 12, 23),
            'end_date': date(2025, 1, 6),
            'description': 'Winter holiday break',
            'color': '#17a2b8'
        },
        {
            'title': 'Martin Luther King Jr. Day',
            'event_type': 'holiday',
            'start_date': date(2025, 1, 20),
            'end_date': date(2025, 1, 20),
            'description': 'Federal holiday - no school',
            'color': '#28a745'
        },
        {
            'title': 'Spring Testing Week',
            'event_type': 'testing',
            'start_date': date(2025, 3, 10),
            'end_date': date(2025, 3, 14),
            'description': 'State standardized testing',
            'color': '#6c757d'
        }
    ]
    
    for event_data in events:
        event, created = SchoolCalendarEvent.objects.get_or_create(
            title=event_data['title'],
            school_year=current_school_year,
            defaults=event_data
        )
        
        if created:
            print(f"Created event: {event.title}")
        else:
            print(f"Event already exists: {event.title}")
    
    print(f"Total events in school year: {SchoolCalendarEvent.objects.filter(school_year=current_school_year).count()}")
else:
    print("No active school year found!")
