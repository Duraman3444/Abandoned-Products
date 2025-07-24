from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from django.db.models import Count, Avg, Q
from django.db import models
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, CreateView, UpdateView
from django.utils import timezone
from django.urls import reverse_lazy, reverse
from datetime import datetime, date
import csv
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False
from authentication.decorators import role_required
from academics.models import CourseSection, Assignment, Enrollment, Grade, AssignmentCategory, GradeHistory
from students.models import Student, SchoolYear
from .forms import AssignmentForm, GradeFormSet, BulkGradeForm, GradebookFilterForm, QuickGradeForm, ProgressReportForm


@method_decorator([login_required, role_required(["Staff", "Admin"])], name='dispatch')
class TeacherDashboardView(TemplateView):
    template_name = 'teacher_portal/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get teacher's sections
        sections = user.taught_sections.filter(is_active=True)
        
        # Get current section (from URL param or first section)
        section_id = self.request.GET.get('section')
        if section_id:
            current_section = get_object_or_404(sections, id=section_id)
        else:
            current_section = sections.first() if sections.exists() else None
        
        # Dashboard statistics
        stats = {}
        if current_section:
            enrollments = current_section.enrollments.filter(is_active=True)
            assignments = current_section.assignments.filter(is_published=True)
            
            stats = {
                'total_students': enrollments.count(),
                'total_assignments': assignments.count(),
                'pending_grades': assignments.filter(
                    grades__isnull=True
                ).count(),
                'average_grade': enrollments.filter(
                    final_grade__isnull=False
                ).aggregate(avg=Avg('final_grade'))['avg'] or 0,
            }
            
            # Recent assignments
            recent_assignments = assignments.order_by('-due_date')[:5]
            context['recent_assignments'] = recent_assignments
            
            # Recent enrollments (students)
            recent_students = enrollments.order_by('-enrollment_date')[:10]
            context['recent_students'] = recent_students
        
        context.update({
            'sections': sections,
            'current_section': current_section,
            'stats': stats,
            'show_section_selector': sections.count() > 1,
        })
        
        return context


@method_decorator([login_required, role_required(["Staff", "Admin"])], name='dispatch')
class TeacherGradebookView(TemplateView):
    template_name = 'teacher_portal/gradebook.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get teacher's sections
        sections = user.taught_sections.filter(is_active=True)
        
        # Get current section
        section_id = self.request.GET.get('section')
        if section_id:
            current_section = get_object_or_404(sections, id=section_id)
        else:
            current_section = sections.first() if sections.exists() else None
        
        if current_section:
            # Get filter parameters
            filter_form = GradebookFilterForm(self.request.GET)
            
            # Get enrollments and assignments for gradebook
            enrollments = current_section.enrollments.filter(is_active=True).select_related('student')
            assignments_query = current_section.assignments.all()
            
            # Apply filters
            if filter_form.is_valid():
                category = filter_form.cleaned_data.get('category')
                published_only = filter_form.cleaned_data.get('published_only', True)
                
                if category:
                    assignments_query = assignments_query.filter(category=category)
                if published_only:
                    assignments_query = assignments_query.filter(is_published=True)
            else:
                assignments_query = assignments_query.filter(is_published=True)
            
            assignments = assignments_query.order_by('due_date')
            
            # Create gradebook data structure
            gradebook_data = []
            for enrollment in enrollments:
                student_data = {
                    'enrollment': enrollment,
                    'student': enrollment.student,
                    'grades': {},
                    'final_grade': enrollment.calculate_grade(),
                    'final_letter': enrollment.get_letter_grade()
                }
                
                # Get grades for each assignment
                for assignment in assignments:
                    try:
                        grade = Grade.objects.get(enrollment=enrollment, assignment=assignment)
                    except Grade.DoesNotExist:
                        grade = Grade(enrollment=enrollment, assignment=assignment)
                    student_data['grades'][assignment.id] = grade
                
                gradebook_data.append(student_data)
            
            context.update({
                'enrollments': enrollments,
                'assignments': assignments,
                'gradebook_data': gradebook_data,
                'filter_form': filter_form,
                'categories': AssignmentCategory.objects.filter(is_active=True),
            })
        
        context.update({
            'sections': sections,
            'current_section': current_section,
            'show_section_selector': sections.count() > 1,
        })
        
        return context


