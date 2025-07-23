"""
Analytics calculation services
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from django.db.models import Avg, Count, Q, Min, Max, Sum
from django.utils import timezone
from decimal import Decimal
import json

from academics.models import Course, Grade, Assignment, Attendance
from students.models import Student
from .models import StudentAnalytics, ClassAnalytics, Alert, AlertRule

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Service for calculating and updating analytics data"""
    
    def calculate_student_analytics(self, student: Student) -> StudentAnalytics:
        """Calculate comprehensive analytics for a student"""
        analytics, created = StudentAnalytics.objects.get_or_create(student=student)
        
        try:
            # Calculate GPA
            grades = Grade.objects.filter(student=student)
            if grades.exists():
                analytics.current_gpa = grades.aggregate(avg=Avg('grade'))['avg']
                
                # Semester GPA (last 90 days)
                semester_cutoff = timezone.now() - timedelta(days=90)
                semester_grades = grades.filter(date_taken__gte=semester_cutoff)
                if semester_grades.exists():
                    analytics.semester_gpa = semester_grades.aggregate(avg=Avg('grade'))['avg']
            
            # Calculate attendance metrics
            attendance_records = Attendance.objects.filter(student=student)
            if attendance_records.exists():
                total_days = attendance_records.count()
                present_days = attendance_records.filter(status='PRESENT').count()
                analytics.attendance_rate = Decimal((present_days / total_days) * 100) if total_days > 0 else Decimal(0)
                
                analytics.total_absences = attendance_records.filter(
                    status__in=['ABSENT', 'UNEXCUSED_ABSENT']
                ).count()
                
                analytics.unexcused_absences = attendance_records.filter(
                    status='UNEXCUSED_ABSENT'
                ).count()
            
            # Calculate assignment metrics
            student_assignments = Assignment.objects.filter(
                course__enrollments__student=student
            ).distinct()
            
            analytics.assignments_completed = Grade.objects.filter(
                student=student,
                assignment__in=student_assignments
            ).count()
            
            analytics.assignments_missing = student_assignments.count() - analytics.assignments_completed
            
            if analytics.assignments_completed > 0:
                analytics.average_assignment_score = Grade.objects.filter(
                    student=student,
                    assignment__in=student_assignments
                ).aggregate(avg=Avg('grade'))['avg']
            
            # Calculate progress notes metrics
            from academics.models import StudentProgressNote
            progress_notes = StudentProgressNote.objects.filter(student=student)
            analytics.progress_notes_count = progress_notes.count()
            
            analytics.positive_notes_count = progress_notes.filter(
                note_type='ACHIEVEMENT'
            ).count()
            
            analytics.concerning_notes_count = progress_notes.filter(
                note_type__in=['BEHAVIORAL', 'CONCERN', 'ATTENDANCE']
            ).count()
            
            # Calculate trends (last 12 weeks)
            analytics.grade_trend = self._calculate_grade_trend(student)
            analytics.attendance_trend = self._calculate_attendance_trend(student)
            
            analytics.data_current_as_of = timezone.now()
            analytics.save()
            
        except Exception as e:
            logger.error(f"Error calculating student analytics for {student}: {e}")
            
        return analytics
    
    def calculate_class_analytics(self, course: Course) -> ClassAnalytics:
        """Calculate comprehensive analytics for a class"""
        analytics, created = ClassAnalytics.objects.get_or_create(course=course)
        
        try:
            # Get all students in the course
            enrolled_students = Student.objects.filter(
                enrollments__course=course
            ).distinct()
            
            if not enrolled_students.exists():
                return analytics
            
            # Calculate grade metrics
            course_grades = Grade.objects.filter(
                assignment__course=course
            )
            
            if course_grades.exists():
                grade_stats = course_grades.aggregate(
                    avg=Avg('grade'),
                    min=Min('grade'),
                    max=Max('grade')
                )
                
                analytics.class_average_grade = grade_stats['avg']
                analytics.lowest_grade = grade_stats['min']
                analytics.highest_grade = grade_stats['max']
                
                # Calculate grade distribution
                analytics.grade_distribution = self._calculate_grade_distribution(course_grades)
            
            # Calculate attendance metrics
            course_attendance = Attendance.objects.filter(
                student__in=enrolled_students,
                course=course
            )
            
            if course_attendance.exists():
                total_records = course_attendance.count()
                present_records = course_attendance.filter(status='PRESENT').count()
                analytics.average_attendance_rate = Decimal((present_records / total_records) * 100) if total_records > 0 else Decimal(0)
            
            # Calculate assignment metrics
            course_assignments = Assignment.objects.filter(course=course)
            analytics.total_assignments = course_assignments.count()
            
            if course_assignments.exists():
                total_possible_submissions = course_assignments.count() * enrolled_students.count()
                actual_submissions = Grade.objects.filter(
                    assignment__course=course
                ).count()
                
                analytics.average_completion_rate = Decimal((actual_submissions / total_possible_submissions) * 100) if total_possible_submissions > 0 else Decimal(0)
            
            # Calculate student performance categories
            self._calculate_student_categories(analytics, course, enrolled_students)
            
            # Calculate performance trend
            analytics.performance_trend = self._calculate_class_performance_trend(course)
            
            analytics.data_current_as_of = timezone.now()
            analytics.save()
            
        except Exception as e:
            logger.error(f"Error calculating class analytics for {course}: {e}")
            
        return analytics
    
    def generate_failing_student_alerts(self, threshold: float = 70.0) -> List[Alert]:
        """Generate alerts for students with failing grades"""
        alerts = []
        
        try:
            # Find alert rule for failing grades
            rule = AlertRule.objects.filter(
                alert_type='FAILING_GRADE',
                is_active=True
            ).first()
            
            if not rule:
                logger.warning("No active failing grade alert rule found")
                return alerts
            
            # Find students with recent failing grades
            recent_date = timezone.now() - timedelta(days=30)
            failing_students = Student.objects.filter(
                grade__grade__lt=threshold,
                grade__date_taken__gte=recent_date
            ).distinct()
            
            for student in failing_students:
                # Check if alert already exists for this student
                existing_alert = Alert.objects.filter(
                    rule=rule,
                    student=student,
                    is_resolved=False,
                    created_at__gte=recent_date
                ).first()
                
                if existing_alert:
                    continue
                
                # Calculate failure details
                failing_grades = Grade.objects.filter(
                    student=student,
                    grade__lt=threshold,
                    date_taken__gte=recent_date
                )
                
                avg_failing_grade = failing_grades.aggregate(avg=Avg('grade'))['avg']
                failure_count = failing_grades.count()
                
                alert = Alert.objects.create(
                    rule=rule,
                    student=student,
                    message=f"{student.get_full_name()} has {failure_count} failing grade(s) with an average of {avg_failing_grade:.1f}%",
                    severity=rule.severity,
                    context_data={
                        'failing_grade_count': failure_count,
                        'average_failing_grade': float(avg_failing_grade) if avg_failing_grade else 0,
                        'threshold': threshold,
                        'recent_grades': list(failing_grades.values('assignment__assignment_name', 'grade', 'date_taken'))
                    }
                )
                alerts.append(alert)
                
        except Exception as e:
            logger.error(f"Error generating failing student alerts: {e}")
            
        return alerts
    
    def generate_attendance_alerts(self, absence_threshold: int = 5) -> List[Alert]:
        """Generate alerts for excessive absences"""
        alerts = []
        
        try:
            rule = AlertRule.objects.filter(
                alert_type='EXCESSIVE_ABSENCES',
                is_active=True
            ).first()
            
            if not rule:
                return alerts
            
            # Find students with excessive absences in last 30 days
            recent_date = timezone.now() - timedelta(days=30)
            
            students_with_absences = Student.objects.annotate(
                recent_absences=Count(
                    'attendance',
                    filter=Q(
                        attendance__date__gte=recent_date,
                        attendance__status__in=['ABSENT', 'UNEXCUSED_ABSENT']
                    )
                )
            ).filter(recent_absences__gte=absence_threshold)
            
            for student in students_with_absences:
                # Check for existing unresolved alert
                existing_alert = Alert.objects.filter(
                    rule=rule,
                    student=student,
                    is_resolved=False,
                    created_at__gte=recent_date
                ).first()
                
                if existing_alert:
                    continue
                
                absence_count = student.recent_absences
                
                alert = Alert.objects.create(
                    rule=rule,
                    student=student,
                    message=f"{student.get_full_name()} has {absence_count} absences in the last 30 days",
                    severity=rule.severity,
                    context_data={
                        'absence_count': absence_count,
                        'threshold': absence_threshold,
                        'period_days': 30
                    }
                )
                alerts.append(alert)
                
        except Exception as e:
            logger.error(f"Error generating attendance alerts: {e}")
            
        return alerts
    
    def _calculate_grade_trend(self, student: Student) -> List[Dict]:
        """Calculate 12-week grade trend for student"""
        trend = []
        
        try:
            # Get grades from last 12 weeks
            start_date = timezone.now() - timedelta(weeks=12)
            grades = Grade.objects.filter(
                student=student,
                date_taken__gte=start_date
            ).order_by('date_taken')
            
            # Group by week
            for week in range(12):
                week_start = start_date + timedelta(weeks=week)
                week_end = week_start + timedelta(days=7)
                
                week_grades = grades.filter(
                    date_taken__gte=week_start,
                    date_taken__lt=week_end
                )
                
                if week_grades.exists():
                    avg_grade = week_grades.aggregate(avg=Avg('grade'))['avg']
                    trend.append({
                        'week': week + 1,
                        'average_grade': float(avg_grade) if avg_grade else 0,
                        'assignment_count': week_grades.count()
                    })
                else:
                    trend.append({
                        'week': week + 1,
                        'average_grade': None,
                        'assignment_count': 0
                    })
                    
        except Exception as e:
            logger.error(f"Error calculating grade trend for {student}: {e}")
            
        return trend
    
    def _calculate_attendance_trend(self, student: Student) -> List[Dict]:
        """Calculate 12-week attendance trend for student"""
        trend = []
        
        try:
            start_date = timezone.now() - timedelta(weeks=12)
            
            for week in range(12):
                week_start = start_date + timedelta(weeks=week)
                week_end = week_start + timedelta(days=7)
                
                week_attendance = Attendance.objects.filter(
                    student=student,
                    date__gte=week_start.date(),
                    date__lt=week_end.date()
                )
                
                total_days = week_attendance.count()
                present_days = week_attendance.filter(status='PRESENT').count()
                
                trend.append({
                    'week': week + 1,
                    'attendance_rate': (present_days / total_days * 100) if total_days > 0 else 0,
                    'total_days': total_days,
                    'present_days': present_days
                })
                
        except Exception as e:
            logger.error(f"Error calculating attendance trend for {student}: {e}")
            
        return trend
    
    def _calculate_grade_distribution(self, grades) -> Dict[str, int]:
        """Calculate grade distribution for a set of grades"""
        distribution = {'A': 0, 'B': 0, 'C': 0, 'D': 0, 'F': 0}
        
        for grade in grades:
            if grade.grade >= 90:
                distribution['A'] += 1
            elif grade.grade >= 80:
                distribution['B'] += 1
            elif grade.grade >= 70:
                distribution['C'] += 1
            elif grade.grade >= 60:
                distribution['D'] += 1
            else:
                distribution['F'] += 1
                
        return distribution
    
    def _calculate_student_categories(self, analytics: ClassAnalytics, course: Course, students):
        """Calculate student performance categories"""
        analytics.students_excelling = 0
        analytics.students_proficient = 0
        analytics.students_developing = 0
        analytics.students_struggling = 0
        
        for student in students:
            avg_grade = Grade.objects.filter(
                student=student,
                assignment__course=course
            ).aggregate(avg=Avg('grade'))['avg']
            
            if avg_grade:
                if avg_grade >= 90:
                    analytics.students_excelling += 1
                elif avg_grade >= 80:
                    analytics.students_proficient += 1
                elif avg_grade >= 70:
                    analytics.students_developing += 1
                else:
                    analytics.students_struggling += 1
    
    def _calculate_class_performance_trend(self, course: Course) -> List[Dict]:
        """Calculate class performance trend over 12 weeks"""
        trend = []
        
        try:
            start_date = timezone.now() - timedelta(weeks=12)
            
            for week in range(12):
                week_start = start_date + timedelta(weeks=week)
                week_end = week_start + timedelta(days=7)
                
                week_grades = Grade.objects.filter(
                    assignment__course=course,
                    date_taken__gte=week_start,
                    date_taken__lt=week_end
                )
                
                if week_grades.exists():
                    avg_grade = week_grades.aggregate(avg=Avg('grade'))['avg']
                    trend.append({
                        'week': week + 1,
                        'average_grade': float(avg_grade) if avg_grade else 0,
                        'submission_count': week_grades.count()
                    })
                else:
                    trend.append({
                        'week': week + 1,
                        'average_grade': None,
                        'submission_count': 0
                    })
                    
        except Exception as e:
            logger.error(f"Error calculating class performance trend for {course}: {e}")
            
        return trend


# Singleton instance
analytics_service = AnalyticsService()
