#!/usr/bin/env python3
"""
Create sample data for school services testing
"""
import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta, time, date

# Add the project directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schooldriver_modern.settings')
django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from students.models import Student, SchoolYear
from school_services.models import (
    LunchAccount, LunchTransaction, TransportationInfo, TransportationAlert,
    Activity, SupplyList, SupplyItem, VolunteerOpportunity
)


def create_lunch_accounts():
    """Create lunch accounts with sample data"""
    print("Creating lunch accounts...")
    
    students = Student.objects.all()[:5]  # Get first 5 students
    
    for student in students:
        lunch_account, created = LunchAccount.objects.get_or_create(
            student=student,
            defaults={
                'balance': Decimal('25.50'),
                'low_balance_threshold': Decimal('5.00'),
                'auto_reload_enabled': True,
                'auto_reload_amount': Decimal('25.00'),
                'auto_reload_threshold': Decimal('10.00'),
                'default_payment_method': 'Credit Card'
            }
        )
        
        if created:
            # Create some sample transactions
            transactions = [
                ('CREDIT', Decimal('25.00'), 'Initial deposit', 'Credit Card'),
                ('DEBIT', Decimal('3.50'), 'Lunch purchase - Pizza day', ''),
                ('DEBIT', Decimal('4.25'), 'Lunch purchase - Chicken sandwich', ''),
                ('CREDIT', Decimal('10.00'), 'Added funds', 'PayPal'),
                ('DEBIT', Decimal('2.75'), 'Lunch purchase - Salad', ''),
            ]
            
            for trans_type, amount, description, payment_method in transactions:
                LunchTransaction.objects.create(
                    lunch_account=lunch_account,
                    transaction_type=trans_type,
                    amount=amount,
                    description=description,
                    payment_method=payment_method
                )
            
            print(f"Created lunch account for {student.display_name}")


def create_transportation_info():
    """Create transportation information"""
    print("Creating transportation information...")
    
    students = Student.objects.all()[:3]
    
    transport_data = [
        {
            'transport_type': 'BUS',
            'bus_route': 'Route 15',
            'bus_number': 'Bus 247',
            'pickup_time': time(7, 30),
            'pickup_location': '123 Main St & Oak Ave',
            'dropoff_time': time(15, 45),
            'dropoff_location': '123 Main St & Oak Ave',
            'special_instructions': 'Student requires assistance boarding due to mobility aid'
        },
        {
            'transport_type': 'BUS',
            'bus_route': 'Route 8',
            'bus_number': 'Bus 163',
            'pickup_time': time(7, 45),
            'pickup_location': 'Elm Street Bus Stop',
            'dropoff_time': time(15, 30),
            'dropoff_location': 'Elm Street Bus Stop',
        },
        {
            'transport_type': 'PARENT',
            'special_instructions': 'Parent pickup/dropoff only'
        }
    ]
    
    for i, student in enumerate(students):
        data = transport_data[i % len(transport_data)]
        transportation, created = TransportationInfo.objects.get_or_create(
            student=student,
            defaults=data
        )
        
        if created:
            print(f"Created transportation info for {student.display_name}")


def create_transportation_alerts():
    """Create transportation alerts"""
    print("Creating transportation alerts...")
    
    alerts_data = [
        {
            'alert_type': 'DELAY',
            'title': 'Bus Route 15 Delayed',
            'message': 'Route 15 is running approximately 10 minutes late due to traffic conditions on Main Street.',
            'affected_routes': '15',
            'expires_at': timezone.now() + timedelta(hours=2)
        },
        {
            'alert_type': 'WEATHER',
            'title': 'Weather Advisory - All Routes',
            'message': 'Due to icy conditions, all bus routes may experience delays this morning. Please allow extra time.',
            'affected_routes': '',  # Affects all routes
            'expires_at': timezone.now() + timedelta(hours=4)
        }
    ]
    
    for alert_data in alerts_data:
        alert, created = TransportationAlert.objects.get_or_create(
            title=alert_data['title'],
            defaults=alert_data
        )
        
        if created:
            print(f"Created transportation alert: {alert.title}")