@method_decorator([login_required, role_required(["Staff", "Admin"])], name='dispatch')
class TeacherAttendanceView(TemplateView):
    template_name = 'teacher_portal/attendance.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get teacher's sections
        sections = user.taught_sections.filter(is_active=True)
        
        # Get current section
        section_id = self.request.GET.get('section')
        if section_id:
            current_section = get_object_or_404(sections, id=section_id)
        else:
            current_section = sections.first() if sections.exists() else None
        
        # Get attendance date (default to today)
        attendance_date_str = self.request.GET.get('date')
        if attendance_date_str:
            try:
                attendance_date = datetime.strptime(attendance_date_str, '%Y-%m-%d').date()
            except ValueError:
                attendance_date = date.today()
        else:
            attendance_date = date.today()
        
        if current_section:
            # Get active enrollments for attendance
            from academics.models import Attendance, AbsenceReason
            enrollments = current_section.enrollments.filter(is_active=True).select_related('student')
            
            # Get or create attendance records for the date
            attendance_data = []
            for enrollment in enrollments:
                try:
                    attendance = Attendance.objects.get(
                        enrollment=enrollment,
                        date=attendance_date
                    )
                except Attendance.DoesNotExist:
                    attendance = Attendance(
                        enrollment=enrollment,
                        date=attendance_date,
                        status='P'  # Default to present
                    )
                
                # Get attendance summary and patterns
                summary = Attendance.get_attendance_summary(enrollment)
                patterns = Attendance.get_attendance_patterns(enrollment)
                
                attendance_data.append({
                    'enrollment': enrollment,
                    'student': enrollment.student,
                    'attendance': attendance,
                    'summary': summary,
                    'patterns': patterns,
                    'has_concerns': patterns['consecutive_absences'] >= 3 or 
                                  summary['attendance_rate'] < 90 or
                                  patterns['frequent_tardiness']
                })
            
            context.update({
                'enrollments': enrollments,
                'attendance_data': attendance_data,
                'attendance_date': attendance_date,
                'current_date': attendance_date,
                'absence_reasons': AbsenceReason.objects.filter(is_active=True),
            })
        
        context.update({
            'sections': sections,
            'current_section': current_section,
            'show_section_selector': sections.count() > 1,
            'today': date.today(),
        })
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle attendance submission"""
        from academics.models import Attendance, AbsenceReason
        
        action = request.POST.get('action')
        section_id = request.POST.get('section_id')
        attendance_date_str = request.POST.get('date')
        
        if not all([section_id, attendance_date_str]):
            messages.error(request, 'Missing required information')
            return redirect('teacher_portal:teacher_attendance')
        
        try:
            attendance_date = datetime.strptime(attendance_date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, 'Invalid date format')
            return redirect('teacher_portal:teacher_attendance')
        
        section = get_object_or_404(
            request.user.taught_sections.filter(is_active=True),
            id=section_id
        )
        
        if action == 'bulk_action':
            return self.handle_bulk_action(request, section, attendance_date)
        elif action == 'save_attendance':
            return self.handle_individual_attendance(request, section, attendance_date)
        else:
            messages.error(request, 'Invalid action')
            return redirect('teacher_portal:teacher_attendance')
    
    def handle_bulk_action(self, request, section, attendance_date):
        """Handle bulk attendance actions"""
        from academics.models import Attendance, AbsenceReason
        
        bulk_action = request.POST.get('bulk_action')
        absence_reason_id = request.POST.get('absence_reason')
        
        enrollments = section.enrollments.filter(is_active=True)
        
        if bulk_action == 'mark_all_present':
            for enrollment in enrollments:
                Attendance.objects.update_or_create(
                    enrollment=enrollment,
                    date=attendance_date,
                    defaults={
                        'status': 'P',
                        'absence_reason': None,
                        'minutes_late': None,
                        'recorded_by': request.user,
                    }
                )
            messages.success(request, f'Marked all students present for {attendance_date}')
            
        elif bulk_action == 'mark_all_absent':
            absence_reason = None
            if absence_reason_id:
                absence_reason = get_object_or_404(AbsenceReason, id=absence_reason_id)
            
            for enrollment in enrollments:
                Attendance.objects.update_or_create(
                    enrollment=enrollment,
                    date=attendance_date,
                    defaults={
                        'status': 'A',
                        'absence_reason': absence_reason,
                        'recorded_by': request.user,
                    }
                )
            messages.success(request, f'Marked all students absent for {attendance_date}')
            
        elif bulk_action == 'copy_previous_day':
            from datetime import timedelta
            previous_date = attendance_date - timedelta(days=1)
            copied_count = 0
            
            for enrollment in enrollments:
                try:
                    previous_attendance = Attendance.objects.get(
                        enrollment=enrollment,
                        date=previous_date
                    )
                    Attendance.objects.update_or_create(
                        enrollment=enrollment,
                        date=attendance_date,
                        defaults={
                            'status': previous_attendance.status,
                            'absence_reason': previous_attendance.absence_reason,
                            'minutes_late': previous_attendance.minutes_late,
                            'recorded_by': request.user,
                        }
                    )
                    copied_count += 1
                except Attendance.DoesNotExist:
                    pass
            
            messages.success(request, f'Copied attendance for {copied_count} students from {previous_date}')
        
        return redirect(f"{reverse('teacher_portal:teacher_attendance')}?section={section.id}&date={attendance_date}")
    
    def handle_individual_attendance(self, request, section, attendance_date):
        """Handle individual attendance records"""
        from academics.models import Attendance, AbsenceReason
        
        enrollments = section.enrollments.filter(is_active=True)
        updated_count = 0
        
        for enrollment in enrollments:
            status = request.POST.get(f'status_{enrollment.id}')
            absence_reason_id = request.POST.get(f'absence_reason_{enrollment.id}')
            minutes_late = request.POST.get(f'minutes_late_{enrollment.id}')
            notes = request.POST.get(f'notes_{enrollment.id}', '')
            
            if status:
                absence_reason = None
                if absence_reason_id and status in ['A', 'E']:
                    absence_reason = get_object_or_404(AbsenceReason, id=absence_reason_id)
                
                minutes_late_value = None
                if minutes_late and status in ['T', 'L']:
                    try:
                        minutes_late_value = int(minutes_late)
                    except ValueError:
                        pass
                
                Attendance.objects.update_or_create(
                    enrollment=enrollment,
                    date=attendance_date,
                    defaults={
                        'status': status,
                        'absence_reason': absence_reason,
                        'minutes_late': minutes_late_value,
                        'notes': notes,
                        'recorded_by': request.user,
                    }
                )
                updated_count += 1
        
        messages.success(request, f'Updated attendance for {updated_count} students')
        return redirect(f"{reverse('teacher_portal:teacher_attendance')}?section={section.id}&date={attendance_date}")


@login_required
@role_required(["Staff", "Admin"])
def teacher_section_switch(request):
    """AJAX endpoint for switching between teacher sections"""
    section_id = request.GET.get('section_id')
    if not section_id:
        return JsonResponse({'error': 'Section ID required'}, status=400)
    
    try:
        section = get_object_or_404(
            request.user.taught_sections.filter(is_active=True),
            id=section_id
        )
        
        return JsonResponse({
            'success': True,
            'section': {
                'id': section.id,
                'name': f"{section.course.name} - Section {section.section_name}",
                'student_count': section.enrollments.filter(is_active=True).count(),
            }
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@role_required(["Staff", "Admin"])
def ajax_save_grade(request):
    """AJAX endpoint for saving individual grades"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        enrollment_id = request.POST.get('enrollment_id')
        assignment_id = request.POST.get('assignment_id')
        points_earned = request.POST.get('points_earned')
        
        if not all([enrollment_id, assignment_id]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        # Get objects
        enrollment = get_object_or_404(Enrollment, id=enrollment_id)
        assignment = get_object_or_404(Assignment, id=assignment_id)
        
        # Verify teacher has access to this section
        if assignment.section.teacher != request.user:
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        # Get or create grade
        grade, created = Grade.objects.get_or_create(
            enrollment=enrollment,
            assignment=assignment,
            defaults={'graded_by': request.user}
        )
        
        # Update grade
        if points_earned:
            try:
                grade.points_earned = float(points_earned)
                if grade.points_earned < 0 or grade.points_earned > assignment.max_points:
                    return JsonResponse({'error': 'Invalid points value'}, status=400)
            except ValueError:
                return JsonResponse({'error': 'Invalid points format'}, status=400)
        else:
            grade.points_earned = None
            
        grade.graded_by = request.user
        grade.graded_date = timezone.now()
        grade.save()
        
        # Update enrollment final grade
        enrollment.update_final_grade()
        
        return JsonResponse({
            'success': True,
            'percentage': float(grade.percentage) if grade.percentage else None,
            'letter_grade': grade.letter_grade,
            'final_grade': float(enrollment.final_percentage) if enrollment.final_percentage else None,
            'final_letter': enrollment.final_grade
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@method_decorator([login_required, role_required(["Staff", "Admin"])], name='dispatch')
class CreateAssignmentView(CreateView):
    model = Assignment
    template_name = 'teacher_portal/create_assignment.html'
    
    def get_form_class(self):
        from .assignment_forms import EnhancedAssignmentForm
        return EnhancedAssignmentForm
    
    def get_success_url(self):
        return reverse('teacher_portal:teacher_assignments') + f'?section={self.object.section.id}'
    
    def form_valid(self, form):
        # Get section from URL or form
        section_id = self.request.GET.get('section') or self.request.POST.get('section')
        if section_id:
            section = get_object_or_404(
                self.request.user.taught_sections.filter(is_active=True),
                id=section_id
            )
            form.instance.section = section
            
        messages.success(self.request, f'Assignment "{form.instance.name}" created successfully!')
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        section_id = self.request.GET.get('section')
        if section_id:
            section = get_object_or_404(
                self.request.user.taught_sections.filter(is_active=True),
                id=section_id
            )
            kwargs['section'] = section
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        section_id = self.request.GET.get('section')
        if section_id:
            context['current_section'] = get_object_or_404(
                self.request.user.taught_sections.filter(is_active=True),
                id=section_id
            )
        return context


@login_required
@role_required(["Staff", "Admin"])
def export_grades(request):
    """Export grades to CSV or PDF"""
    section_id = request.GET.get('section')
    format_type = request.GET.get('format', 'csv')
    
    if not section_id:
        messages.error(request, 'Section required for export')
        return redirect('teacher_portal:teacher_gradebook')
    
    section = get_object_or_404(
        request.user.taught_sections.filter(is_active=True),
        id=section_id
    )
    
    if format_type == 'csv':
        return export_grades_csv(section)
    elif format_type == 'pdf':
        return export_grades_pdf(section)
    else:
        messages.error(request, 'Invalid export format')
        return redirect('teacher_portal:teacher_gradebook')


def export_grades_csv(section):
    """Export grades to CSV format"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{section.course.course_code}_grades.csv"'
    
    writer = csv.writer(response)
    
    # Get data
    enrollments = section.enrollments.filter(is_active=True).select_related('student')
    assignments = section.assignments.filter(is_published=True).order_by('due_date')
    
    # Write header
    header = ['Student ID', 'Student Name']
    for assignment in assignments:
        header.append(f"{assignment.name} ({assignment.max_points}pts)")
    header.extend(['Final Grade', 'Final Letter'])
    writer.writerow(header)
    
    # Write data
    for enrollment in enrollments:
        row = [enrollment.student.student_id, enrollment.student.full_name]
        
        for assignment in assignments:
            try:
                grade = Grade.objects.get(enrollment=enrollment, assignment=assignment)
                row.append(grade.points_earned or '')
            except Grade.DoesNotExist:
                row.append('')
        
        row.extend([
            enrollment.final_percentage or '',
            enrollment.final_grade or ''
        ])
        writer.writerow(row)
    
    return response


def export_grades_pdf(section):
    """Export grades to PDF format"""
    if not HAS_REPORTLAB:
        messages.error(request, 'PDF export not available - reportlab not installed')
        return redirect('teacher_portal:teacher_gradebook')
        
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{section.course.course_code}_grades.pdf"'
    
    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter
    
    # Title
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 50, f"Grade Report: {section.course.name}")
    p.drawString(50, height - 70, f"Section {section.section_name} - {section.school_year}")
    
    # Basic implementation - can be enhanced with better formatting
    p.setFont("Helvetica", 10)
    y_position = height - 120
    
    enrollments = section.enrollments.filter(is_active=True).select_related('student')
    
    for enrollment in enrollments:
        if y_position < 100:  # Start new page
            p.showPage()
            y_position = height - 50
            
        student_text = f"{enrollment.student.get_full_name()}: {enrollment.final_percentage or 'N/A'}% ({enrollment.final_grade or 'N/A'})"
        p.drawString(50, y_position, student_text)
        y_position -= 20
    
    p.save()
    return response


@login_required
@role_required(["Staff", "Admin"])
def ajax_save_attendance(request):
    """AJAX endpoint for saving individual attendance records"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    try:
        from academics.models import Attendance, AbsenceReason
        
        enrollment_id = request.POST.get('enrollment_id')
        attendance_date_str = request.POST.get('date')
        status = request.POST.get('status')
        
        if not all([enrollment_id, attendance_date_str, status]):
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        # Parse date
        try:
            attendance_date = datetime.strptime(attendance_date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'error': 'Invalid date format'}, status=400)
        
        # Get enrollment and verify teacher has access
        enrollment = get_object_or_404(Enrollment, id=enrollment_id)
        if enrollment.section.teacher != request.user:
            return JsonResponse({'error': 'Access denied'}, status=403)
        
        # Get optional fields
        absence_reason_id = request.POST.get('absence_reason')
        minutes_late = request.POST.get('minutes_late')
        notes = request.POST.get('notes', '')
        
        # Process absence reason
        absence_reason = None
        if absence_reason_id and status in ['A', 'E']:
            absence_reason = get_object_or_404(AbsenceReason, id=absence_reason_id)
        
        # Process minutes late
        minutes_late_value = None
        if minutes_late and status in ['T', 'L']:
            try:
                minutes_late_value = int(minutes_late)
            except ValueError:
                pass
        
        # Update or create attendance record
        attendance, created = Attendance.objects.update_or_create(
            enrollment=enrollment,
            date=attendance_date,
            defaults={
                'status': status,
                'absence_reason': absence_reason,
                'minutes_late': minutes_late_value,
                'notes': notes,
                'recorded_by': request.user,
            }
        )
        
        # Trigger parent notification if needed
        if status in ['A', 'T'] and not attendance.parent_notified:
            # TODO: Implement parent notification
            pass
        
        # Get updated summary
        summary = Attendance.get_attendance_summary(enrollment)
        
        return JsonResponse({
            'success': True,
            'attendance_rate': summary['attendance_rate'],
            'present_days': summary['present_days'],
            'total_days': summary['total_days'],
            'status_display': attendance.get_status_display()
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@role_required(["Staff", "Admin"])
def attendance_reports(request):
    """Generate attendance reports"""
    from .attendance_forms import AttendanceReportForm
    from academics.models import Attendance, AbsenceReason
    
    section_id = request.GET.get('section')
    if not section_id:
        messages.error(request, 'Section required for reports')
        return redirect('teacher_portal:teacher_attendance')
    
    section = get_object_or_404(
        request.user.taught_sections.filter(is_active=True),
        id=section_id
    )
    
    if request.method == 'POST':
        form = AttendanceReportForm(request.POST, section=section)
        if form.is_valid():
            return generate_attendance_report(request, section, form.cleaned_data)
        else:
            # Add form errors to messages for debugging
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
            messages.error(request, "Please fix the form errors and try again.")
    else:
        form = AttendanceReportForm(section=section)
    
    return render(request, 'teacher_portal/attendance_reports.html', {
        'form': form,
        'section': section,
    })


def generate_attendance_report(request, section, report_data):
    """Generate specific attendance report"""
    from academics.models import Attendance
    
    try:
        report_type = report_data['report_type']
        format_type = report_data['format']
        date_start = report_data['date_start']
        date_end = report_data['date_end']
        
        # Get attendance data
        attendance_records = Attendance.objects.filter(
            enrollment__section=section,
            date__gte=date_start,
            date__lte=date_end
        ).select_related('enrollment__student', 'absence_reason')
        
        # Check if there are any records
        if not attendance_records.exists():
            messages.warning(request, f'No attendance records found for the selected date range ({date_start} to {date_end}). Please check if attendance has been recorded for this section.')
            return redirect(f"{reverse('teacher_portal:attendance_reports')}?section={section.id}")
        
        if report_type == 'daily':
            return generate_daily_report(section, attendance_records, format_type)
        elif report_type == 'student':
            return generate_student_report(section, attendance_records, format_type)
        elif report_type == 'patterns':
            return generate_patterns_report(section, attendance_records, format_type)
        elif report_type == 'chronic':
            return generate_chronic_report(section, attendance_records, format_type)
        elif report_type == 'tardiness':
            return generate_tardiness_report(section, attendance_records, format_type)
        
        messages.error(request, 'Invalid report type')
        return redirect('teacher_portal:attendance_reports', section=section.id)
        
    except Exception as e:
        messages.error(request, f'Error generating report: {str(e)}')
        return redirect('teacher_portal:attendance_reports', section=section.id)


def generate_daily_report(section, attendance_records, format_type):
    """Generate daily attendance summary report"""
    try:
        if format_type == 'csv':
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = f'attachment; filename="daily_attendance_{section.course.course_code}.csv"'
            
            writer = csv.writer(response)
            writer.writerow(['Date', 'Present', 'Absent', 'Tardy', 'Excused', 'Total', 'Attendance Rate'])
            
            # Group by date
            from django.utils import timezone
            from collections import defaultdict
            
            daily_data = defaultdict(lambda: {'P': 0, 'A': 0, 'T': 0, 'E': 0, 'L': 0})
            
            for record in attendance_records:
                daily_data[record.date][record.status] += 1
            
            # If no data, add a message row
            if not daily_data:
                writer.writerow(['No data', 0, 0, 0, 0, 0, '0%'])
            else:
                for date, counts in sorted(daily_data.items()):
                    total = sum(counts.values())
                    present = counts['P']
                    absent = counts['A'] + counts['E']
                    tardy = counts['T'] + counts['L']
                    excused = counts['E'] + counts['L']
                    rate = (present / total * 100) if total > 0 else 0
                    
                    writer.writerow([
                        date, present, absent, tardy, excused, total, f"{rate:.1f}%"
                    ])
            
            return response
        
        # For HTML format, create a simple response showing the data
        if format_type == 'html':
            html_content = f"""
            <html>
            <head><title>Daily Attendance Report - {section.course.name}</title></head>
            <body>
                <h1>Daily Attendance Report</h1>
                <h2>{section.course.name} - {section.name}</h2>
                <table border="1">
                    <tr><th>Date</th><th>Present</th><th>Absent</th><th>Tardy</th><th>Excused</th><th>Total</th><th>Attendance Rate</th></tr>
            """
            
            # Group by date
            from collections import defaultdict
            daily_data = defaultdict(lambda: {'P': 0, 'A': 0, 'T': 0, 'E': 0, 'L': 0})
            
            for record in attendance_records:
                daily_data[record.date][record.status] += 1
            
            if not daily_data:
                html_content += "<tr><td colspan='7'>No attendance data found</td></tr>"
            else:
                for date, counts in sorted(daily_data.items()):
                    total = sum(counts.values())
                    present = counts['P']
                    absent = counts['A'] + counts['E']
                    tardy = counts['T'] + counts['L']
                    excused = counts['E'] + counts['L']
                    rate = (present / total * 100) if total > 0 else 0
                    
                    html_content += f"""
                    <tr>
                        <td>{date}</td>
                        <td>{present}</td>
                        <td>{absent}</td>
                        <td>{tardy}</td>
                        <td>{excused}</td>
                        <td>{total}</td>
                        <td>{rate:.1f}%</td>
                    </tr>
                    """
            
            html_content += """
                </table>
                <p><a href="javascript:history.back()">Back to Reports</a></p>
            </body>
            </html>
            """
            
            return HttpResponse(html_content)
        
        # Default to HTML for other formats (PDF/HTML)
        from django.http import JsonResponse
        return JsonResponse({'error': 'PDF format not implemented yet. Please use CSV or HTML format.'}, status=400)
        
    except Exception as e:
        from django.http import JsonResponse
        return JsonResponse({'error': f'Error generating daily report: {str(e)}'}, status=500)


def generate_patterns_report(section, attendance_records, format_type):
    """Generate attendance patterns analysis report"""
    enrollments = section.enrollments.filter(is_active=True)
    patterns_data = []
    
    for enrollment in enrollments:
        summary = Attendance.get_attendance_summary(enrollment)
        patterns = Attendance.get_attendance_patterns(enrollment)
        
        patterns_data.append({
            'student': enrollment.student,
            'summary': summary,
            'patterns': patterns,
            'concerns': patterns['consecutive_absences'] >= 3 or 
                      summary['attendance_rate'] < 90 or
                      patterns['frequent_tardiness']
        })
    
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="attendance_patterns_{section.course.course_code}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Student', 'Student ID', 'Attendance Rate', 'Total Days', 'Present', 'Absent', 
            'Tardy', 'Consecutive Absences', 'Frequent Tardiness', 'Monday Pattern', 'Friday Pattern'
        ])
        
        for data in patterns_data:
            writer.writerow([
                data['student'].full_name,
                data['student'].student_id,
                f"{data['summary']['attendance_rate']:.1f}%",
                data['summary']['total_days'],
                data['summary']['present_days'],
                data['summary']['absent_days'],
                data['summary']['tardy_days'],
                data['patterns']['consecutive_absences'],
                'Yes' if data['patterns']['frequent_tardiness'] else 'No',
                'Yes' if data['patterns']['monday_pattern'] else 'No',
                'Yes' if data['patterns']['friday_pattern'] else 'No',
            ])
        
        return response
    
    # Default to HTML for other formats (PDF/HTML)
    from django.http import JsonResponse
    return JsonResponse({'error': 'PDF and HTML formats not implemented yet. Please use CSV format.'}, status=400)


def generate_student_report(section, attendance_records, format_type):
    """Generate individual student attendance report"""
    enrollments = section.enrollments.filter(is_active=True).select_related('student')
    
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="student_attendance_{section.course.course_code}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Student Name', 'Student ID', 'Total Days', 'Present', 'Absent', 'Tardy', 
            'Excused Absences', 'Unexcused Absences', 'Attendance Rate', 'Status'
        ])
        
        for enrollment in enrollments:
            summary = Attendance.get_attendance_summary(enrollment)
            status = 'At Risk' if summary['attendance_rate'] < 90 else 'Good Standing'
            
            writer.writerow([
                enrollment.student.full_name,
                enrollment.student.student_id,
                summary['total_days'],
                summary['present_days'],
                summary['absent_days'],
                summary['tardy_days'],
                summary.get('excused_days', 0),
                summary.get('unexcused_days', 0),
                f"{summary['attendance_rate']:.1f}%",
                status
            ])
        
        return response
    
    from django.http import JsonResponse
    return JsonResponse({'error': 'PDF and HTML formats not implemented yet. Please use CSV format.'}, status=400)


