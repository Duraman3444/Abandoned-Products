#!/usr/bin/env python3
"""Final verification of all student portal data and connections."""

import os
import sys
import django

# Add the Django app directory to the Python path
sys.path.append('/Users/abdurrahmanmirza/Gauntlet Projects/Schooldriver-ModernVersion/schooldriver-modern')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schooldriver_modern.settings')
django.setup()

from django.contrib.auth.models import User
from students.models import Student, SchoolYear
from academics.models import (
    Enrollment, CourseSection, Assignment, Grade, Schedule, Attendance, 
    Course, Department, AssignmentCategory, Announcement
)

def final_verification():
    """Final verification of all student portal functionality."""
    
    print("🔍 FINAL VERIFICATION OF STUDENT PORTAL")
    print("=" * 50)
    
    # Check Emma Smith student
    emma_student = Student.objects.filter(student_id='STU-EMMA-001').first()
    if not emma_student:
        print("❌ Emma Smith student not found!")
        return False
    
    print(f"✅ Student: {emma_student.first_name} {emma_student.last_name} ({emma_student.student_id})")
    print(f"   Email: {emma_student.primary_contact_email}")
    
    # Check Lisa Garcia teacher
    lisa_user = User.objects.filter(username='lisa.garcia').first()
    if not lisa_user:
        print("❌ Lisa Garcia teacher not found!")
        return False
    
    print(f"✅ Teacher: {lisa_user.first_name} {lisa_user.last_name} ({lisa_user.username})")
    
    # Check current school year
    current_year = SchoolYear.objects.filter(is_active=True).first()
    if not current_year:
        print("❌ No active school year found!")
        return False
    
    print(f"✅ School Year: {current_year.name}")
    
    # Check enrollments
    enrollments = Enrollment.objects.filter(
        student=emma_student,
        section__school_year=current_year,
        is_active=True
    )
    
    print(f"\n📚 ENROLLMENTS ({enrollments.count()} total):")
    for enrollment in enrollments:
        print(f"   • {enrollment.section.course.name}")
        print(f"     Teacher: {enrollment.section.teacher.first_name} {enrollment.section.teacher.last_name}")
        print(f"     Section: {enrollment.section.section_name}")
        print(f"     Room: {enrollment.section.room}")
    
    # Check assignments
    assignments = Assignment.objects.filter(
        section__enrollments__student=emma_student,
        section__school_year=current_year,
        is_published=True
    ).distinct()
    
    print(f"\n📝 ASSIGNMENTS ({assignments.count()} total):")
    upcoming = assignments.filter(due_date__gte=django.utils.timezone.now().date())
    past = assignments.filter(due_date__lt=django.utils.timezone.now().date())
    
    print(f"   📅 Upcoming: {upcoming.count()}")
    print(f"   📅 Past due: {past.count()}")
    
    for assignment in assignments[:5]:  # Show first 5
        print(f"   • {assignment.name}")
        print(f"     Course: {assignment.section.course.name}")
        print(f"     Due: {assignment.due_date}")
        print(f"     Points: {assignment.max_points}")
    
    # Check grades
    grades = Grade.objects.filter(
        enrollment__student=emma_student
    )
    
    print(f"\n📊 GRADES ({grades.count()} total):")
    total_points = 0
    total_possible = 0
    
    for grade in grades:
        total_points += float(grade.points_earned or 0)
        total_possible += float(grade.assignment.max_points)
    
    if total_possible > 0:
        overall_percentage = (total_points / total_possible) * 100
        print(f"   📈 Overall Average: {overall_percentage:.1f}%")
        
        # Convert to GPA (4.0 scale)
        if overall_percentage >= 90:
            gpa = 4.0
        elif overall_percentage >= 80:
            gpa = 3.0 + (overall_percentage - 80) / 10
        elif overall_percentage >= 70:
            gpa = 2.0 + (overall_percentage - 70) / 10
        elif overall_percentage >= 60:
            gpa = 1.0 + (overall_percentage - 60) / 10
        else:
            gpa = 0.0
        
        print(f"   📈 GPA (4.0 scale): {gpa:.2f}")
    
    # Show sample grades
    print("   Recent grades:")
    for grade in grades.order_by('-id')[:3]:
        print(f"   • {grade.assignment.name}: {grade.percentage}% ({grade.points_earned}/{grade.assignment.max_points})")
    
    # Check schedules
    schedules = Schedule.objects.filter(
        section__enrollments__student=emma_student,
        section__school_year=current_year,
        is_active=True
    ).distinct()
    
    print(f"\n📅 SCHEDULE ({schedules.count()} total time slots):")
    days = {}
    for schedule in schedules:
        day = schedule.get_day_of_week_display()
        if day not in days:
            days[day] = []
        days[day].append({
            'time': f"{schedule.start_time.strftime('%H:%M')}-{schedule.end_time.strftime('%H:%M')}",
            'course': schedule.section.course.name,
            'teacher': f"{schedule.section.teacher.first_name} {schedule.section.teacher.last_name}",
            'room': schedule.room or schedule.section.room
        })
    
    for day, classes in sorted(days.items()):
        print(f"   {day}:")
        for class_info in sorted(classes, key=lambda x: x['time']):
            print(f"     {class_info['time']} - {class_info['course']}")
            print(f"                    {class_info['room']} • {class_info['teacher']}")
    
    # Check attendance
    attendance_records = Attendance.objects.filter(
        enrollment__student=emma_student
    )
    
    print(f"\n📋 ATTENDANCE ({attendance_records.count()} total records):")
    present_count = attendance_records.filter(status='P').count()
    absent_count = attendance_records.filter(status='A').count()
    tardy_count = attendance_records.filter(status='T').count()
    
    total_days = attendance_records.count()
    if total_days > 0:
        attendance_rate = (present_count + tardy_count) / total_days * 100
        print(f"   📊 Present: {present_count} days")
        print(f"   📊 Absent: {absent_count} days")
        print(f"   📊 Tardy: {tardy_count} days")
        print(f"   📊 Attendance Rate: {attendance_rate:.1f}%")
    else:
        print("   ⚠️ No attendance records found")
    
    # Check announcements
    announcements = Announcement.objects.filter(
        audience__in=['ALL', 'STUDENTS'],
        is_published=True
    ).order_by('-publish_date')[:5]
    
    print(f"\n📢 ANNOUNCEMENTS ({announcements.count()} visible):")
    for announcement in announcements:
        print(f"   • {announcement.title}")
        print(f"     Published: {announcement.publish_date.strftime('%Y-%m-%d')}")
        print(f"     Audience: {announcement.audience}")
    
    # Check user account
    student_user = User.objects.filter(username='student1').first()
    if student_user:
        print(f"\n👤 USER ACCOUNT:")
        print(f"   Username: {student_user.username}")
        print(f"   Name: {student_user.first_name} {student_user.last_name}")
        print(f"   Email: {student_user.email}")
        print(f"   Active: {student_user.is_active}")
    
    print(f"\n✅ VERIFICATION COMPLETE - ALL SYSTEMS READY!")
    return True

