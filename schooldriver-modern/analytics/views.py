"""
Analytics views for teachers and administrators
"""
import json
from datetime import datetime, timedelta
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from django.http import JsonResponse
from django.db.models import Q, Avg, Count
from django.utils import timezone

from core.decorators import role_required
from academics.models import Course, Grade, Assignment, Attendance
from students.models import Student, Enrollment
from .models import StudentAnalytics, ClassAnalytics, Alert, ReportTemplate
from .services import analytics_service


@method_decorator([login_required, role_required(["Staff", "Admin"])], name='dispatch')
class ClassPerformanceView(TemplateView):
    """Class performance overview dashboard"""
    template_name = 'analytics/class_performance.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get teacher's courses
        if self.request.user.groups.filter(name='Staff').exists():
            courses = Course.objects.filter(teacher=self.request.user)
        else:
            courses = Course.objects.all()
        
        # Calculate analytics for each course
        course_analytics = []
        for course in courses:
            analytics = analytics_service.calculate_class_analytics(course)
            
            # Get enrollment count
            enrollment_count = Enrollment.objects.filter(course=course).count()
            
            course_analytics.append({
                'course': course,
                'analytics': analytics,
                'enrollment_count': enrollment_count,
            })
        
        context.update({
            'course_analytics': course_analytics,
            'total_courses': courses.count(),
        })
        
        return context


@method_decorator([login_required, role_required(["Staff", "Admin"])], name='dispatch')
class StudentProgressView(TemplateView):
    """Individual student progress tracking"""
    template_name = 'analytics/student_progress.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get students for teacher's courses
        if self.request.user.groups.filter(name='Staff').exists():
            teacher_courses = Course.objects.filter(teacher=self.request.user)
            students = Student.objects.filter(
                enrollments__course__in=teacher_courses
            ).distinct()
        else:
            students = Student.objects.all()
        
        # Calculate analytics for each student
        student_analytics = []
        for student in students[:50]:  # Limit for performance
            analytics = analytics_service.calculate_student_analytics(student)
            
            # Get recent grades
            recent_grades = Grade.objects.filter(
                student=student
            ).order_by('-date_taken')[:5]
            
            student_analytics.append({
                'student': student,
                'analytics': analytics,
                'recent_grades': recent_grades,
            })
        
        context.update({
            'student_analytics': student_analytics,
            'total_students': students.count(),
        })
        
        return context


@method_decorator([login_required, role_required(["Staff", "Admin"])], name='dispatch')
class GradeDistributionView(TemplateView):
    """Grade distribution analytics"""
    template_name = 'analytics/grade_distribution.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get teacher's courses or all courses
        if self.request.user.groups.filter(name='Staff').exists():
            courses = Course.objects.filter(teacher=self.request.user)
        else:
            courses = Course.objects.all()
        
        # Calculate grade distribution for each course
        course_distributions = []
        for course in courses:
            grades = Grade.objects.filter(assignment__course=course)
            
            if grades.exists():
                distribution = {
                    'A (90-100)': grades.filter(grade__gte=90).count(),
                    'B (80-89)': grades.filter(grade__gte=80, grade__lt=90).count(),
                    'C (70-79)': grades.filter(grade__gte=70, grade__lt=80).count(),
                    'D (60-69)': grades.filter(grade__gte=60, grade__lt=70).count(),
                    'F (0-59)': grades.filter(grade__lt=60).count(),
                }
                
                average_grade = grades.aggregate(avg=Avg('grade'))['avg']
                
                course_distributions.append({
                    'course': course,
                    'distribution': distribution,
                    'average_grade': average_grade,
                    'total_grades': grades.count(),
                })
        
        context.update({
            'course_distributions': course_distributions,
        })
        
        return context


@method_decorator([login_required, role_required(["Staff", "Admin"])], name='dispatch')
class AttendanceTrendsView(TemplateView):
    """Attendance trend analysis"""
    template_name = 'analytics/attendance_trends.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get attendance data for the last 30 days
        start_date = timezone.now() - timedelta(days=30)
        
        # Daily attendance rates
        daily_rates = []
        for i in range(30):
            date = start_date + timedelta(days=i)
            
            day_attendance = Attendance.objects.filter(date=date.date())
            total_records = day_attendance.count()
            present_records = day_attendance.filter(status='PRESENT').count()
            
            rate = (present_records / total_records * 100) if total_records > 0 else 0
            
            daily_rates.append({
                'date': date.date(),
                'attendance_rate': rate,
                'total_students': total_records,
                'present_students': present_records,
            })
        
        # Students with concerning attendance
        concerning_students = Student.objects.annotate(
            recent_absences=Count(
                'attendance',
                filter=Q(
                    attendance__date__gte=start_date.date(),
                    attendance__status__in=['ABSENT', 'UNEXCUSED_ABSENT']
                )
            )
        ).filter(recent_absences__gte=5).order_by('-recent_absences')
        
        context.update({
            'daily_rates': daily_rates,
            'concerning_students': concerning_students[:20],
        })
        
        return context