def create_activities():
    """Create extracurricular activities"""
    print("Creating activities...")
    
    # Get some staff users to be supervisors
    supervisors = User.objects.filter(is_staff=True)[:3]
    
    activities_data = [
        {
            'name': 'Chess Club',
            'description': 'Learn chess strategies and compete in tournaments. All skill levels welcome!',
            'activity_type': 'ACADEMIC',
            'meeting_days': 'Tuesday, Thursday',
            'meeting_time': '3:30 PM - 4:30 PM',
            'location': 'Library',
            'max_participants': 20,
            'grade_levels': '6,7,8,9,10,11,12',
            'registration_fee': Decimal('15.00'),
            'registration_start': date.today() - timedelta(days=7),
            'registration_end': date.today() + timedelta(days=14),
            'activity_start': date.today() + timedelta(days=21),
            'activity_end': date.today() + timedelta(days=120),
        },
        {
            'name': 'Basketball Team',
            'description': 'Competitive basketball team. Tryouts required. Must maintain academic eligibility.',
            'activity_type': 'SPORTS',
            'meeting_days': 'Monday, Wednesday, Friday',
            'meeting_time': '4:00 PM - 6:00 PM',
            'location': 'Gymnasium',
            'max_participants': 15,
            'grade_levels': '9,10,11,12',
            'registration_fee': Decimal('75.00'),
            'registration_start': date.today() - timedelta(days=14),
            'registration_end': date.today() + timedelta(days=7),
            'activity_start': date.today() + timedelta(days=14),
            'activity_end': date.today() + timedelta(days=150),
        },
        {
            'name': 'Drama Club',
            'description': 'Participate in school plays and musicals. No experience necessary - we welcome all!',
            'activity_type': 'ARTS',
            'meeting_days': 'Monday, Wednesday',
            'meeting_time': '3:30 PM - 5:30 PM',
            'location': 'Auditorium',
            'max_participants': 0,  # No limit
            'grade_levels': '6,7,8,9,10,11,12',
            'registration_fee': Decimal('25.00'),
            'registration_start': date.today() - timedelta(days=3),
            'registration_end': date.today() + timedelta(days=21),
            'activity_start': date.today() + timedelta(days=28),
            'activity_end': date.today() + timedelta(days=180),
        }
    ]
    
    for i, activity_data in enumerate(activities_data):
        supervisor = supervisors[i % len(supervisors)] if supervisors else None
        activity_data['supervisor'] = supervisor
        
        activity, created = Activity.objects.get_or_create(
            name=activity_data['name'],
            defaults=activity_data
        )
        
        if created:
            print(f"Created activity: {activity.name}")


def create_supply_lists():
    """Create school supply lists"""
    print("Creating supply lists...")
    
    current_year = SchoolYear.objects.filter(is_active=True).first()
    if not current_year:
        print("No active school year found, skipping supply lists")
        return
    
    supply_lists_data = [
        {
            'grade_level': '9',
            'subject': 'English',
            'title': '9th Grade English Supplies',
            'description': 'Required supplies for English 9 course',
            'items': [
                ('3-Ring Binder (2 inch)', '1', True, 'Any brand', '$8-12'),
                ('Loose Leaf Paper (College Ruled)', '200 sheets', True, '', '$3-5'),
                ('Blue or Black Pens', '12 pack', True, 'Bic or similar', '$5-8'),
                ('Pencils (#2)', '12 pack', True, '', '$3-5'),
                ('Highlighters (assorted colors)', '4 pack', True, '', '$4-6'),
                ('Index Cards (3x5)', '2 packs', False, '', '$2-3'),
            ]
        },
        {
            'grade_level': '10',
            'subject': 'Mathematics',
            'title': '10th Grade Math Supplies',
            'description': 'Required supplies for Algebra II and Geometry',
            'items': [
                ('Graphing Calculator', '1', True, 'TI-84 Plus recommended', '$80-120'),
                ('Graph Paper Notebook', '2', True, '', '$4-8'),
                ('Mechanical Pencils (0.7mm)', '2 packs', True, '', '$6-10'),
                ('Compass and Protractor Set', '1', True, '', '$8-15'),
                ('Ruler (12 inch)', '1', True, '', '$2-4'),
                ('Eraser (large)', '2', True, '', '$2-4'),
            ]
        }
    ]
    
    for list_data in supply_lists_data:
        items_data = list_data.pop('items')
        
        supply_list, created = SupplyList.objects.get_or_create(
            title=list_data['title'],
            defaults={
                **list_data,
                'school_year': current_year
            }
        )
        
        if created:
            for item_name, quantity, is_required, brand_pref, cost_range in items_data:
                SupplyItem.objects.create(
                    supply_list=supply_list,
                    name=item_name,
                    quantity=quantity,
                    is_required=is_required,
                    brand_preference=brand_pref,
                    store_suggestions=cost_range
                )
            
            print(f"Created supply list: {supply_list.title}")