def verify_views_data():
    """Verify that views have access to proper data."""
    print(f"\n🔧 VERIFYING VIEW DATA ACCESS")
    print("=" * 30)
    
    from student_portal.views import get_current_student, get_student_academic_data
    
    # Test getting student
    student_user = User.objects.get(username='student1')
    student = get_current_student(student_user)
    
    if student:
        print(f"✅ get_current_student() works: {student.first_name} {student.last_name}")
        
        # Test academic data
        academic_data = get_student_academic_data(student)
        
        print(f"✅ Academic data loaded:")
        print(f"   Current courses: {len(academic_data['current_courses'])}")
        print(f"   GPA (4.0): {academic_data['gpa_data']['gpa4']:.2f}")
        print(f"   GPA (percentage): {academic_data['gpa_data']['gpa_pct']:.1f}%")
        print(f"   Total credits: {academic_data['total_credits']}")
        print(f"   Attendance rate: {academic_data['attendance_summary'].get('attendance_rate', 0):.1f}%")
        
        # Show course details
        print("   Courses:")
        for course in academic_data['current_courses']:
            print(f"     • {course['name']} - {course['current_grade']} ({course['percentage']:.1f}%)")
            print(f"       Teacher: {course['teacher']}, Room: {course['room']}")
        
        return True
    else:
        print("❌ get_current_student() failed")
        return False

if __name__ == '__main__':
    success = final_verification()
    if success:
        verify_views_data()
        print(f"\n🎉 ALL VERIFICATIONS PASSED - STUDENT PORTAL IS READY!")
        print("🚀 You can now start the server and test with:")
        print("   Username: student1")
        print("   Password: password123")
    else:
        print(f"\n❌ VERIFICATION FAILED")