def generate_chronic_report(section, attendance_records, format_type):
    """Generate chronic absenteeism report (students missing 10%+ of days)"""
    enrollments = section.enrollments.filter(is_active=True).select_related('student')
    chronic_students = []
    
    for enrollment in enrollments:
        summary = Attendance.get_attendance_summary(enrollment)
        if summary['attendance_rate'] < 90:  # Less than 90% attendance
            patterns = Attendance.get_attendance_patterns(enrollment)
            chronic_students.append({
                'student': enrollment.student,
                'summary': summary,
                'patterns': patterns
            })
    
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="chronic_absenteeism_{section.course.course_code}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Student Name', 'Student ID', 'Attendance Rate', 'Days Missed', 'Consecutive Absences',
            'Frequent Monday Absences', 'Frequent Friday Absences', 'Risk Level'
        ])
        
        for data in chronic_students:
            risk_level = 'High' if data['summary']['attendance_rate'] < 80 else 'Moderate'
            
            writer.writerow([
                data['student'].full_name,
                data['student'].student_id,
                f"{data['summary']['attendance_rate']:.1f}%",
                data['summary']['absent_days'],
                data['patterns']['consecutive_absences'],
                'Yes' if data['patterns']['monday_pattern'] else 'No',
                'Yes' if data['patterns']['friday_pattern'] else 'No',
                risk_level
            ])
        
        return response
    
    from django.http import JsonResponse
    return JsonResponse({'error': 'PDF and HTML formats not implemented yet. Please use CSV format.'}, status=400)


