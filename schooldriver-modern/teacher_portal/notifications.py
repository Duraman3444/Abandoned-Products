"""
Parent notification system for attendance tracking
"""
from datetime import date, timedelta
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
from academics.models import Attendance, Message
from students.models import Student


def trigger_attendance_notifications():
    """
    Check for attendance issues and send notifications to parents
    This function should be called daily via a management command or cron job
    """
    today = date.today()
    notifications_sent = 0
    
    # Get all attendance records from today that need notifications
    todays_attendance = Attendance.objects.filter(
        date=today,
        parent_notified=False,
        status__in=['A', 'T']  # Absent or Tardy
    ).select_related('enrollment__student')
    
    for attendance in todays_attendance:
        student = attendance.enrollment.student
        
        # Send immediate notification for absence/tardiness
        if send_absence_notification(student, attendance):
            attendance.parent_notified = True
            attendance.parent_notified_at = timezone.now()
            attendance.save()
            notifications_sent += 1
    
    # Check for pattern-based notifications
    pattern_notifications = check_attendance_patterns()
    notifications_sent += pattern_notifications
    
    return notifications_sent


def send_absence_notification(student, attendance):
    """Send immediate notification to parents about absence or tardiness"""
    try:
        # Get parent contact information
        parent_emails = get_parent_emails(student)
        if not parent_emails:
            return False
        
        # Prepare notification content
        subject = f"Attendance Alert - {student.get_full_name()}"
        
        context = {
            'student': student,
            'attendance': attendance,
            'date': attendance.date,
            'status': attendance.get_status_display(),
            'reason': attendance.absence_reason.name if attendance.absence_reason else 'No reason provided',
            'minutes_late': attendance.minutes_late,
            'school_name': getattr(settings, 'SCHOOL_NAME', 'School'),
        }
        
        # Render email templates
        if attendance.status == 'A' or attendance.status == 'E':
            template_name = 'notifications/absence_notification.html'
        else:  # Tardy
            template_name = 'notifications/tardiness_notification.html'
        
        html_message = render_to_string(template_name, context)
        plain_message = render_to_string(template_name.replace('.html', '.txt'), context)
        
        # Send email notification
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@school.edu'),
            recipient_list=parent_emails,
            fail_silently=False,
        )
        
        # Create in-app message record
        create_parent_message(student, subject, plain_message)
        
        return True
        
    except Exception as e:
        # Log error but don't fail the entire process
        print(f"Failed to send attendance notification for {student}: {e}")
        return False


def check_attendance_patterns():
    """Check for concerning attendance patterns and notify parents"""
    from academics.models import Enrollment
    
    notifications_sent = 0
    enrollments = Enrollment.objects.filter(is_active=True).select_related('student')
    
    for enrollment in enrollments:
        student = enrollment.student
        summary = Attendance.get_attendance_summary(enrollment)
        patterns = Attendance.get_attendance_patterns(enrollment)
        
        # Check for chronic absenteeism (less than 90% attendance)
        if summary['attendance_rate'] < 90 and summary['total_days'] >= 10:
            if send_chronic_absenteeism_alert(student, summary, patterns):
                notifications_sent += 1
        
        # Check for consecutive absences (3+ days)
        if patterns['consecutive_absences'] >= 3:
            if send_consecutive_absence_alert(student, patterns):
                notifications_sent += 1
        
        # Check for frequent tardiness pattern
        if patterns['frequent_tardiness'] and summary['total_days'] >= 10:
            if send_tardiness_pattern_alert(student, summary, patterns):
                notifications_sent += 1
    
    return notifications_sent


def send_chronic_absenteeism_alert(student, summary, patterns):
    """Send alert for chronic absenteeism"""
    try:
        parent_emails = get_parent_emails(student)
        if not parent_emails:
            return False
        
        # Check if we've already sent this alert recently (within 7 days)
        recent_alert = Message.objects.filter(
            recipient__in=get_parent_users(student),
            subject__contains="Attendance Concern",
            sent_at__gte=timezone.now() - timedelta(days=7)
        ).exists()
        
        if recent_alert:
            return False
        
        subject = f"Attendance Concern - {student.get_full_name()}"
        
        context = {
            'student': student,
            'summary': summary,
            'patterns': patterns,
            'school_name': getattr(settings, 'SCHOOL_NAME', 'School'),
        }
        
        html_message = render_to_string('notifications/chronic_absenteeism_alert.html', context)
        plain_message = render_to_string('notifications/chronic_absenteeism_alert.txt', context)
        
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@school.edu'),
            recipient_list=parent_emails,
            fail_silently=False,
        )
        
        create_parent_message(student, subject, plain_message)
        return True
        
    except Exception as e:
        print(f"Failed to send chronic absenteeism alert for {student}: {e}")
        return False