@method_decorator([login_required, role_required(["Staff", "Admin"])], name='dispatch')
class FailingStudentAlertsView(TemplateView):
    """Failing student alerts dashboard"""
    template_name = 'analytics/failing_alerts.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Generate fresh alerts
        failing_alerts = analytics_service.generate_failing_student_alerts()
        attendance_alerts = analytics_service.generate_attendance_alerts()
        
        # Get recent unresolved alerts
        recent_alerts = Alert.objects.filter(
            is_resolved=False,
            created_at__gte=timezone.now() - timedelta(days=30)
        ).order_by('-created_at')
        
        # Get alert summary by type
        alert_summary = {}
        for alert in recent_alerts:
            alert_type = alert.rule.alert_type
            if alert_type not in alert_summary:
                alert_summary[alert_type] = {'count': 0, 'critical': 0}
            alert_summary[alert_type]['count'] += 1
            if alert.severity == 'CRITICAL':
                alert_summary[alert_type]['critical'] += 1
        
        context.update({
            'recent_alerts': recent_alerts[:50],
            'alert_summary': alert_summary,
            'failing_alerts_count': len(failing_alerts),
            'attendance_alerts_count': len(attendance_alerts),
        })
        
        return context


@method_decorator([login_required, role_required(["Staff", "Admin"])], name='dispatch')
class CustomReportBuilderView(TemplateView):
    """Custom report builder interface"""
    template_name = 'analytics/report_builder.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get user's saved reports
        user_reports = ReportTemplate.objects.filter(
            created_by=self.request.user
        )
        
        # Get shared reports
        shared_reports = ReportTemplate.objects.filter(
            is_shared=True,
            is_active=True
        ).exclude(created_by=self.request.user)
        
        context.update({
            'user_reports': user_reports,
            'shared_reports': shared_reports,
        })
        
        return context


@login_required
@role_required(["Staff", "Admin"])
def api_student_analytics(request, student_id):
    """API endpoint for student analytics data"""
    student = get_object_or_404(Student, id=student_id)
    analytics = analytics_service.calculate_student_analytics(student)
    
    data = {
        'student_name': student.get_full_name(),
        'current_gpa': float(analytics.current_gpa) if analytics.current_gpa else None,
        'semester_gpa': float(analytics.semester_gpa) if analytics.semester_gpa else None,
        'attendance_rate': float(analytics.attendance_rate) if analytics.attendance_rate else None,
        'assignments_completed': analytics.assignments_completed,
        'assignments_missing': analytics.assignments_missing,
        'grade_trend': analytics.grade_trend,
        'attendance_trend': analytics.attendance_trend,
    }
    
    return JsonResponse(data)


@login_required
@role_required(["Staff", "Admin"])
def api_class_analytics(request, course_id):
    """API endpoint for class analytics data"""
    course = get_object_or_404(Course, id=course_id)
    analytics = analytics_service.calculate_class_analytics(course)
    
    data = {
        'course_name': course.course_name,
        'class_average_grade': float(analytics.class_average_grade) if analytics.class_average_grade else None,
        'grade_distribution': analytics.grade_distribution,
        'attendance_rate': float(analytics.average_attendance_rate) if analytics.average_attendance_rate else None,
        'students_excelling': analytics.students_excelling,
        'students_proficient': analytics.students_proficient,
        'students_developing': analytics.students_developing,
        'students_struggling': analytics.students_struggling,
        'performance_trend': analytics.performance_trend,
    }
    
    return JsonResponse(data)


@login_required
@role_required(["Staff", "Admin"])
def resolve_alert(request, alert_id):
    """Resolve an alert"""
    if request.method == 'POST':
        alert = get_object_or_404(Alert, id=alert_id)
        resolution_notes = request.POST.get('resolution_notes', '')
        
        alert.is_resolved = True
        alert.resolved_at = timezone.now()
        alert.resolved_by = request.user
        alert.resolution_notes = resolution_notes
        alert.save()
        
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})