def generate_tardiness_report(section, attendance_records, format_type):
    """Generate tardiness report focusing on late arrivals"""
    enrollments = section.enrollments.filter(is_active=True).select_related('student')
    
    if format_type == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="tardiness_report_{section.course.course_code}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Student Name', 'Student ID', 'Total Tardies', 'Average Minutes Late',
            'Most Common Day', 'Tardiness Rate', 'Improvement Needed'
        ])
        
        for enrollment in enrollments:
            # Get tardy records for this student
            tardy_records = attendance_records.filter(
                enrollment=enrollment,
                status__in=['T', 'L']  # Tardy and Late
            )
            
            if tardy_records.exists():
                total_tardies = tardy_records.count()
                avg_minutes = tardy_records.aggregate(
                    avg=models.Avg('minutes_late')
                )['avg'] or 0
                
                # Find most common tardy day
                from collections import Counter
                days = [record.date.strftime('%A') for record in tardy_records]
                most_common_day = Counter(days).most_common(1)[0][0] if days else 'N/A'
                
                # Calculate tardiness rate
                summary = Attendance.get_attendance_summary(enrollment)
                tardiness_rate = (total_tardies / summary['total_days'] * 100) if summary['total_days'] > 0 else 0
                
                needs_improvement = 'Yes' if tardiness_rate > 10 else 'No'
                
                writer.writerow([
                    enrollment.student.full_name,
                    enrollment.student.student_id,
                    total_tardies,
                    f"{avg_minutes:.1f}",
                    most_common_day,
                    f"{tardiness_rate:.1f}%",
                    needs_improvement
                ])
        
        return response
    
    from django.http import JsonResponse
    return JsonResponse({'error': 'PDF and HTML formats not implemented yet. Please use CSV format.'}, status=400)