def create_volunteer_opportunities():
    """Create volunteer opportunities"""
    print("Creating volunteer opportunities...")
    
    # Get coordinator users
    coordinators = User.objects.filter(is_staff=True)[:2]
    
    opportunities_data = [
        {
            'title': 'Fall Festival Setup',
            'description': 'Help set up booths, decorations, and equipment for our annual Fall Festival. Great way to get involved!',
            'volunteer_type': 'EVENT',
            'date': date.today() + timedelta(days=14),
            'start_time': time(8, 0),
            'end_time': time(12, 0),
            'location': 'School Gymnasium and Cafeteria',
            'volunteers_needed': 15,
            'special_requirements': 'Ability to lift up to 25 lbs. Background check required.',
            'contact_email': 'events@school.edu',
            'contact_phone': '(555) 123-4567',
            'preparation_notes': 'Wear comfortable clothes and closed-toe shoes. Light refreshments provided.'
        },
        {
            'title': 'Reading Buddy Program',
            'description': 'Work one-on-one with elementary students to help improve their reading skills. Very rewarding!',
            'volunteer_type': 'CLASSROOM',
            'date': date.today() + timedelta(days=7),
            'start_time': time(9, 0),
            'end_time': time(11, 0),
            'location': 'Elementary Library',
            'volunteers_needed': 8,
            'special_requirements': 'Background check required. Must commit to weekly sessions for at least 1 month.',
            'contact_email': 'reading@school.edu',
            'contact_phone': '(555) 234-5678',
            'preparation_notes': 'Training session will be provided before first volunteer day.'
        },
        {
            'title': 'Science Fair Judging',
            'description': 'Help judge student science fair projects. Science background helpful but not required.',
            'volunteer_type': 'EVENT',
            'date': date.today() + timedelta(days=21),
            'start_time': time(9, 0),
            'end_time': time(15, 0),
            'location': 'School Gymnasium',
            'volunteers_needed': 12,
            'special_requirements': 'Must be available for the full day. Lunch will be provided.',
            'contact_email': 'science@school.edu',
            'contact_phone': '(555) 345-6789',
            'preparation_notes': 'Judging criteria and forms will be provided on the day of the event.'
        }
    ]
    
    for i, opp_data in enumerate(opportunities_data):
        coordinator = coordinators[i % len(coordinators)] if coordinators else None
        opp_data['coordinator'] = coordinator
        
        opportunity, created = VolunteerOpportunity.objects.get_or_create(
            title=opp_data['title'],
            date=opp_data['date'],
            defaults=opp_data
        )
        
        if created:
            print(f"Created volunteer opportunity: {opportunity.title}")


def main():
    """Create all sample data"""
    print("Creating school services sample data...")
    print("=" * 50)
    
    create_lunch_accounts()
    create_transportation_info()
    create_transportation_alerts()
    create_activities()
    create_supply_lists()
    create_volunteer_opportunities()
    
    print("=" * 50)
    print("Sample data creation completed!")


if __name__ == '__main__':
    main()
