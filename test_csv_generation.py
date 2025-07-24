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
from django.http import HttpResponse
from datetime import date, timedelta
import csv
from collections import defaultdict

print("=== Testing CSV Generation ===")

section = CourseSection.objects.filter(is_active=True).first()
print(f"Using section: {section}")

# Get attendance data
attendance_records = Attendance.objects.filter(
    enrollment__section=section,
    date__gte=date.today() - timedelta(days=30),
    date__lte=date.today()
).select_related('enrollment__student', 'absence_reason')

print(f"Found {attendance_records.count()} attendance records")

# Test CSV generation
response = HttpResponse(content_type='text/csv')
response['Content-Disposition'] = f'attachment; filename="test_daily_attendance_{section.course.course_code}.csv"'

writer = csv.writer(response)
writer.writerow(['Date', 'Present', 'Absent', 'Tardy', 'Excused', 'Total', 'Attendance Rate'])

# Group by date
daily_data = defaultdict(lambda: {'P': 0, 'A': 0, 'T': 0, 'E': 0, 'L': 0})

for record in attendance_records:
    daily_data[record.date][record.status] += 1

print(f"Grouped data for {len(daily_data)} dates")

# Generate CSV rows
if not daily_data:
    writer.writerow(['No data', 0, 0, 0, 0, 0, '0%'])
    print("No data found, writing empty row")
else:
    for date, counts in sorted(daily_data.items()):
        total = sum(counts.values())
        present = counts['P']
        absent = counts['A'] + counts['E']
        tardy = counts['T'] + counts['L']
        excused = counts['E'] + counts['L']
        rate = (present / total * 100) if total > 0 else 0
        
        row = [date, present, absent, tardy, excused, total, f"{rate:.1f}%"]
        writer.writerow(row)
        print(f"Row: {row}")

print("CSV generation completed successfully!")
print(f"Response content type: {response.get('Content-Type')}")
print(f"Response content disposition: {response.get('Content-Disposition')}")