# Enhanced Assignment Management Views
@method_decorator([login_required, role_required(["Staff", "Admin"])], name='dispatch')  
class TeacherAssignmentsView(TemplateView):
    template_name = 'teacher_portal/assignments.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        from academics.models import AssignmentTemplate
        
        # Get teacher's sections
        sections = user.taught_sections.filter(is_active=True)
        
        # Get current section
        section_id = self.request.GET.get('section')
        if section_id:
            current_section = get_object_or_404(sections, id=section_id)
        else:
            current_section = sections.first() if sections.exists() else None
        
        if current_section:
            # Get assignments with analytics
            assignments = current_section.assignments.all().select_related('category', 'template')
            
            # Calculate analytics for each assignment
            assignment_data = []
            for assignment in assignments:
                data = {
                    'assignment': assignment,
                    'completion_rate': assignment.get_completion_rate(),
                    'average_score': assignment.get_average_score(),
                    'grade_distribution': assignment.get_grade_distribution(),
                    'is_overdue': assignment.is_overdue,
                    'submission_count': assignment.submissions.count(),
                    'attachment_count': assignment.attachments.count(),
                }
                assignment_data.append(data)
            
            # Get templates
            templates = AssignmentTemplate.objects.filter(
                Q(created_by=user) | Q(is_public=True),
                is_active=True
            )
            
            context.update({
                'assignments': assignments,
                'assignment_data': assignment_data,
                'templates': templates,
            })
        
        context.update({
            'sections': sections,
            'current_section': current_section,
            'show_section_selector': sections.count() > 1,
        })
        
        return context


