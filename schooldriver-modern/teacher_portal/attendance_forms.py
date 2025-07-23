from django import forms
from django.forms import modelformset_factory
from datetime import date, timedelta
from academics.models import Attendance, AbsenceReason, Enrollment, CourseSection


class AttendanceForm(forms.ModelForm):
    """Form for individual attendance entry"""
    
    class Meta:
        model = Attendance
        fields = ['status', 'absence_reason', 'minutes_late', 'notes']
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-select form-select-sm attendance-status',
                'data-bs-toggle': 'tooltip',
                'title': 'Select attendance status'
            }),
            'absence_reason': forms.Select(attrs={
                'class': 'form-select form-select-sm',
                'style': 'display: none;'  # Initially hidden
            }),
            'minutes_late': forms.NumberInput(attrs={
                'class': 'form-control form-control-sm',
                'min': '0',
                'max': '180',
                'placeholder': 'Minutes',
                'style': 'display: none; width: 80px;'  # Initially hidden
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control form-control-sm',
                'rows': 2,
                'placeholder': 'Additional notes (optional)'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['absence_reason'].queryset = AbsenceReason.objects.filter(is_active=True)
        self.fields['absence_reason'].empty_label = "Select reason..."


class BulkAttendanceForm(forms.Form):
    """Form for bulk attendance operations"""
    
    BULK_ACTIONS = [
        ('', 'Select Action'),
        ('mark_all_present', 'Mark All Present'),
        ('mark_all_absent', 'Mark All Absent'),
        ('mark_all_tardy', 'Mark All Tardy'),
        ('copy_previous_day', 'Copy from Previous Day'),
        ('clear_all', 'Clear All Attendance'),
    ]
    
    action = forms.ChoiceField(
        choices=BULK_ACTIONS,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    absence_reason = forms.ModelChoiceField(
        queryset=AbsenceReason.objects.filter(is_active=True),
        required=False,
        empty_label="Select reason (for absences)...",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    confirm = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )


class AttendanceFilterForm(forms.Form):
    """Form for filtering attendance records"""
    
    date_start = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_end = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Status')] + Attendance.ATTENDANCE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    absence_reason = forms.ModelChoiceField(
        queryset=AbsenceReason.objects.filter(is_active=True),
        required=False,
        empty_label="All Reasons",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set default date range to current month
        today = date.today()
        month_start = today.replace(day=1)
        self.fields['date_start'].initial = month_start
        self.fields['date_end'].initial = today


class AttendanceReportForm(forms.Form):
    """Form for generating attendance reports"""
    
    REPORT_TYPES = [
        ('daily', 'Daily Attendance Summary'),
        ('student', 'Individual Student Report'),
        ('patterns', 'Attendance Patterns Analysis'),
        ('chronic', 'Chronic Absenteeism Report'),
        ('tardiness', 'Tardiness Report'),
    ]
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('csv', 'CSV'),
        ('html', 'HTML View'),
    ]
    
    report_type = forms.ChoiceField(
        choices=REPORT_TYPES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    format = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        initial='pdf',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_start = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_end = forms.DateField(
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    students = forms.ModelMultipleChoiceField(
        queryset=None,
        required=False,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    
    include_patterns = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    include_parent_contact = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        section = kwargs.pop('section', None)
        super().__init__(*args, **kwargs)
        
        # Set default date range to current month
        today = date.today()
        month_start = today.replace(day=1)
        self.fields['date_start'].initial = month_start
        self.fields['date_end'].initial = today
        
        if section:
            self.fields['students'].queryset = Enrollment.objects.filter(
                section=section,
                is_active=True
            ).select_related('student')


class QuickAttendanceForm(forms.Form):
    """Quick form for AJAX attendance marking"""
    
    enrollment_id = forms.IntegerField(widget=forms.HiddenInput())
    date = forms.DateField(widget=forms.HiddenInput())
    status = forms.ChoiceField(
        choices=Attendance.ATTENDANCE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    absence_reason = forms.ModelChoiceField(
        queryset=AbsenceReason.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    minutes_late = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control form-control-sm',
            'min': '0',
            'max': '180'
        })
    )


class AbsenceReasonForm(forms.ModelForm):
    """Form for creating/editing absence reasons"""
    
    class Meta:
        model = AbsenceReason
        fields = ['name', 'description', 'is_excused', 'requires_documentation', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Medical Appointment, Family Emergency'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional description'
            }),
            'is_excused': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_documentation': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ParentNotificationForm(forms.Form):
    """Form for parent notification settings"""
    
    NOTIFICATION_TYPES = [
        ('absence', 'Absence Notifications'),
        ('tardiness', 'Tardiness Notifications'),
        ('patterns', 'Pattern Alerts (chronic absenteeism)'),
    ]
    
    notification_type = forms.MultipleChoiceField(
        choices=NOTIFICATION_TYPES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    
    send_immediately = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    daily_summary = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    weekly_summary = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    threshold_consecutive_absences = forms.IntegerField(
        initial=3,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '1',
            'max': '10'
        })
    )
    
    threshold_attendance_rate = forms.DecimalField(
        initial=90.0,
        max_digits=5,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '50',
            'max': '100',
            'step': '0.1'
        })
    )


# Formset for bulk attendance entry
AttendanceFormSet = modelformset_factory(
    Attendance,
    form=AttendanceForm,
    fields=['status', 'absence_reason', 'minutes_late', 'notes'],
    extra=0,
    can_delete=False
)
