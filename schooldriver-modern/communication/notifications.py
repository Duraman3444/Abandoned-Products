"""
Automated notification system for various school events
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from academics.models import Assignment, Grade, Attendance, Message, StudentProgressNote
from students.models import Student
from .email_service import email_service

logger = logging.getLogger(__name__)


class AutomatedNotificationService:
    """Service for sending automated notifications"""
    
    def __init__(self):
        self.notifications_sent = []
        
    def check_missing_assignments(self, days_overdue: int = 3) -> Dict[str, Any]:
        """Send notifications for missing assignments"""
        results = {'sent': 0, 'errors': []}
        
        try:
            cutoff_date = timezone.now() - timedelta(days=days_overdue)
            
            # Find overdue assignments without submissions
            overdue_assignments = Assignment.objects.filter(
                due_date__lt=cutoff_date,
                is_published=True
            ).exclude(
                studentsubmission__isnull=False
            ).distinct()
            
            for assignment in overdue_assignments:
                # Get students who haven't submitted
                enrolled_students = assignment.course.enrollments.all()
                submitted_student_ids = assignment.studentsubmission_set.values_list('student_id', flat=True)
                missing_students = enrolled_students.exclude(student_id__in=submitted_student_ids)
                
                for enrollment in missing_students:
                    student = enrollment.student
                    # Get parent users
                    parents = self._get_parent_users(student)
                    
                    if parents:
                        message_content = f"""
                        Dear Parent/Guardian,
                        
                        This is an automated notification that {student.get_full_name()} has not yet submitted the assignment "{assignment.assignment_name}" in {assignment.course.course_name}.
                        
                        Assignment Details:
                        - Due Date: {assignment.due_date.strftime('%B %d, %Y at %I:%M %p')}
                        - Days Overdue: {(timezone.now() - assignment.due_date).days}
                        
                        Please encourage your student to complete and submit this assignment as soon as possible.
                        
                        Best regards,
                        School Administration
                        """
                        
                        # Create message record
                        for parent in parents:
                            Message.objects.create(
                                sender_id=1,  # System user
                                recipient=parent,
                                subject=f"Missing Assignment: {assignment.assignment_name}",
                                content=message_content.strip(),
                                is_urgent=True,
                                student_context=student
                            )
                            results['sent'] += 1
                            
        except Exception as e:
            logger.error(f"Error sending missing assignment notifications: {e}")
            results['errors'].append(str(e))
            
        return results
    
    def check_failing_grades(self, threshold: float = 65.0) -> Dict[str, Any]:
        """Send notifications for failing grades"""
        results = {'sent': 0, 'errors': []}
        
        try:
            # Find recent failing grades
            recent_date = timezone.now() - timedelta(days=7)
            failing_grades = Grade.objects.filter(
                grade__lt=threshold,
                date_taken__gte=recent_date
            ).select_related('student', 'assignment')
            
            for grade in failing_grades:
                parents = self._get_parent_users(grade.student)
                
                if parents:
                    message_content = f"""
                    Dear Parent/Guardian,
                    
                    This is a notification regarding {grade.student.get_full_name()}'s recent academic performance.
                    
                    Grade Details:
                    - Assignment: {grade.assignment.assignment_name}
                    - Course: {grade.assignment.course.course_name}
                    - Grade Received: {grade.grade}%
                    - Date: {grade.date_taken.strftime('%B %d, %Y')}
                    
                    We encourage you to discuss this with your student and reach out to the teacher if additional support is needed.
                    
                    Best regards,
                    School Administration
                    """
                    
                    for parent in parents:
                        Message.objects.create(
                            sender_id=1,  # System user
                            recipient=parent,
                            subject=f"Academic Alert: {grade.assignment.course.course_name}",
                            content=message_content.strip(),
                            is_urgent=True,
                            student_context=grade.student
                        )
                        results['sent'] += 1
                        
        except Exception as e:
            logger.error(f"Error sending failing grade notifications: {e}")
            results['errors'].append(str(e))
            
        return results
    
    def check_excessive_absences(self, absence_threshold: int = 3) -> Dict[str, Any]:
        """Send notifications for excessive absences"""
        results = {'sent': 0, 'errors': []}
        
        try:
            # Find students with excessive absences in the last 2 weeks
            cutoff_date = timezone.now() - timedelta(days=14)
            
            from django.db.models import Count
            students_with_absences = Student.objects.annotate(
                recent_absences=Count(
                    'attendance',
                    filter=Q(
                        attendance__date__gte=cutoff_date,
                        attendance__status__in=['ABSENT', 'UNEXCUSED_ABSENT']
                    )
                )
            ).filter(recent_absences__gte=absence_threshold)
            
            for student in students_with_absences:
                parents = self._get_parent_users(student)
                absence_count = student.recent_absences
                
                if parents:
                    message_content = f"""
                    Dear Parent/Guardian,
                    
                    This is an automated notification regarding {student.get_full_name()}'s recent attendance.
                    
                    Attendance Summary:
                    - Absences in last 14 days: {absence_count}
                    - Attendance threshold: {absence_threshold} absences
                    
                    Consistent attendance is crucial for academic success. Please contact the school if there are any concerns or circumstances affecting your student's attendance.
                    
                    Best regards,
                    School Administration
                    """
                    
                    for parent in parents:
                        Message.objects.create(
                            sender_id=1,  # System user
                            recipient=parent,
                            subject=f"Attendance Alert: {student.get_full_name()}",
                            content=message_content.strip(),
                            is_urgent=True,
                            student_context=student
                        )
                        results['sent'] += 1
                        
        except Exception as e:
            logger.error(f"Error sending attendance notifications: {e}")
            results['errors'].append(str(e))
            
        return results
    
    def check_progress_note_follow_ups(self) -> Dict[str, Any]:
        """Send notifications for progress note follow-ups that are due"""
        results = {'sent': 0, 'errors': []}
        
        try:
            today = timezone.now().date()
            
            # Find progress notes with follow-up dates that are due
            due_follow_ups = StudentProgressNote.objects.filter(
                requires_follow_up=True,
                follow_up_completed=False,
                follow_up_date__lte=today
            ).select_related('student', 'teacher')
            
            for note in due_follow_ups:
                parents = self._get_parent_users(note.student)
                
                message_content = f"""
                Dear Parent/Guardian,
                
                This is a follow-up reminder regarding a previous progress note for {note.student.get_full_name()}.
                
                Original Note Details:
                - Title: {note.title}
                - Type: {note.get_note_type_display()}
                - Teacher: {note.teacher.get_full_name()}
                - Date: {note.created_at.strftime('%B %d, %Y')}
                - Follow-up Due: {note.follow_up_date.strftime('%B %d, %Y')}
                
                Please contact {note.teacher.get_full_name()} to discuss your student's progress and any next steps.
                
                Best regards,
                School Administration
                """
                
                for parent in parents:
                    Message.objects.create(
                        sender_id=1,  # System user
                        recipient=parent,
                        subject=f"Follow-up Reminder: {note.title}",
                        content=message_content.strip(),
                        student_context=note.student
                    )
                    results['sent'] += 1
                    
        except Exception as e:
            logger.error(f"Error sending follow-up notifications: {e}")
            results['errors'].append(str(e))
            
        return results
    
    def run_all_automated_checks(self) -> Dict[str, Any]:
        """Run all automated notification checks"""
        all_results = {
            'missing_assignments': self.check_missing_assignments(),
            'failing_grades': self.check_failing_grades(),
            'excessive_absences': self.check_excessive_absences(),
            'progress_follow_ups': self.check_progress_note_follow_ups(),
        }
        
        total_sent = sum(result['sent'] for result in all_results.values())
        total_errors = []
        for result in all_results.values():
            total_errors.extend(result['errors'])
            
        logger.info(f"Automated notifications sent: {total_sent}")
        if total_errors:
            logger.warning(f"Errors in automated notifications: {total_errors}")
            
        return {
            'total_sent': total_sent,
            'total_errors': len(total_errors),
            'details': all_results
        }
    
    def _get_parent_users(self, student: Student) -> List[User]:
        """Get parent User objects for a student"""
        # This would need to be implemented based on how parent-student relationships are stored
        # For now, return empty list - would need actual parent relationship model
        return []


# Singleton instance
notification_service = AutomatedNotificationService()