@login_required
@role_required(["Staff", "Admin"])
def assignment_analytics(request):
    """View for detailed assignment analytics"""
    from academics.models import Assignment
    from .assignment_forms import AssignmentAnalyticsFilterForm
    
    section_id = request.GET.get('section')
    if not section_id:
        messages.error(request, 'Section required')
        return redirect('teacher_portal:teacher_assignments')
    
    section = get_object_or_404(
        request.user.taught_sections.filter(is_active=True),
        id=section_id
    )
    
    # Apply filters
    filter_form = AssignmentAnalyticsFilterForm(request.GET)
    assignments = section.assignments.all()
    
    if filter_form.is_valid():
        category = filter_form.cleaned_data.get('category')
        date_start = filter_form.cleaned_data.get('date_start')
        date_end = filter_form.cleaned_data.get('date_end')
        completion_threshold = filter_form.cleaned_data.get('completion_threshold', 75)
        include_unpublished = filter_form.cleaned_data.get('include_unpublished')
        
        if category:
            assignments = assignments.filter(category=category)
        if date_start:
            assignments = assignments.filter(due_date__gte=date_start)
        if date_end:
            assignments = assignments.filter(due_date__lte=date_end)
        if not include_unpublished:
            assignments = assignments.filter(is_published=True)
    else:
        completion_threshold = 75
    
    # Calculate comprehensive analytics
    analytics_data = {
        'section': section,
        'total_assignments': assignments.count(),
        'published_assignments': assignments.filter(is_published=True).count(),
        'overdue_assignments': sum(1 for a in assignments if a.is_overdue),
        'assignments_below_threshold': 0,
        'average_completion_rate': 0,
        'category_breakdown': {},
    }
    
    if assignments.exists():
        completion_rates = []
        
        for assignment in assignments:
            completion_rate = assignment.get_completion_rate()
            completion_rates.append(completion_rate)
            
            if completion_rate < completion_threshold:
                analytics_data['assignments_below_threshold'] += 1
        
        analytics_data['average_completion_rate'] = sum(completion_rates) / len(completion_rates)
        
        # Category breakdown
        from django.db.models import Count, Avg
        category_stats = assignments.values('category__name').annotate(
            count=Count('id'),
            avg_points=Avg('max_points')
        )
        analytics_data['category_breakdown'] = list(category_stats)
    
    return render(request, 'teacher_portal/assignment_analytics.html', {
        'analytics_data': analytics_data,
        'assignments': assignments,
        'filter_form': filter_form,
        'completion_threshold': completion_threshold,
    })


