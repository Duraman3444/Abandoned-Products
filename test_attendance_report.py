#!/usr/bin/env python3

import os
import sys
import django

# Add the Django project to the Python path
sys.path.insert(0, 'schooldriver-modern')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schooldriver_modern.settings')
django.setup()

from academics.models import CourseSection, Attendance
from teacher_portal.attendance_forms import AttendanceReportForm
from datetime import date, timedelta

# Test 1: Check if we have sections and attendance data
print("=== Testing Attendance Report Data ===")

sections = CourseSection.objects.filter(is_active=True)
print(f"Active sections: {sections.count()}")

if sections.exists():
    section = sections.first()
    print(f"Testing with section: {section}")
    
    # Check attendance records for this section
    attendance_count = Attendance.objects.filter(enrollment__section=section).count()
    print(f"Attendance records for this section: {attendance_count}")
    
    # Test the form
    print("\n=== Testing AttendanceReportForm ===")
    
    form_data = {
        'report_type': 'daily',
        'format': 'csv',
        'date_start': date.today() - timedelta(days=30),
        'date_end': date.today(),
        'include_patterns': True,
        'include_parent_contact': False
    }
    
    form = AttendanceReportForm(form_data, section=section)
    print(f"Form is valid: {form.is_valid()}")
    
    if not form.is_valid():
        print("Form errors:")
        for field, errors in form.errors.items():
            print(f"  {field}: {errors}")
    else:
        print("Form cleaned data:")
        for key, value in form.cleaned_data.items():
            print(f"  {key}: {value}")
            
        # Test attendance records query
        from academics.models import Attendance
        attendance_records = Attendance.objects.filter(
            enrollment__section=section,
            date__gte=form.cleaned_data['date_start'],
            date__lte=form.cleaned_data['date_end']
        )
        print(f"Attendance records in date range: {attendance_records.count()}")
        
        if attendance_records.exists():
            print("Sample attendance record:")
            record = attendance_records.first()
            print(f"  Date: {record.date}")
            print(f"  Status: {record.status}")
            print(f"  Student: {record.enrollment.student.full_name}")
else:
    print("No active sections found!")