def send_consecutive_absence_alert(student, patterns):
    """Send alert for consecutive absences"""
    try:
        parent_emails = get_parent_emails(student)
        if not parent_emails:
            return False
        
        subject = f"Consecutive Absence Alert - {student.get_full_name()}"
        
        context = {
            'student': student,
            'consecutive_days': patterns['consecutive_absences'],
            'school_name': getattr(settings, 'SCHOOL_NAME', 'School'),
        }
        
        html_message = render_to_string('notifications/consecutive_absence_alert.html', context)
        plain_message = render_to_string('notifications/consecutive_absence_alert.txt', context)
        
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@school.edu'),
            recipient_list=parent_emails,
            fail_silently=False,
        )
        
        create_parent_message(student, subject, plain_message)
        return True
        
    except Exception as e:
        print(f"Failed to send consecutive absence alert for {student}: {e}")
        return False


def send_tardiness_pattern_alert(student, summary, patterns):
    """Send alert for frequent tardiness pattern"""
    try:
        parent_emails = get_parent_emails(student)
        if not parent_emails:
            return False
        
        subject = f"Tardiness Pattern Alert - {student.get_full_name()}"
        
        context = {
            'student': student,
            'summary': summary,
            'patterns': patterns,
            'school_name': getattr(settings, 'SCHOOL_NAME', 'School'),
        }
        
        html_message = render_to_string('notifications/tardiness_pattern_alert.html', context)
        plain_message = render_to_string('notifications/tardiness_pattern_alert.txt', context)
        
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@school.edu'),
            recipient_list=parent_emails,
            fail_silently=False,
        )
        
        create_parent_message(student, subject, plain_message)
        return True
        
    except Exception as e:
        print(f"Failed to send tardiness pattern alert for {student}: {e}")
        return False


def get_parent_emails(student):
    """Get list of parent email addresses for a student"""
    emails = []
    
    # Add primary contact email
    if hasattr(student, 'primary_contact') and student.primary_contact.email:
        emails.append(student.primary_contact.email)
    
    # Add secondary contact email
    if hasattr(student, 'secondary_contact') and student.secondary_contact.email:
        emails.append(student.secondary_contact.email)
    
    # Add guardian emails if available
    if hasattr(student, 'guardians'):
        for guardian in student.guardians.all():
            if guardian.email:
                emails.append(guardian.email)
    
    # Remove duplicates and return
    return list(set(emails))


def get_parent_users(student):
    """Get list of parent User objects for a student"""
    from django.contrib.auth.models import User
    parent_emails = get_parent_emails(student)
    return User.objects.filter(email__in=parent_emails)


def create_parent_message(student, subject, content):
    """Create in-app message record for parents"""
    from django.contrib.auth.models import User
    
    # Get system user for sending automated messages
    try:
        system_user = User.objects.get(username='system')
    except User.DoesNotExist:
        # Create system user if it doesn't exist
        system_user = User.objects.create_user(
            username='system',
            email='system@school.edu',
            first_name='School',
            last_name='System'
        )
    
    # Send message to all parent users
    parent_users = get_parent_users(student)
    for parent_user in parent_users:
        Message.objects.create(
            sender=system_user,
            recipient=parent_user,
            subject=subject,
            content=content,
            is_urgent=True
        )


def send_weekly_attendance_summary():
    """Send weekly attendance summary to parents"""
    from datetime import datetime
    from academics.models import Enrollment
    
    # Get date range for the past week
    end_date = date.today()
    start_date = end_date - timedelta(days=7)
    
    enrollments = Enrollment.objects.filter(is_active=True).select_related('student')
    summaries_sent = 0
    
    for enrollment in enrollments:
        student = enrollment.student
        
        # Get weekly attendance data
        weekly_attendance = Attendance.objects.filter(
            enrollment=enrollment,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        if weekly_attendance.exists():
            if send_weekly_summary_email(student, weekly_attendance, start_date, end_date):
                summaries_sent += 1
    
    return summaries_sent


def send_weekly_summary_email(student, attendance_records, start_date, end_date):
    """Send weekly attendance summary email to parents"""
    try:
        parent_emails = get_parent_emails(student)
        if not parent_emails:
            return False
        
        subject = f"Weekly Attendance Summary - {student.get_full_name()}"
        
        # Calculate weekly statistics
        total_days = attendance_records.count()
        present_days = attendance_records.filter(status='P').count()
        absent_days = attendance_records.filter(status__in=['A', 'E']).count()
        tardy_days = attendance_records.filter(status__in=['T', 'L']).count()
        
        weekly_rate = (present_days / total_days * 100) if total_days > 0 else 0
        
        context = {
            'student': student,
            'start_date': start_date,
            'end_date': end_date,
            'attendance_records': attendance_records,
            'total_days': total_days,
            'present_days': present_days,
            'absent_days': absent_days,
            'tardy_days': tardy_days,
            'weekly_rate': weekly_rate,
            'school_name': getattr(settings, 'SCHOOL_NAME', 'School'),
        }
        
        html_message = render_to_string('notifications/weekly_attendance_summary.html', context)
        plain_message = render_to_string('notifications/weekly_attendance_summary.txt', context)
        
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@school.edu'),
            recipient_list=parent_emails,
            fail_silently=False,
        )
        
        return True
        
    except Exception as e:
        print(f"Failed to send weekly summary for {student}: {e}")
        return False