# Placeholder views for remaining menu items

@method_decorator([login_required, role_required(["Staff", "Admin"])], name='dispatch')
class TeacherStudentsView(TemplateView):
    template_name = 'teacher_portal/students.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get teacher's sections
        sections = user.taught_sections.filter(is_active=True)
        
        # Get current section (from URL param or first section)
        section_id = self.request.GET.get('section')
        if section_id:
            current_section = get_object_or_404(sections, id=section_id)
        else:
            current_section = sections.first() if sections.exists() else None
        
        # Get students based on filters
        students = None
        if current_section:
            students = current_section.enrollments.filter(is_active=True).select_related(
                'student', 'student__grade_level'
            )
        elif sections.exists():
            # If no specific section selected, show all students from all teacher's sections
            students = Enrollment.objects.filter(
                section__in=sections,
                is_active=True
            ).select_related('student', 'student__grade_level')
        else:
            students = Enrollment.objects.none()
        
        # Apply search filter
        search_query = self.request.GET.get('search')
        if search_query and students:
            students = students.filter(
                Q(student__first_name__icontains=search_query) |
                Q(student__last_name__icontains=search_query) |
                Q(student__student_id__icontains=search_query)
            )
        
        # Apply section filter
        section_filter = self.request.GET.get('section')
        if section_filter and section_filter != section_id:
            try:
                filter_section = sections.get(id=section_filter)
                students = students.filter(section=filter_section)
                current_section = filter_section
            except CourseSection.DoesNotExist:
                pass
        
        # Apply grade level filter
        grade_filter = self.request.GET.get('grade')
        if grade_filter and students:
            students = students.filter(student__grade_level__name=grade_filter)
        
        # Order students by name
        if students:
            students = students.order_by('student__last_name', 'student__first_name')
        
        context.update({
            'sections': sections,
            'current_section': current_section,
            'students': students,
            'show_section_selector': sections.count() > 1,
        })
        
        return context

@method_decorator([login_required, role_required(["Staff", "Admin"])], name='dispatch')
class TeacherReportsView(TemplateView):
    template_name = 'teacher_portal/reports.html'

@method_decorator([login_required, role_required(["Staff", "Admin"])], name='dispatch')
class TeacherMessagesView(TemplateView):
    template_name = 'teacher_portal/messages.html'
    
    def get_context_data(self, **kwargs):
        from academics.models import Message, Announcement
        from django.db.models import Q
        from django.core.paginator import Paginator
        
        context = super().get_context_data(**kwargs)
        
        # Get direct messages sent to this teacher
        # TODO: Fix database schema issue with thread_id column
        # received_messages = Message.objects.filter(
        #     recipient=self.request.user
        # ).select_related('sender').order_by('-sent_at')
        received_messages = []
        
        # Get messages sent by this teacher
        # sent_messages = Message.objects.filter(
        #     sender=self.request.user
        # ).select_related('recipient').order_by('-sent_at')
        sent_messages = []
        
        # Get relevant announcements for teachers
        today = timezone.now().date()
        announcements = Announcement.objects.filter(
            Q(audience__in=['ALL', 'TEACHERS']) &
            Q(publish_date__lte=today) &
            (Q(expire_date__gte=today) | Q(expire_date__isnull=True)) &
            Q(is_published=True)
        ).order_by('-publish_date')
        
        # Paginate received messages
        paginator = Paginator(received_messages, 10)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)
        
        # Count unread and urgent messages
        # Since received_messages is currently an empty list, set counts to 0
        unread_count = 0
        urgent_count = 0
        
        context.update({
            'page_obj': page_obj,
            'received_messages': received_messages,
            'sent_messages': sent_messages,
            'announcements': announcements,
            'unread_count': unread_count,
            'urgent_count': urgent_count,
        })
        
        return context

@method_decorator([login_required, role_required(["Staff", "Admin"])], name='dispatch')
class TeacherSettingsView(TemplateView):
    template_name = 'teacher_portal/settings.html'
